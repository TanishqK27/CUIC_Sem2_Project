"""Team and player season aggregate stats collector."""

from __future__ import annotations

import logging

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashteamstats

from cuic_quant.data.nba.api_helper import fetch_endpoint
from cuic_quant.data.nba.constants import SEASONS, standardize_team_abbr

logger = logging.getLogger(__name__)


def collect_team_stats(seasons: list[str] | None = None) -> pd.DataFrame:
    """Collect team season aggregates (basic + advanced)."""
    seasons = seasons or SEASONS
    all_frames = []

    for season in seasons:
        logger.info("Collecting team stats for %s", season)

        basic = fetch_endpoint(
            leaguedashteamstats.LeagueDashTeamStats,
            dataset_index=0,
            season=season,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Base",
        )

        advanced = fetch_endpoint(
            leaguedashteamstats.LeagueDashTeamStats,
            dataset_index=0,
            season=season,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Advanced",
        )

        if basic.empty:
            logger.warning("No team stats for %s", season)
            continue

        if not advanced.empty:
            adv_cols = ["TEAM_ID", "OFF_RATING", "DEF_RATING", "NET_RATING",
                        "PACE", "EFG_PCT", "TS_PCT", "OREB_PCT", "DREB_PCT",
                        "TM_TOV_PCT"]
            adv_existing = [c for c in adv_cols if c in advanced.columns]
            merged = basic.merge(advanced[adv_existing], on="TEAM_ID", how="left", suffixes=("", "_adv"))
        else:
            merged = basic

        merged["season"] = season
        all_frames.append(merged)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    return _format_team_stats(combined)


def _format_team_stats(df: pd.DataFrame) -> pd.DataFrame:
    if "TEAM_ABBREVIATION" in df.columns:
        df["team_abbr"] = df["TEAM_ABBREVIATION"].apply(standardize_team_abbr)

    col_map = {
        "TEAM_ID": "team_id", "TEAM_NAME": "team_name",
        "GP": "gp", "W": "w", "L": "l", "W_PCT": "w_pct",
        "PTS": "ppg", "REB": "rpg", "AST": "apg",
        "STL": "spg", "BLK": "bpg", "TOV": "topg",
        "FG_PCT": "fg_pct", "FG3_PCT": "fg3_pct", "FT_PCT": "ft_pct",
        "OFF_RATING": "off_rating", "DEF_RATING": "def_rating",
        "NET_RATING": "net_rating", "PACE": "pace",
        "EFG_PCT": "efg_pct", "TS_PCT": "ts_pct",
        "OREB_PCT": "oreb_pct", "DREB_PCT": "dreb_pct",
        "TM_TOV_PCT": "tov_pct",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    if "ppg" in df.columns and "PLUS_MINUS" in df.columns:
        df["oppg"] = df["ppg"] - df["PLUS_MINUS"]
    elif "OPP_PTS" in df.columns:
        df["oppg"] = df["OPP_PTS"]

    final = ["team_id", "team_name", "team_abbr", "season",
             "gp", "w", "l", "w_pct", "ppg", "oppg", "rpg", "apg",
             "spg", "bpg", "topg", "fg_pct", "fg3_pct", "ft_pct",
             "off_rating", "def_rating", "net_rating", "pace",
             "efg_pct", "ts_pct", "oreb_pct", "dreb_pct", "tov_pct"]
    return df[[c for c in final if c in df.columns]]


def collect_player_stats(seasons: list[str] | None = None) -> pd.DataFrame:
    """Collect player season aggregates (basic + advanced)."""
    seasons = seasons or SEASONS
    all_frames = []

    for season in seasons:
        logger.info("Collecting player stats for %s", season)

        basic = fetch_endpoint(
            leaguedashplayerstats.LeagueDashPlayerStats,
            dataset_index=0,
            season=season,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Base",
        )

        advanced = fetch_endpoint(
            leaguedashplayerstats.LeagueDashPlayerStats,
            dataset_index=0,
            season=season,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Advanced",
        )

        if basic.empty:
            logger.warning("No player stats for %s", season)
            continue

        if not advanced.empty:
            adv_cols = ["PLAYER_ID", "OFF_RATING", "DEF_RATING", "NET_RATING",
                        "USG_PCT", "TS_PCT", "EFG_PCT"]
            adv_existing = [c for c in adv_cols if c in advanced.columns]
            merged = basic.merge(advanced[adv_existing], on="PLAYER_ID", how="left", suffixes=("", "_adv"))
        else:
            merged = basic

        merged["season"] = season
        all_frames.append(merged)

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    return _format_player_stats(combined)


def _format_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    if "TEAM_ABBREVIATION" in df.columns:
        df["team_abbr"] = df["TEAM_ABBREVIATION"].apply(standardize_team_abbr)

    col_map = {
        "PLAYER_ID": "player_id", "PLAYER_NAME": "player_name", "TEAM_ID": "team_id",
        "AGE": "age", "GP": "gp", "GS": "gs", "MIN": "mpg",
        "PTS": "ppg", "REB": "rpg", "AST": "apg", "STL": "spg",
        "BLK": "bpg", "TOV": "topg",
        "FG_PCT": "fg_pct", "FG3_PCT": "fg3_pct", "FT_PCT": "ft_pct",
        "PLUS_MINUS": "plus_minus",
        "OFF_RATING": "off_rating", "DEF_RATING": "def_rating",
        "NET_RATING": "net_rating", "USG_PCT": "usg_pct",
        "TS_PCT": "ts_pct", "EFG_PCT": "efg_pct",
        "NBA_FANTASY_PTS": "fantasy_pts",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    final = ["player_id", "player_name", "team_id", "team_abbr", "season",
             "age", "gp", "gs", "mpg", "ppg", "rpg", "apg", "spg", "bpg", "topg",
             "fg_pct", "fg3_pct", "ft_pct", "plus_minus",
             "off_rating", "def_rating", "net_rating", "usg_pct",
             "ts_pct", "efg_pct", "fantasy_pts"]
    return df[[c for c in final if c in df.columns]]
