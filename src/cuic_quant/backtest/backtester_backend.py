"""Backtester backend module for the CUIC Quant Fund sports betting backtester.

This module contains all core backtesting functions extracted from the
tools/backtester.ipynb notebook. It provides:

- Data loading from Railway PostgreSQL or local CSV fallback
- Core backtesting loop that evaluates strategy functions against historical data
- Example strategy implementation for testing
- Validation suite to verify backtest results are correct and leak-free

Why this exists:
    The backtester logic was originally defined inline in a Jupyter notebook,
    making it impossible to import from other modules (e.g., Ben's metrics,
    Ismaeel's tests). This module makes the backtester importable and testable.

How to use:
    from cuic_quant.backtest.backtester_backend import (
        load_backtest_data, backtest, always_bet_home, validate_backtest_results,
    )

    data = load_backtest_data("2026-01-01", "2026-01-31")
    results = backtest(data, always_bet_home)
    report = validate_backtest_results(results, data)
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
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

VALID_ACTIONS = {"BUY_HOME", "BUY_AWAY", "SKIP"}
"""Actions a strategy function may return."""

VALID_OUTCOMES = {"WIN", "LOSS"}
"""Possible trade outcomes."""

# Project root detection: works whether imported from src/ or tools/
_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent.parent.parent  # src/cuic_quant/backtest -> project root
DATA_DIR = PROJECT_ROOT / "data"
DUMMY_CSV = DATA_DIR / "dummy_backtest_input.csv"
TEST_CSV = DATA_DIR / "test_games.csv"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_backtest_data(
    start_date: str,
    end_date: str,
    csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load historical game data for backtesting.

    What: Loads a DataFrame of completed games with odds and outcomes,
    filtered to a date range and sorted chronologically.

    Why: The backtester needs historical game data to simulate strategy
    performance. This function abstracts the data source — it tries the
    Railway PostgreSQL database first (production), then falls back to a
    local CSV file (development/testing).

    How:
        1. Check if DATABASE_URL environment variable is set.
        2. If yes, query the sportsbook_matches + sportsbook_odds tables
           via SQLAlchemy, filter by date range, return sorted DataFrame.
        3. If no (or if the DB query fails), load from a local CSV file.
        4. Filter the CSV by date range, sort by timestamp, return.

    Args:
        start_date: Start of date range, inclusive. Format: "YYYY-MM-DD".
        end_date: End of date range, inclusive. Format: "YYYY-MM-DD".
        csv_path: Path to fallback CSV file. If None, defaults to
            data/dummy_backtest_input.csv.

    Returns:
        DataFrame with columns: timestamp (datetime), game (str),
        home_team (str), away_team (str), home_odds (float),
        away_odds (float), home_win (int: 1 or 0).
        Sorted by timestamp ascending.

    Raises:
        FileNotFoundError: If no database is available and no CSV exists
            at the specified path.
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(database_url)
            query = text("""
                SELECT
                    m.commence_time AS timestamp,
                    m.home_team || ' vs ' || m.away_team AS game,
                    m.home_team,
                    m.away_team,
                    o.home_odds,
                    o.away_odds,
                    m.home_win
                FROM sportsbook_matches m
                JOIN sportsbook_odds o ON m.id = o.match_id
                WHERE m.commence_time >= :start_date
                  AND m.commence_time <= :end_date
                ORDER BY m.commence_time ASC
            """)

            with engine.connect() as conn:
                df = pd.read_sql(
                    query, conn,
                    params={"start_date": start_date, "end_date": end_date},
                )

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            print(f"Loaded {len(df)} rows from Railway database.")
            return df

        except Exception as e:
            print(f"Database connection failed ({e}), falling back to CSV.")

    # Fallback to CSV
    if csv_path is None:
        csv_path = DUMMY_CSV
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"No CSV found at {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # Filter by date range
    mask = (df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)
    df = df.loc[mask].sort_values("timestamp").reset_index(drop=True)

    print(f"Loaded {len(df)} rows from {csv_path.name}.")
    return df


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
            win probability. Default None.
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

    context: dict[str, Any] = {
        "initial_bankroll": initial_bankroll,
        "bankroll": bankroll,
        "trade_count": 0,
        "cumulative_pnl": 0.0,
    }

    for _, row in data.iterrows():
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

        # Remove outcome column to prevent data leakage
        strategy_row = row.drop(labels=["home_win"])
        signal = strategy_fn(strategy_row, context)
        action = signal.get("action", "SKIP")

        if action == "SKIP":
            continue

        # Determine initial bet size from strategy signal
        bet_size = signal.get("size", 0.0)
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
            continue  # Invalid action, skip

        # Apply Kelly position sizing if enabled
        if position_sizing == "kelly":
            confidence = signal.get("confidence")
            if confidence is not None and 0 < confidence < 1:
                from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction as calc_kelly
                kelly_size = calc_kelly(
                    win_probability=confidence,
                    decimal_odds=odds,
                    kelly_fraction=kelly_fraction,
                )
                bet_size = round(kelly_size * bankroll, 2)
                if bet_size <= 0:
                    continue

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

    # Return DataFrame with correct columns even if empty
    if not trades:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame(trades)[OUTPUT_COLUMNS]


# ---------------------------------------------------------------------------
# Example strategy
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

    How: Ignores all inputs and returns a fixed signal dict with
    action='BUY_HOME', confidence=0.5, and size=100.

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

    What: Bets on home team with confidence = implied_prob + 0.05.
    Why: Demonstrates how to wire a strategy's confidence field into
        the Kelly position sizing system in backtest().

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


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_backtest_results(
    results: pd.DataFrame,
    input_data: pd.DataFrame,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
) -> dict[str, Any]:
    """Validate backtest results for correctness and data leakage.

    What: Runs a comprehensive suite of checks on backtest output to
    verify schema compliance, mathematical correctness, and absence
    of data leakage.

    Why: Backtester bugs can silently produce wrong results — inflated
    win rates, incorrect PnL, or outcomes that could only be known
    through future data leakage. This function catches those errors
    before anyone draws conclusions from bad data.

    Checks (11 total across 3 categories):

        **Schema Validation (5 checks)**
        1. Column names — output has exactly the 9 required columns
           in the correct order.
        2. Valid actions — every action is BUY_HOME or BUY_AWAY
           (no SKIP rows in output).
        3. Valid outcomes — every outcome is WIN or LOSS.
        4. Positive bet sizes — no zero or negative bets.
        5. Valid odds — all decimal odds are > 1.0.

        **Math Correctness (4 checks)**
        6. PnL formula — WIN trades pay bet_size * (odds - 1),
           LOSS trades pay -bet_size.
        7. Cumulative PnL — the cumulative_pnl column is a correct
           running sum of pnl.
        8. Bankroll tracking — bankroll = initial_bankroll +
           cumulative_pnl at every row.
        9. No overbetting — no bet exceeds the bankroll available
           at the time of the bet.

        **Data Leakage Detection (2 checks)**
        10. Outcome consistency — each trade's outcome is
            cross-referenced against the original input data's
            home_win column. If a strategy somehow produced outcomes
            that don't match the actual game results, this catches
            it (e.g. a bug that lets the strategy see the outcome
            before betting).
        11. Chronological order — trades must be in timestamp order.
            Out-of-order trades could indicate the strategy accessed
            future game data to make decisions.

    Args:
        results: DataFrame output from backtest() with 9 columns.
        input_data: The original DataFrame passed to backtest(), used to
            cross-reference outcomes and verify game existence.
        initial_bankroll: The initial_bankroll value used in the backtest.
            Needed to verify bankroll column calculations.

    Returns:
        Dict with keys:
        - passed (bool): True if ALL checks pass.
        - checks_run (int): Total number of checks executed.
        - checks_passed (int): Number of checks that passed.
        - failures (list[str]): Descriptions of each failed check.
    """
    failures: list[str] = []
    checks_run = 0

    # --- Handle empty results ---
    if len(results) == 0:
        checks_run += 1
        if results.columns.tolist() == OUTPUT_COLUMNS:
            return {
                "passed": True,
                "checks_run": checks_run,
                "checks_passed": checks_run,
                "failures": [],
            }
        else:
            failures.append(
                f"Schema: empty results have wrong columns. "
                f"Expected {OUTPUT_COLUMNS}, got {results.columns.tolist()}"
            )
            return {
                "passed": False,
                "checks_run": checks_run,
                "checks_passed": 0,
                "failures": failures,
            }

    # ===================================================================
    # Category 1: Schema Validation
    # ===================================================================

    # Check 1: Column names
    checks_run += 1
    if results.columns.tolist() != OUTPUT_COLUMNS:
        failures.append(
            f"Schema: column mismatch. "
            f"Expected {OUTPUT_COLUMNS}, got {results.columns.tolist()}"
        )
        # Cannot run further checks without correct columns
        return {
            "passed": False,
            "checks_run": checks_run,
            "checks_passed": 0,
            "failures": failures,
        }

    # Check 2: Actions are valid (results should only contain trade actions, not SKIP)
    checks_run += 1
    trade_actions = VALID_ACTIONS - {"SKIP"}
    invalid_actions = set(results["action"].unique()) - trade_actions
    if invalid_actions:
        failures.append(f"Schema: invalid actions found: {invalid_actions}")

    # Check 3: Outcomes are valid
    checks_run += 1
    invalid_outcomes = set(results["outcome"].unique()) - VALID_OUTCOMES
    if invalid_outcomes:
        failures.append(f"Schema: invalid outcomes found: {invalid_outcomes}")

    # Check 4: Bet sizes positive
    checks_run += 1
    if (results["bet_size"] <= 0).any():
        failures.append("Schema: found non-positive bet_size values")

    # Check 5: Odds are valid (decimal odds must be > 1.0)
    checks_run += 1
    if (results["odds"] <= 1.0).any():
        bad_odds = results[results["odds"] <= 1.0]
        failures.append(
            f"Schema: {len(bad_odds)} rows have odds <= 1.0 "
            f"(invalid decimal odds). First: Row {bad_odds.index[0]}, "
            f"odds={bad_odds['odds'].iloc[0]}"
        )

    # ===================================================================
    # Category 2: Math Correctness
    # ===================================================================

    # Check 5: PnL calculations
    checks_run += 1
    pnl_errors = []
    for idx, row in results.iterrows():
        if row["outcome"] == "WIN":
            expected_pnl = round(row["bet_size"] * (row["odds"] - 1) * (1 - cost_pct) - cost_flat, 2)
        else:
            expected_pnl = round(-row["bet_size"] - cost_flat, 2)

        if abs(row["pnl"] - expected_pnl) > 0.01:
            pnl_errors.append(
                f"Row {idx}: pnl={row['pnl']}, expected={expected_pnl}"
            )

    if pnl_errors:
        failures.append(
            f"Math: incorrect pnl calculations in {len(pnl_errors)} rows. "
            f"First: {pnl_errors[0]}"
        )

    # Check 6: Cumulative PnL is running sum
    checks_run += 1
    running_sum = 0.0
    cum_pnl_errors = []
    for idx, row in results.iterrows():
        running_sum = round(running_sum + row["pnl"], 2)
        if abs(row["cumulative_pnl"] - running_sum) > 0.01:
            cum_pnl_errors.append(
                f"Row {idx}: cumulative_pnl={row['cumulative_pnl']}, "
                f"expected={running_sum}"
            )

    if cum_pnl_errors:
        failures.append(
            f"Math: incorrect cumulative_pnl in {len(cum_pnl_errors)} rows. "
            f"First: {cum_pnl_errors[0]}"
        )

    # Check 7: Bankroll = initial + cumulative_pnl
    checks_run += 1
    bankroll_errors = []
    for idx, row in results.iterrows():
        expected_bankroll = round(initial_bankroll + row["cumulative_pnl"], 2)
        if abs(row["bankroll"] - expected_bankroll) > 0.01:
            bankroll_errors.append(
                f"Row {idx}: bankroll={row['bankroll']}, "
                f"expected={expected_bankroll}"
            )

    if bankroll_errors:
        failures.append(
            f"Math: incorrect bankroll in {len(bankroll_errors)} rows. "
            f"First: {bankroll_errors[0]}"
        )

    # Check 8: No bet exceeds bankroll at time of bet
    checks_run += 1
    prev_bankroll = initial_bankroll
    overbet_errors = []
    for idx, row in results.iterrows():
        if row["bet_size"] > prev_bankroll + 0.01:
            overbet_errors.append(
                f"Row {idx}: bet_size={row['bet_size']}, "
                f"bankroll_at_time={prev_bankroll}"
            )
        prev_bankroll = row["bankroll"]

    if overbet_errors:
        failures.append(
            f"Math: bet exceeds bankroll in {len(overbet_errors)} rows. "
            f"First: {overbet_errors[0]}"
        )

    # ===================================================================
    # Category 3: Data Leakage Detection
    # ===================================================================

    # Check 9: Every game in results exists in input data
    checks_run += 1
    result_games = set(results["game"].unique())
    input_games = set(input_data["game"].unique())
    missing_games = result_games - input_games
    if missing_games:
        failures.append(
            f"Leakage: {len(missing_games)} games in results not found in "
            f"input data: {list(missing_games)[:3]}"
        )

    # Check 10: Outcomes match input data
    checks_run += 1
    outcome_errors = []
    for idx, row in results.iterrows():
        # Match on both game name AND timestamp to handle repeat matchups
        matching_input = input_data[
            (input_data["game"] == row["game"])
            & (input_data["timestamp"] == row["timestamp"])
        ]
        if len(matching_input) == 0:
            # Fallback to game-name-only match for backwards compatibility
            matching_input = input_data[input_data["game"] == row["game"]]
        if len(matching_input) == 0:
            continue  # Already caught by check 9

        input_row = matching_input.iloc[0]
        if row["action"] == "BUY_HOME":
            expected_outcome = "WIN" if input_row["home_win"] == 1 else "LOSS"
        elif row["action"] == "BUY_AWAY":
            expected_outcome = "WIN" if input_row["home_win"] == 0 else "LOSS"
        else:
            continue

        if row["outcome"] != expected_outcome:
            outcome_errors.append(
                f"Row {idx} ({row['game']}): outcome={row['outcome']}, "
                f"expected={expected_outcome} based on home_win={input_row['home_win']}"
            )

    if outcome_errors:
        failures.append(
            f"Leakage: outcome mismatch in {len(outcome_errors)} rows. "
            f"First: {outcome_errors[0]}"
        )

    # Check 11: Trades in chronological order
    checks_run += 1
    timestamps = pd.to_datetime(results["timestamp"])
    if not timestamps.is_monotonic_increasing:
        failures.append(
            "Leakage: trades are not in chronological order "
            "(possible future data access)"
        )

    # --- Build report ---
    checks_passed = checks_run - len(failures)
    return {
        "passed": len(failures) == 0,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Performance display helpers
# ---------------------------------------------------------------------------


def display_extended_metrics(
    results_df: pd.DataFrame,
    initial_bankroll: float = 10000.0,
) -> None:
    """Display 12 extended performance metrics for backtest results.

    Prints a formatted table of risk/reward statistics including Sharpe
    ratio, Sortino ratio, max drawdown, profit factor, streaks, and more.

    Args:
        results_df: DataFrame output from backtest().
        initial_bankroll: Starting bankroll used in the backtest.
    """
    if len(results_df) == 0:
        print("No trades to analyze.")
        return

    from cuic_quant.metrics import calculate_all_metrics

    metrics = calculate_all_metrics(results_df)

    pnl = results_df["pnl"]
    wins_pnl = pnl[results_df["outcome"] == "WIN"]
    losses_pnl = pnl[results_df["outcome"] == "LOSS"]

    avg_win = float(wins_pnl.mean()) if len(wins_pnl) > 0 else 0.0
    avg_loss = float(losses_pnl.mean()) if len(losses_pnl) > 0 else 0.0
    wl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # Sortino Ratio (penalizes downside volatility only)
    downside = pnl[pnl < 0]
    downside_std = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0
    sortino = (float(pnl.mean()) / downside_std * math.sqrt(252)) if downside_std > 0 else 0.0

    ev_per_bet = float(pnl.mean())

    # Streak calculation
    is_win = (results_df["outcome"] == "WIN").astype(int)
    groups = is_win.groupby((is_win != is_win.shift()).cumsum())
    longest_win = int(groups.sum().max())
    longest_loss = int((groups.count() - groups.sum()).max())

    best = float(pnl.max())
    worst = float(pnl.min())

    print("=" * 45)
    print("       EXTENDED PERFORMANCE METRICS")
    print("=" * 45)
    print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:>10.3f}")
    print(f"  Sortino Ratio:        {sortino:>10.3f}")
    print(f"  Max Drawdown:         {metrics['max_drawdown']:>9.1%}")
    print(f"  Profit Factor:        {metrics['profit_factor']:>10.3f}")
    print(f"  Average Win:          ${avg_win:>9.2f}")
    print(f"  Average Loss:         ${avg_loss:>9.2f}")
    print(f"  Win/Loss Ratio:       {wl_ratio:>10.3f}")
    print(f"  Expected Value/Bet:   ${ev_per_bet:>9.2f}")
    print(f"  Longest Win Streak:   {longest_win:>10d}")
    print(f"  Longest Loss Streak:  {longest_loss:>10d}")
    print(f"  Best Trade:           ${best:>9.2f}")
    print(f"  Worst Trade:          ${worst:>9.2f}")
    print("=" * 45)


def plot_performance(
    results_df: pd.DataFrame,
    title: str = "Backtest Performance",
    initial_bankroll: float = 10000.0,
) -> None:
    """Plot a 2x2 performance dashboard for backtest results.

    Panels: cumulative P&L, drawdown, P&L distribution, trade outcomes.

    Args:
        results_df: DataFrame output from backtest().
        title: Plot super-title.
        initial_bankroll: Starting bankroll used in the backtest.
    """
    if len(results_df) == 0:
        print("No trades to plot.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    pnl = results_df["pnl"]
    cum_pnl = results_df["cumulative_pnl"]
    trade_num = range(1, len(results_df) + 1)

    # 1. Cumulative PnL
    ax = axes[0, 0]
    ax.plot(trade_num, cum_pnl, color="#2196F3", linewidth=1.5)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    ax.fill_between(trade_num, cum_pnl, alpha=0.15, color="#2196F3")
    ax.set_title("Cumulative P&L")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("P&L ($)")
    ax.grid(True, alpha=0.3)

    # 2. Drawdown
    ax = axes[0, 1]
    equity = cum_pnl + initial_bankroll
    running_peak = equity.cummax()
    drawdown_pct = (running_peak - equity) / running_peak * 100
    ax.fill_between(trade_num, drawdown_pct, color="#F44336", alpha=0.4)
    ax.plot(trade_num, drawdown_pct, color="#F44336", linewidth=1.0)
    ax.set_title("Drawdown")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Drawdown (%)")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)

    # 3. PnL Distribution
    ax = axes[1, 0]
    ax.hist(pnl, bins=min(30, len(pnl)), color="#9C27B0", alpha=0.7, edgecolor="white")
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.8)
    mean_pnl = float(pnl.mean())
    ax.axvline(x=mean_pnl, color="#FF9800", linewidth=1.5, label=f"Mean: ${mean_pnl:.2f}")
    ax.set_title("P&L Distribution")
    ax.set_xlabel("P&L ($)")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Trade Outcomes
    ax = axes[1, 1]
    wins = int((results_df["outcome"] == "WIN").sum())
    losses = int((results_df["outcome"] == "LOSS").sum())
    bars = ax.bar(
        ["Wins", "Losses"], [wins, losses],
        color=["#4CAF50", "#F44336"], alpha=0.8, edgecolor="white",
    )
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, h, str(int(h)),
                ha="center", va="bottom", fontweight="bold")
    ax.set_title("Trade Outcomes")
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.show()
