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

import os
from pathlib import Path
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
