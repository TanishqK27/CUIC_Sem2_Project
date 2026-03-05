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
    "confidence", "closing_odds",
]
"""The 11 required columns in backtester output. This is the contract that
downstream consumers (Ben's metrics module, Ismaeel's tests) depend on.
Do NOT remove or rename columns without coordinating per
docs/SOPs/modularity-upgrades.md.

M4: confidence is stored directly in the DataFrame (not just attrs) so
    that Brier Score and Log Loss can be computed by the metrics module.
M2: closing_odds is always present (NaN when input has no closing odds)
    so that CLV can be computed when closing line data is available.
"""

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


def _validate_strategy_size(size: Any, game: str) -> float:
    """Validate and return strategy size as a clean Python float.

    Args:
        size: The size value from the strategy signal dict.
        game: Game identifier for use in error messages.

    Returns:
        Validated size cast to Python float. Always positive and finite.

    Raises:
        ValueError: If size is None, non-numeric, NaN, inf, or <= 0.
    """
    if size is None:
        raise ValueError(
            f"Strategy returned size=None for game '{game}'. "
            f"size must be a positive finite number."
        )
    # Reject strings even if numeric-looking ("100") — a strategy returning a
    # string size is always a bug, not an acceptable implicit coercion.
    if isinstance(size, str):
        raise ValueError(
            f"Strategy returned non-numeric size={size!r} for game '{game}'. "
            f"size must be a positive finite number."
        )
    try:
        f = float(size)
    except (TypeError, ValueError):
        raise ValueError(
            f"Strategy returned non-numeric size={size!r} for game '{game}'. "
            f"size must be a positive finite number."
        ) from None
    if math.isnan(f):
        raise ValueError(
            f"Strategy returned size={f!r} for game '{game}'. "
            f"size must be a positive finite number."
        )
    if math.isinf(f):
        raise ValueError(
            f"Strategy returned size={f!r} for game '{game}'. "
            f"size must be a positive finite number."
        )
    if f <= 0:
        raise ValueError(
            f"Strategy returned size={f} which is <= 0 for game '{game}'. "
            f"size must be a positive finite number."
        )
    return f


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
        3. Return trades as a DataFrame with exactly 11 columns.

    Args:
        data: DataFrame from load_backtest_data() with columns: timestamp,
            game, home_team, away_team, home_odds, away_odds, home_win.
        strategy_fn: Callable matching the strategy interface
            (see docs/reference/strategy-interface.md). Takes
            (row: pd.Series, context: dict | None) and returns a dict with
            keys: action, confidence, size, reason (optional).
        initial_bankroll: Starting bankroll in dollars. Defaults to 10000.
            Must be a finite non-negative number.
        cost_pct: Percentage deducted from winning payouts (e.g. 0.02 for 2%).
            Models bookmaker vig/margin. Must be in [0, 1]. Default 0.0.
        cost_flat: Flat dollar fee deducted per trade regardless of outcome.
            Must be non-negative. Default 0.0.
        position_sizing: Position sizing method. None = use strategy's size field,
            "kelly" = Kelly Criterion sizing using strategy's confidence as
            win probability. Case-insensitive ("Kelly" and "KELLY" also work).
            If confidence is None, 0.0, or 1.0, falls back to the strategy's
            raw size field with a warning. Default None.
        kelly_fraction: Fraction of Kelly to use when position_sizing="kelly".
            0.5 = half-Kelly (safer), 1.0 = full Kelly. Must be in (0, 1].
            Default 0.5.

    Returns:
        DataFrame with 11 columns: timestamp, game, action, bet_size, odds,
        outcome, pnl, cumulative_pnl, bankroll, confidence, closing_odds.
        Returns empty DataFrame with correct columns if no trades are executed.

    Raises:
        ValueError: If initial_bankroll, cost_pct, cost_flat, or kelly_fraction
            are invalid (NaN, out of range, etc.).
    """
    # --- Input validation (fail fast on bad parameters) ---
    if not isinstance(initial_bankroll, (int, float)) or not math.isfinite(initial_bankroll):
        raise ValueError(f"initial_bankroll must be a finite number, got {initial_bankroll!r}")
    if initial_bankroll <= 0:
        raise ValueError(f"initial_bankroll must be positive, got {initial_bankroll}")

    if not isinstance(cost_pct, (int, float)) or not math.isfinite(cost_pct):
        raise ValueError(f"cost_pct must be a finite number, got {cost_pct!r}")
    if cost_pct < 0 or cost_pct > 1:
        raise ValueError(
            f"cost_pct must be in [0, 1], got {cost_pct}. "
            f"Note: cost_pct is a fraction (0.05 = 5%), not a percentage."
        )

    if not isinstance(cost_flat, (int, float)) or not math.isfinite(cost_flat):
        raise ValueError(f"cost_flat must be a finite number, got {cost_flat!r}")
    if cost_flat < 0:
        raise ValueError(f"cost_flat must be non-negative, got {cost_flat}")

    # Normalize position_sizing to lowercase for case-insensitive matching
    if position_sizing is not None:
        position_sizing = position_sizing.lower()
        if position_sizing != "kelly":
            warnings.warn(
                f"Unrecognized position_sizing={position_sizing!r} — "
                f"only 'kelly' is supported. Using flat sizing.",
                stacklevel=2,
            )
            position_sizing = None

    if position_sizing == "kelly":
        if not isinstance(kelly_fraction, (int, float)) or math.isnan(kelly_fraction):
            raise ValueError(f"kelly_fraction must be a finite number, got {kelly_fraction!r}")
        if kelly_fraction <= 0 or kelly_fraction > 1:
            raise ValueError(
                f"kelly_fraction must be in (0, 1], got {kelly_fraction}"
            )

    bankroll = initial_bankroll
    cumulative_pnl = 0.0
    trades: list[dict[str, Any]] = []

    # M2: Pre-check whether closing odds columns exist in input
    _has_closing_home = "closing_home_odds" in data.columns
    _has_closing_away = "closing_away_odds" in data.columns

    # Validate required columns
    required = {"timestamp", "game", "home_team", "away_team", "home_odds", "away_odds", "home_win"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # B1: Guard against unsorted data — past_games relies on index ordering
    ts = pd.to_datetime(data["timestamp"], errors="coerce")
    if not ts.is_monotonic_increasing:
        raise ValueError(
            "Input data must be sorted by timestamp (ascending). "
            "Use load_backtest_data() or sort before calling backtest()."
        )

    # Pre-import Kelly if needed (avoid importing inside the loop)
    _calc_kelly = None
    if position_sizing == "kelly":
        from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction as _calc_kelly

    for row_pos, (row_idx, row) in enumerate(data.iterrows()):
        if bankroll <= 0:
            break

        try:
            # Skip rows with NaN or invalid odds (decimal odds must be > 1.0)
            try:
                home_odds_val = float(row["home_odds"])
                away_odds_val = float(row["away_odds"])
            except (TypeError, ValueError):
                warnings.warn(
                    f"Non-numeric odds for game '{row['game']}' — skipping.",
                    stacklevel=2,
                )
                continue

            if math.isnan(home_odds_val) or math.isnan(away_odds_val):
                continue
            if home_odds_val <= 1.0 or away_odds_val <= 1.0:
                continue

            # Skip rows with NaN or non-binary home_win
            home_win_val = row["home_win"]
            if pd.isna(home_win_val):
                warnings.warn(
                    f"NaN home_win for game '{row['game']}' — skipping row.",
                    stacklevel=2,
                )
                continue
            try:
                home_win_float = float(home_win_val)
            except (TypeError, ValueError):
                warnings.warn(
                    f"Non-numeric home_win={home_win_val!r} for game "
                    f"'{row['game']}' — skipping row.",
                    stacklevel=2,
                )
                continue
            # Reject non-binary values (e.g. 0.7) — int() would silently
            # truncate 0.7 to 0, misclassifying the outcome.
            if home_win_float not in (0.0, 1.0):
                warnings.warn(
                    f"home_win={home_win_val!r} for game '{row['game']}' is not "
                    f"0 or 1 — skipping row.",
                    stacklevel=2,
                )
                continue
            home_win_int = int(home_win_float)

            # Update context for strategy — deep copies to prevent mutation
            context: dict[str, Any] = {
                "initial_bankroll": initial_bankroll,
                "bankroll": bankroll,
                "trade_count": len(trades),
                "cumulative_pnl": cumulative_pnl,
                "history": [dict(t) for t in trades],  # U3: deep copy of past trades
                "past_games": None,  # U3: set below
            }

            # U3: past_games is a copy with home_win DROPPED to prevent leakage
            # Use positional slicing (iloc) to avoid label-based issues with
            # duplicate index values that could include current/future rows.
            past_games_raw = data.iloc[:row_pos]
            _past_drop = ["home_win"]
            if _has_closing_home:
                _past_drop.append("closing_home_odds")
            if _has_closing_away:
                _past_drop.append("closing_away_odds")
            context["past_games"] = past_games_raw.drop(columns=_past_drop, errors="ignore").copy()

            # Remove outcome and closing odds to prevent data leakage
            # Closing odds are post-hoc evaluation data — strategies should only
            # see opening odds available at decision time.
            _drop_labels = ["home_win"]
            if _has_closing_home:
                _drop_labels.append("closing_home_odds")
            if _has_closing_away:
                _drop_labels.append("closing_away_odds")
            strategy_row = row.drop(labels=_drop_labels)

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

            # Guard against strategy returning non-dict (None, str, int, list)
            if not isinstance(signal, dict):
                warnings.warn(
                    f"Strategy returned {type(signal).__name__} instead of dict "
                    f"for game '{row['game']}' — skipping row.",
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

            # Determine initial bet size from strategy signal.
            # For flat sizing: validate strictly — NaN/None/non-numeric/inf/<= 0 all
            # raise ValueError, caught here, warned, and skipped cleanly.
            # For Kelly: raw size is only used as a fallback when confidence is invalid;
            # Kelly computes the real size below.
            raw_size = signal.get("size")
            if position_sizing != "kelly":
                try:
                    bet_size = _validate_strategy_size(raw_size, row["game"])
                except ValueError as exc:
                    warnings.warn(str(exc), stacklevel=2)
                    continue
            else:
                # Kelly path — placeholder; Kelly block below sets the real bet_size.
                # raw_size is only used as Kelly fallback when confidence is invalid.
                bet_size = 0.0

            # Determine odds based on action
            if action == "BUY_HOME":
                odds = home_odds_val
                won = home_win_int == 1
            elif action == "BUY_AWAY":
                odds = away_odds_val
                won = home_win_int == 0
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
                        max_fraction=1.0,  # let kelly_fraction be the sole throttle
                    )
                    # Use effective bankroll (bankroll minus flat fee) so Kelly
                    # sizing is optimal given the per-trade fee.  Without this,
                    # Kelly computes size on the full bankroll and cost_flat is
                    # only subtracted later, making the bet larger than optimal.
                    effective_bankroll = max(0.0, bankroll - cost_flat)
                    bet_size = round(kelly_size * effective_bankroll, 2)
                    # Guard NaN/inf from Kelly arithmetic. Legitimate 0 = no edge,
                    # handled by soft continue below.
                    if not math.isfinite(bet_size):
                        warnings.warn(
                            f"Kelly produced non-finite size={bet_size!r} for game "
                            f"'{row['game']}' — skipping.",
                            stacklevel=2,
                        )
                        continue
                    if bet_size <= 0:
                        continue  # No edge on this game — skip silently
                else:
                    # Confidence invalid — validate and use raw size strictly.
                    try:
                        bet_size = _validate_strategy_size(raw_size, row["game"])
                    except ValueError as exc:
                        warnings.warn(
                            f"Kelly sizing enabled but confidence={confidence!r} is "
                            f"outside (0, 1), and raw size is also invalid: {exc}",
                            stacklevel=2,
                        )
                        continue
                    warnings.warn(
                        f"Kelly sizing enabled but confidence={confidence!r} is "
                        f"outside (0, 1) — falling back to raw size={bet_size} "
                        f"for game '{row['game']}'.",
                        stacklevel=2,
                    )

            # Cap bet at bankroll minus flat fee to prevent negative bankroll
            bet_size = round(min(bet_size, max(0.0, bankroll - cost_flat)), 2)
            if bet_size <= 0:
                continue

            # Calculate P&L (round immediately so stored and accumulated values match)
            # Cost model: "commission on net winnings" — this is the standard
            # sports-betting model where cost_pct (e.g. bookmaker vig) is charged
            # only on the NET PROFIT of winning bets, not on losses.  Losing bets
            # forfeit the full stake; no percentage commission applies.
            # cost_flat is a per-trade fee charged regardless of outcome.
            if won:
                pnl = round(bet_size * (odds - 1) * (1 - cost_pct) - cost_flat, 2)
                outcome = "WIN"
            else:
                pnl = round(-bet_size - cost_flat, 2)
                outcome = "LOSS"

            # Accumulate at full float precision — only round for output
            cumulative_pnl += pnl
            # Derive bankroll from initial + cumulative to avoid drift
            bankroll = max(initial_bankroll + cumulative_pnl, 0.0)

            # M2: Resolve closing odds for the side we bet on
            closing_odds_val = float("nan")
            if action == "BUY_HOME" and _has_closing_home:
                val = row.get("closing_home_odds")
                if pd.notna(val):
                    closing_odds_val = float(val)
            elif action == "BUY_AWAY" and _has_closing_away:
                val = row.get("closing_away_odds")
                if pd.notna(val):
                    closing_odds_val = float(val)

            # M4: Store confidence directly in output, clamped to [0, 1]
            stored_confidence = float("nan")
            if confidence is not None:
                try:
                    conf_val = float(confidence)
                    if math.isnan(conf_val):
                        stored_confidence = float("nan")
                    else:
                        # Clamp to [0, 1] to prevent downstream Brier/LogLoss corruption
                        stored_confidence = max(0.0, min(1.0, conf_val))
                except (TypeError, ValueError):
                    stored_confidence = float("nan")

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
                "confidence": stored_confidence,
                "closing_odds": closing_odds_val,
            })

        except (KeyboardInterrupt, SystemExit):
            warnings.warn(
                f"Backtest interrupted after {len(trades)} completed trades — "
                f"partial results returned.",
                stacklevel=2,
            )
            raise
        except Exception as exc:  # B5: was BaseException — let MemoryError etc. propagate
            warnings.warn(
                f"Unexpected {type(exc).__name__} processing game "
                f"'{row.get('game', f'row {row_idx}')}': {exc} — skipping row.",
                stacklevel=2,
            )
            continue

    # Return DataFrame with correct columns even if empty
    if not trades:
        result = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        result = pd.DataFrame(trades)[OUTPUT_COLUMNS]

    # Store cost params in metadata so validator can auto-read them
    result.attrs["cost_pct"] = cost_pct
    result.attrs["cost_flat"] = cost_flat
    result.attrs["initial_bankroll"] = initial_bankroll
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
