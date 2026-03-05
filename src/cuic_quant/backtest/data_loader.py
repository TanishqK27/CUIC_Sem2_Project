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


# ---------------------------------------------------------------------------
# Database query
# ---------------------------------------------------------------------------

# Joins historical_odds (opening/closing moneyline from multiple bookmakers)
# with combined_player_stats (actual final scores) to get ground-truth outcomes.
# commence_time is UTC; game_date in stats uses US Eastern, so we subtract
# 5 hours to align dates for the join.
_HISTORICAL_ODDS_QUERY = """
    WITH first_odds AS (
        SELECT DISTINCT ON (game_id)
            game_id, home_team_abbr, away_team_abbr,
            commence_time,
            (commence_time - interval '5 hours')::date AS game_date_est,
            avg_home_ml, avg_away_ml
        FROM historical_odds
        ORDER BY game_id, snapshot_timestamp ASC
    ),
    last_odds AS (
        SELECT DISTINCT ON (game_id)
            game_id,
            avg_home_ml AS closing_home_ml,
            avg_away_ml AS closing_away_ml
        FROM historical_odds
        ORDER BY game_id, snapshot_timestamp DESC
    ),
    scores AS (
        SELECT game_date::date AS gd,
               MAX(CASE WHEN team_pre_is_home = 1 THEN team_abbr END) AS home_abbr,
               MAX(CASE WHEN team_pre_is_home = 0 THEN team_abbr END) AS away_abbr,
               MAX(CASE WHEN team_pre_is_home = 1 THEN team_pts END) AS home_pts,
               MAX(CASE WHEN team_pre_is_home = 0 THEN team_pts END) AS away_pts
        FROM combined_player_stats
        WHERE team_pts IS NOT NULL
        GROUP BY game_id, game_date
    )
    SELECT fo.commence_time AS timestamp,
           fo.home_team_abbr || ' vs ' || fo.away_team_abbr AS game,
           fo.home_team_abbr AS home_team,
           fo.away_team_abbr AS away_team,
           fo.avg_home_ml AS open_home_ml,
           fo.avg_away_ml AS open_away_ml,
           lo.closing_home_ml,
           lo.closing_away_ml,
           CASE WHEN s.home_pts > s.away_pts THEN 1 ELSE 0 END AS home_win
    FROM first_odds fo
    JOIN last_odds lo ON fo.game_id = lo.game_id
    JOIN scores s ON fo.home_team_abbr = s.home_abbr
                  AND fo.game_date_est = s.gd
    WHERE fo.game_date_est >= :start_date
      AND fo.game_date_est < :end_date_exclusive
    ORDER BY fo.commence_time
"""


def _build_db_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    """Convert raw DB rows into backtester format with decimal odds."""
    rows: list[dict] = []

    for _, r in raw.iterrows():
        open_home_ml = r["open_home_ml"]
        open_away_ml = r["open_away_ml"]
        if pd.isna(open_home_ml) or pd.isna(open_away_ml):
            continue

        home_odds = _moneyline_to_decimal(float(open_home_ml))
        away_odds = _moneyline_to_decimal(float(open_away_ml))

        # Skip invalid odds (must be > 1.0 and <= 50.0).
        # Near-zero moneylines (e.g. avg_home_ml = -1.2 from averaging
        # bookmakers with opposing signs) produce absurd decimal odds.
        if home_odds <= 1.0 or away_odds <= 1.0:
            continue
        if home_odds > 50.0 or away_odds > 50.0:
            continue

        row = {
            "timestamp": r["timestamp"],
            "game": r["game"],
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "home_odds": round(home_odds, 4),
            "away_odds": round(away_odds, 4),
            "home_win": int(r["home_win"]),
        }

        # Closing odds for CLV analysis
        closing_home_ml = r.get("closing_home_ml")
        closing_away_ml = r.get("closing_away_ml")
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
    start_date: str | None = None,
    end_date: str | None = None,
    csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load historical game data for backtesting.

    Connects to the Railway PostgreSQL database and joins historical_odds
    (opening/closing moneyline from bookmakers) with combined_player_stats
    (actual final scores) to get one row per game with ground-truth
    outcomes — no guesswork.

    The database is IP-restricted to US servers. Connect to a US VPN
    before calling this function.

    If ``csv_path`` is provided, loads from that CSV instead (used by
    tests only).

    Args:
        start_date: Start of date range, inclusive. Format: "YYYY-MM-DD".
            Defaults to 2 years ago from today.
        end_date: End of date range, inclusive. Format: "YYYY-MM-DD".
            Defaults to today.
        csv_path: Path to a CSV file to load instead of the database.
            Only used for testing. When None (default), loads from DB.

    Returns:
        DataFrame with columns: timestamp (datetime), game (str),
        home_team (str), away_team (str), home_odds (float),
        away_odds (float), home_win (int: 1 or 0).
        Optionally includes closing_home_odds and closing_away_odds
        for CLV analysis.
        Sorted by timestamp ascending.

    Raises:
        RuntimeError: If the database connection or query fails.
            Connect to a US VPN and try again.
    """
    # Default date range: 2 years back → today
    if end_date is None:
        end_date = str(pd.Timestamp.now().normalize().date())
    if start_date is None:
        start_date = str(
            (pd.Timestamp(end_date) - pd.DateOffset(years=2)).date()
        )

    # If caller explicitly passed a CSV path, load from file (tests only).
    if csv_path is not None:
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"No CSV found at {csv_path}")

        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)
        mask = (df["timestamp"] >= start_date) & (df["timestamp"] < end_ts)
        df = df.loc[mask].sort_values(["timestamp", "game"]).reset_index(drop=True)
        logger.info("Loaded %d rows from %s.", len(df), csv_path.name)
        return df

    # Load from Railway PostgreSQL database
    database_url = os.environ.get("DATABASE_URL", "") or _RAILWAY_URL

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(
            database_url,
            connect_args={"connect_timeout": 10},
        )

        end_date_exclusive = str(
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        )

        query = text(_HISTORICAL_ODDS_QUERY)

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
                "odds and scores in the requested date range."
            )

        df = _build_db_dataframe(raw)

        if len(df) == 0:
            raise RuntimeError(
                f"Found {len(raw)} raw rows but 0 valid games after "
                "moneyline conversion."
            )

        df = df.sort_values(["timestamp", "game"]).reset_index(drop=True)
        logger.info(
            "Loaded %d games from database (%s to %s).",
            len(df), start_date, end_date,
        )
        return df

    except Exception as e:
        raise RuntimeError(
            f"Database connection failed: {e}\n\n"
            "The Railway database is IP-restricted to US servers.\n"
            "Connect to a US VPN and try again."
        ) from e


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DUMMY_CSV",
    "TEST_CSV",
    "load_backtest_data",
]
