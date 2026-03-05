"""Data loading for the backtester.

Provides load_backtest_data() which tries Railway PostgreSQL first,
then falls back to local CSV.
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent.parent.parent  # src/cuic_quant/backtest -> project root
DATA_DIR = PROJECT_ROOT / "data"
DUMMY_CSV = DATA_DIR / "dummy_backtest_input.csv"
TEST_CSV = DATA_DIR / "test_games.csv"

# Railway PostgreSQL connection (IP-restricted — works from Colab/VPN).
# Falls back to DATABASE_URL env var if set.
_RAILWAY_URL = (
    "postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU"
    "@switchyard.proxy.rlwy.net:44650/railway"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _moneyline_to_decimal(ml: float) -> float:
    """Convert American moneyline odds to decimal odds.

    Examples:
        +150 → 2.50  (bet $100 to win $150, total return $250)
        -200 → 1.50  (bet $200 to win $100, total return $300)
    """
    if ml > 0:
        return 1.0 + ml / 100.0
    elif ml < 0:
        return 1.0 + 100.0 / abs(ml)
    else:
        return 1.0  # Even money


def _build_game_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-snapshot rows into one row per game.

    For each game:
    - timestamp: earliest snapshot (game commence time)
    - home_odds / away_odds: first snapshot's moneyline → decimal
    - closing_home_odds / closing_away_odds: last snapshot's moneyline → decimal
    - home_win: derived from final pm_home_prob (≥0.9 → 1, ≤0.1 → 0)
    """
    rows: list[dict] = []

    for game_name, grp in raw.groupby("game"):
        grp = grp.sort_values("timestamp")
        first = grp.iloc[0]
        last = grp.iloc[-1]

        # Derive outcome from final Polymarket probability.
        # Settled markets go to ~1.0 (home win) or ~0.0 (away win).
        final_prob = last["pm_home_prob"]
        if pd.isna(final_prob):
            continue  # Can't determine outcome
        if final_prob >= 0.9:
            home_win = 1
        elif final_prob <= 0.1:
            home_win = 0
        else:
            # Game hasn't settled or ambiguous — skip
            continue

        # Convert moneyline to decimal odds (opening)
        home_ml = first.get("sb_home_ml")
        away_ml = first.get("sb_away_ml")
        if pd.isna(home_ml) or pd.isna(away_ml):
            continue  # No sportsbook odds available

        home_odds = _moneyline_to_decimal(float(home_ml))
        away_odds = _moneyline_to_decimal(float(away_ml))

        # Skip invalid odds (must be > 1.0)
        if home_odds <= 1.0 or away_odds <= 1.0:
            continue

        row = {
            "timestamp": first["timestamp"],
            "game": game_name,
            "home_team": first["home"],
            "away_team": first["away"],
            "home_odds": round(home_odds, 4),
            "away_odds": round(away_odds, 4),
            "home_win": home_win,
        }

        # Closing odds for CLV analysis
        closing_home_ml = last.get("sb_home_ml")
        closing_away_ml = last.get("sb_away_ml")
        if not pd.isna(closing_home_ml) and not pd.isna(closing_away_ml):
            row["closing_home_odds"] = round(
                _moneyline_to_decimal(float(closing_home_ml)), 4
            )
            row["closing_away_odds"] = round(
                _moneyline_to_decimal(float(closing_away_ml)), 4
            )

        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=[
            "timestamp", "game", "home_team", "away_team",
            "home_odds", "away_odds", "home_win",
        ])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


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
        1. Try the Railway PostgreSQL database (price_snapshots table).
           Collapses multiple snapshots per game into one row with opening
           odds, closing odds, and outcome derived from final Polymarket
           settlement probability.
        2. If the DB is unavailable (IP restriction, timeout, etc.), fall
           back to a local CSV file.

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
        Optionally includes closing_home_odds and closing_away_odds
        for CLV analysis.
        Sorted by timestamp ascending.

    Raises:
        FileNotFoundError: If no database is available and no CSV exists
            at the specified path.
        RuntimeError: If strict=True and the database query fails.
    """
    database_url = os.environ.get("DATABASE_URL", "")

    if database_url:
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(
                database_url,
                connect_args={"connect_timeout": 10},
            )

            # Query all snapshots for games in the date range.
            # We collapse them into one row per game in Python (_build_game_rows)
            # because the aggregation logic (first/last per game, moneyline
            # conversion, outcome derivation) is complex for raw SQL.
            query = text("""
                SELECT
                    timestamp,
                    game,
                    home,
                    away,
                    pm_home_prob,
                    sb_home_ml,
                    sb_away_ml
                FROM price_snapshots
                WHERE game_date >= :start_date
                  AND game_date < :end_date_exclusive
                  AND sb_home_ml IS NOT NULL
                  AND sb_away_ml IS NOT NULL
                ORDER BY game, timestamp ASC
            """)

            end_date_exclusive = str(
                pd.Timestamp(end_date) + pd.Timedelta(days=1)
            )

            with engine.connect() as conn:
                raw = pd.read_sql(
                    query, conn,
                    params={
                        "start_date": start_date,
                        "end_date_exclusive": end_date_exclusive,
                    },
                )

            if len(raw) == 0:
                raise RuntimeError(
                    "Database query returned 0 rows — no games with "
                    "sportsbook odds in the requested date range."
                )

            df = _build_game_rows(raw)

            if len(df) == 0:
                raise RuntimeError(
                    f"Found {len(raw)} snapshots but 0 settled games — "
                    "no games with clear outcomes in the date range."
                )

            df = df.sort_values(["timestamp", "game"]).reset_index(drop=True)
            logger.info(
                "Loaded %d games from Railway database (%d raw snapshots).",
                len(df), len(raw),
            )
            return df

        except Exception as e:
            if strict:
                raise RuntimeError(
                    f"Database query failed and strict=True: {e}"
                ) from e
            warnings.warn(
                f"Database query failed ({e}). "
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

    # Filter by date range (use < end + 1 day so intra-day rows are included)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    mask = (df["timestamp"] >= start_date) & (df["timestamp"] < end_ts)
    df = df.loc[mask].sort_values(["timestamp", "game"]).reset_index(drop=True)

    logger.info("Loaded %d rows from %s.", len(df), csv_path.name)
    return df


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DUMMY_CSV",
    "TEST_CSV",
    "load_backtest_data",
]
