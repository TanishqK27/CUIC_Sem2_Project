"""Core backtesting engine.

Provides the backtest() loop, output column constants, and example
strategy implementations.
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Callable

import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_COLUMNS = [
    "timestamp", "game", "action", "bet_size",
    "odds", "outcome", "pnl", "cumulative_pnl", "bankroll",
]
"""The 9 required columns in backtester output. This is the contract that
downstream consumers (Ben's metrics module, Ismaeel's tests) depend on.
Do NOT remove or rename columns without coordinating per
docs/SOPs/modularity-upgrades.md."""

# Common strategy signal key misspellings -> correct key name
_SIGNAL_KEY_TYPOS: dict[str, str] = {
    "Action": "action",
    "ACTION": "action",
    "bet_size": "size",
    "betsize": "size",
    "Confidence": "confidence",
    "conf": "confidence",
    "Size": "size",
    "Reason": "reason",
}

VALID_ACTIONS = {"BUY_HOME", "BUY_AWAY", "SKIP"}
"""Actions a strategy function may return."""

VALID_OUTCOMES = {"WIN", "LOSS"}
"""Possible trade outcomes."""


# ---------------------------------------------------------------------------
# Core backtesting loop
# ---------------------------------------------------------------------------


def backtest(
    data: pd.DataFrame,
    strategy_fn: Callable[[pd.Series, dict[str, Any] | None], dict[str, Any]],
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    position_sizing: str | None = None,
    kelly_fraction: float = 0.5,
) -> pd.DataFrame:
    """Run a backtest over historical game data using a strategy function.

    What: Simulates betting on historical games by iterating through each row,
    calling the strategy function for a signal, and tracking the bankroll,
    profit/loss, and trade history.

    Why: This is the core engine that every strategy in the CUIC Quant Fund
    is evaluated through. It provides a standardized way to measure strategy
    performance on historical data before risking real money.

    How:
        1. Initialize bankroll and empty trade list.
        2. For each game row (sorted by timestamp):
           a. Skip rows with NaN or invalid odds (data quality guard).
           b. Strip home_win from the row before passing to strategy
              (prevents data leakage — the strategy must not know outcomes).
           c. Call strategy_fn(row, context) to get a signal.
           d. If signal is SKIP or size <= 0, skip to next row.
           e. Cap bet_size at current bankroll.
           f. Determine outcome: compare action vs home_win.
           g. Calculate PnL: WIN = bet_size * (odds - 1), LOSS = -bet_size.
           h. Update cumulative_pnl and bankroll.
           i. Append trade to list.
        3. Return trades as a DataFrame with exactly 9 columns.

    Args:
        data: DataFrame from load_backtest_data() with columns: timestamp,
            game, home_team, away_team, home_odds, away_odds, home_win.
        strategy_fn: Callable matching the strategy interface
            (see docs/reference/strategy-interface.md). Takes
            (row: pd.Series, context: dict | None) and returns a dict with
            keys: action, confidence, size, reason (optional).
        initial_bankroll: Starting bankroll in dollars. Defaults to 10000.
        cost_pct: Percentage deducted from winning payouts (e.g. 0.02 for 2%).
            Models bookmaker vig/margin. Default 0.0 (no cost).
        cost_flat: Flat dollar fee deducted per trade regardless of outcome.
            Default 0.0 (no fee).
        position_sizing: Position sizing method. None = use strategy's size field,
            "kelly" = Kelly Criterion sizing using strategy's confidence as
            win probability. If confidence is None, 0.0, or 1.0, falls back
            to the strategy's raw size field with a warning. Default None.
        kelly_fraction: Fraction of Kelly to use when position_sizing="kelly".
            0.5 = half-Kelly (safer), 1.0 = full Kelly. Default 0.5.

    Returns:
        DataFrame with 9 columns: timestamp, game, action, bet_size, odds,
        outcome, pnl, cumulative_pnl, bankroll. Returns empty DataFrame with
        correct columns if no trades are executed.
    """
    bankroll = initial_bankroll
    cumulative_pnl = 0.0
    trades: list[dict[str, Any]] = []
    confidence_values: list[float | None] = []

    context: dict[str, Any] = {
        "initial_bankroll": initial_bankroll,
        "bankroll": bankroll,
        "trade_count": 0,
        "cumulative_pnl": 0.0,
        "history": [],           # U3: past trades for lookback
        "past_games": None,      # U3: past game data (set per iteration)
    }

    # Validate required columns
    required = {"timestamp", "game", "home_team", "away_team", "home_odds", "away_odds", "home_win"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Pre-import Kelly if needed (avoid importing inside the loop)
    _calc_kelly = None
    if position_sizing == "kelly":
        from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction as _calc_kelly

    for row_idx, row in data.iterrows():
        if bankroll <= 0:
            break

        # Skip rows with NaN or invalid odds (decimal odds must be > 1.0)
        if pd.isna(row["home_odds"]) or pd.isna(row["away_odds"]):
            continue
        if row["home_odds"] <= 1.0 or row["away_odds"] <= 1.0:
            continue

        # Update context for strategy
        context["bankroll"] = bankroll
        context["trade_count"] = len(trades)
        context["cumulative_pnl"] = cumulative_pnl
        context["history"] = list(trades)  # U3: snapshot of past trades
        context["past_games"] = data.loc[:row_idx].iloc[:-1]  # U3: all rows before current

        # Remove outcome column to prevent data leakage
        strategy_row = row.drop(labels=["home_win"])

        # B3: Catch strategy exceptions to preserve prior trades
        try:
            signal = strategy_fn(strategy_row, context)
        except Exception as exc:
            warnings.warn(
                f"Strategy raised {type(exc).__name__} for game "
                f"'{row['game']}': {exc} — skipping row.",
                stacklevel=2,
            )
            continue

        # U2: Warn on common signal key misspellings
        for typo, correct in _SIGNAL_KEY_TYPOS.items():
            if typo in signal and correct not in signal:
                warnings.warn(
                    f"Strategy returned '{typo}' instead of '{correct}' "
                    f"(case/name-sensitive) for game '{row['game']}' — "
                    f"key ignored. Use '{correct}'.",
                    stacklevel=2,
                )

        if "action" not in signal:
            warnings.warn(
                f"Strategy returned no 'action' key for game "
                f"'{row['game']}' — treating as SKIP. "
                f"Got keys: {list(signal.keys())}",
                stacklevel=2,
            )
            continue

        action = signal.get("action", "SKIP")

        if action == "SKIP":
            continue

        # Determine initial bet size from strategy signal
        bet_size = signal.get("size", 0.0)

        # B2: Guard against NaN in bet_size
        if bet_size is None or (isinstance(bet_size, float) and math.isnan(bet_size)):
            warnings.warn(
                f"Strategy returned NaN/None size for game "
                f"'{row['game']}' — skipping.",
                stacklevel=2,
            )
            continue

        if bet_size <= 0 and position_sizing != "kelly":
            continue

        # Determine odds based on action
        if action == "BUY_HOME":
            odds = row["home_odds"]
            won = row["home_win"] == 1
        elif action == "BUY_AWAY":
            odds = row["away_odds"]
            won = row["home_win"] == 0
        else:
            warnings.warn(
                f"Unrecognized action '{action}' from strategy for game "
                f"'{row['game']}' — skipping. Valid actions: {VALID_ACTIONS}",
                stacklevel=2,
            )
            continue

        # Apply Kelly position sizing if enabled
        confidence = signal.get("confidence")
        if position_sizing == "kelly":
            if confidence is not None and 0 < confidence < 1:
                kelly_size = _calc_kelly(
                    win_probability=confidence,
                    decimal_odds=odds,
                    kelly_fraction=kelly_fraction,
                )
                bet_size = round(kelly_size * bankroll, 2)
                # B2: Guard against NaN from Kelly calculation
                if bet_size is None or (isinstance(bet_size, float) and math.isnan(bet_size)):
                    warnings.warn(
                        f"Kelly produced NaN bet_size for game "
                        f"'{row['game']}' — skipping.",
                        stacklevel=2,
                    )
                    continue
                if bet_size <= 0:
                    continue
            else:
                warnings.warn(
                    f"Kelly sizing enabled but confidence={confidence!r} is "
                    f"outside (0, 1) — falling back to strategy's raw size "
                    f"({bet_size}) for game '{row['game']}'.",
                    stacklevel=2,
                )

        # Cap bet at bankroll minus flat fee to prevent negative bankroll
        bet_size = min(bet_size, max(0.0, bankroll - cost_flat))
        if bet_size <= 0:
            continue

        # Calculate P&L (round immediately so stored and accumulated values match)
        if won:
            pnl = round(bet_size * (odds - 1) * (1 - cost_pct) - cost_flat, 2)
            outcome = "WIN"
        else:
            pnl = round(-bet_size - cost_flat, 2)
            outcome = "LOSS"

        cumulative_pnl += pnl
        bankroll += pnl

        trades.append({
            "timestamp": row["timestamp"],
            "game": row["game"],
            "action": action,
            "bet_size": round(bet_size, 2),
            "odds": odds,
            "outcome": outcome,
            "pnl": pnl,
            "cumulative_pnl": round(cumulative_pnl, 2),
            "bankroll": round(bankroll, 2),
        })
        confidence_values.append(confidence)  # M4: track confidence

    # Return DataFrame with correct columns even if empty
    if not trades:
        result = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        result = pd.DataFrame(trades)[OUTPUT_COLUMNS]

    # Store cost params in metadata so validator can auto-read them
    result.attrs["cost_pct"] = cost_pct
    result.attrs["cost_flat"] = cost_flat
    result.attrs["initial_bankroll"] = initial_bankroll
    result.attrs["confidence_values"] = confidence_values  # M4: confidence stored in attrs
    return result


# ---------------------------------------------------------------------------
# Example strategies
# ---------------------------------------------------------------------------


def always_bet_home(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Example strategy that always bets $100 on the home team.

    What: A naive strategy that unconditionally backs the home team
    for every game, regardless of odds or context.

    Why: This exists as a reference implementation of the strategy interface
    (see docs/reference/strategy-interface.md). It is used to validate
    that the backtester produces correct output — since the strategy is
    deterministic, we can verify results against a known-good CSV.

    Args:
        row: Game data row with home_odds, away_odds, etc.
            Must NOT contain home_win (the backtester strips it).
        context: Optional dict from the backtester with current state
            (bankroll, trade_count, cumulative_pnl). Ignored by this strategy.

    Returns:
        Signal dict conforming to the strategy interface:
        - action: 'BUY_HOME'
        - confidence: 0.5
        - size: 100.0
        - reason: Human-readable explanation
    """
    return {
        "action": "BUY_HOME",
        "confidence": 0.5,
        "size": 100.0,
        "reason": "Always bet home (test strategy)",
    }

def always_bet_away(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Example strategy that always bets $100 on the away team.

    Args:
        row: Game data row with home_odds, away_odds, etc.
            Must NOT contain home_win (the backtester strips it).
        context: Optional dict from the backtester with current state
            (bankroll, trade_count, cumulative_pnl). Ignored by this strategy.

    Returns:
        Signal dict conforming to the strategy interface:
        - action: 'BUY_AWAY'
        - confidence: 0.5
        - size: 100.0
        - reason: Human-readable explanation
    """
    return {
        "action": "BUY_AWAY",
        "confidence": 0.5,
        "size": 100.0,
        "reason": "Always bet away (test strategy)",
    }


def kelly_bet_home_demo(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """DEMO ONLY — Example strategy showing Kelly sizing plumbing.

    WARNING: This is a plumbing demonstration, NOT a real edge model.
    The confidence value is derived from implied probability + a flat 5%,
    which is tautological — Kelly will always bet on every game because
    p > 1/odds is guaranteed by construction. Do NOT use this as a
    template for real strategy development.

    Args:
        row: Game data row with home_odds, away_odds, etc.
        context: Optional dict from backtester with current state.

    Returns:
        Signal dict with action, confidence, size, and reason.
    """
    implied_prob = 1.0 / row["home_odds"]
    confidence = min(implied_prob + 0.05, 0.95)
    return {
        "action": "BUY_HOME",
        "confidence": confidence,
        "size": 100.0,
        "reason": f"DEMO kelly home bet (implied={implied_prob:.2f}, conf={confidence:.2f})",
    }


__all__ = [
    "OUTPUT_COLUMNS",
    "VALID_ACTIONS",
    "VALID_OUTCOMES",
    "backtest",
    "always_bet_home",
    "always_bet_away",
    "kelly_bet_home_demo",
]
