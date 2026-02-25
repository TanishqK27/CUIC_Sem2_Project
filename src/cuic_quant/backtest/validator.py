"""Backtest result validation.

Provides validate_backtest_results() which runs 12 checks across
schema validation, math correctness, and data leakage detection.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from cuic_quant.backtest.engine import (
    OUTPUT_COLUMNS,
    VALID_ACTIONS,
    VALID_OUTCOMES,
)


def validate_backtest_results(
    results: pd.DataFrame,
    input_data: pd.DataFrame,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
) -> dict[str, Any]:
    """Validate backtest results for correctness and data leakage.

    Checks (12 total across 3 categories):

        **Schema Validation (5 checks)**
        1. Column names — output has exactly the 9 required columns.
        2. Valid actions — every action is BUY_HOME or BUY_AWAY.
        3. Valid outcomes — every outcome is WIN or LOSS.
        4. Positive bet sizes — no zero or negative bets.
        5. Valid odds — all decimal odds are > 1.0.

        **Math Correctness (4 checks)**
        6. PnL formula — WIN = bet_size * (odds - 1), LOSS = -bet_size.
        7. Cumulative PnL — correct running sum of pnl.
        8. Bankroll tracking — bankroll = initial_bankroll + cumulative_pnl.
        9. No overbetting — no bet exceeds available bankroll.

        **Data Leakage Detection (3 checks)**
        10. Game existence — every game in results exists in input data.
        11. Outcome consistency — outcomes match input data's home_win.
        12. Chronological order — trades in timestamp order.

    Args:
        results: DataFrame output from backtest() with 9 columns.
        input_data: The original DataFrame passed to backtest().
        initial_bankroll: The initial_bankroll value used in the backtest.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat cost per trade.

    Returns:
        Dict with passed, checks_run, checks_passed, failures.
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
        return {
            "passed": False,
            "checks_run": checks_run,
            "checks_passed": 0,
            "failures": failures,
        }

    # Check 2: Actions are valid
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

    # Check 5: Odds are valid
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

    # Check 6: PnL calculations
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

    # Check 7: Cumulative PnL is running sum
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

    # Check 8: Bankroll = initial + cumulative_pnl
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

    # Check 9: No bet exceeds bankroll at time of bet
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

    # Check 10: Every game in results exists in input data
    checks_run += 1
    result_games = set(results["game"].unique())
    input_games = set(input_data["game"].unique())
    missing_games = result_games - input_games
    if missing_games:
        failures.append(
            f"Leakage: {len(missing_games)} games in results not found in "
            f"input data: {list(missing_games)[:3]}"
        )

    # Check 11: Outcomes match input data
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
            continue  # Already caught by check 10

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

    # Check 12: Trades in chronological order
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


__all__ = [
    "validate_backtest_results",
]
