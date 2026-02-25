"""Injury report collector using nbainjuries package."""

from __future__ import annotations

import logging

import pandas as pd

from cuic_quant.data.nba.constants import SEASONS, standardize_team_abbr

logger = logging.getLogger(__name__)


def collect_injuries(seasons: list[str] | None = None) -> pd.DataFrame:
    """Collect injury reports using the nbainjuries package."""
    try:
        import nbainjuries
    except ImportError:
        logger.warning(
            "nbainjuries package not installed. Skipping injury collection. "
            "Install with: pip install nbainjuries"
        )
        return pd.DataFrame()

    seasons = seasons or SEASONS
    all_injuries = []

    for season in seasons:
        logger.info("Collecting injuries for %s", season)
        try:
            df = nbainjuries.get_injuries(season=season)
            if df is not None and not df.empty:
                df["season"] = season
                all_injuries.append(df)
        except Exception:
            logger.exception("Failed to collect injuries for %s", season)

    if not all_injuries:
        logger.info("No injury data collected")
        return pd.DataFrame()

    combined = pd.concat(all_injuries, ignore_index=True)
    return _format_injuries(combined)


def _format_injuries(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {
        "Player_ID": "player_id", "player_id": "player_id",
        "Player": "player_name", "player_name": "player_name",
        "Team": "team_abbr", "team": "team_abbr",
        "Date": "date", "date": "date",
        "Status": "status", "status": "status",
        "Description": "reason", "Reason": "reason", "reason": "reason",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    if "team_abbr" in df.columns:
        df["team_abbr"] = df["team_abbr"].apply(
            lambda x: standardize_team_abbr(x) if pd.notna(x) and x else x
        )

    final = ["player_id", "player_name", "team_abbr", "date",
             "status", "reason", "season"]
    return df[[c for c in final if c in df.columns]]
