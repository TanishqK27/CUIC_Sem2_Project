"""Data loading for the backtester.

Provides load_backtest_data() which tries Railway PostgreSQL first,
then falls back to local CSV.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

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
    strict: bool = False,
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
        strict: If True, raise RuntimeError when the database query fails
            instead of falling back to CSV. Default False.

    Returns:
        DataFrame with columns: timestamp (datetime), game (str),
        home_team (str), away_team (str), home_odds (float),
        away_odds (float), home_win (int: 1 or 0).
        Sorted by timestamp ascending.

    Raises:
        FileNotFoundError: If no database is available and no CSV exists
            at the specified path.
        RuntimeError: If strict=True and the database query fails.
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
            # U4: Apply same deterministic sort as CSV path
            df = df.sort_values(["timestamp", "game"]).reset_index(drop=True)
            print(f"Loaded {len(df)} rows from Railway database.")
            return df

        except Exception as e:
            if strict:
                raise RuntimeError(
                    f"Database query failed and strict=True: {e}"
                ) from e
            warnings.warn(
                f"DATABASE_URL is set but query failed ({e}). "
                f"Falling back to local CSV — results may use synthetic data.",
                RuntimeWarning,
                stacklevel=2,
            )

    # Fallback to CSV
    if csv_path is None:
        csv_path = DUMMY_CSV
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"No CSV found at {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # Filter by date range
    mask = (df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)
    df = df.loc[mask].sort_values(["timestamp", "game"]).reset_index(drop=True)

    print(f"Loaded {len(df)} rows from {csv_path.name}.")
    return df


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DUMMY_CSV",
    "TEST_CSV",
    "load_backtest_data",
]
