"""Roster and player reference data collector."""

from __future__ import annotations

import logging

import pandas as pd
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams as nba_teams_static

from cuic_quant.data.nba.api_helper import fetch_endpoint
from cuic_quant.data.nba.constants import SEASONS, standardize_team_abbr

logger = logging.getLogger(__name__)


def collect_rosters(seasons: list[str] | None = None) -> pd.DataFrame:
    """Collect team rosters for all teams across given seasons."""
    seasons = seasons or SEASONS
    all_teams = nba_teams_static.get_teams()
    all_rosters = []

    for season in seasons:
        for team in all_teams:
            team_id = team["id"]
            abbr = standardize_team_abbr(team["abbreviation"])
            logger.debug("Collecting roster: %s %s", abbr, season)

            df = fetch_endpoint(
                commonteamroster.CommonTeamRoster,
                dataset_index=0,
                team_id=team_id,
                season=season,
            )
            if df.empty:
                continue

            df["team_abbr"] = abbr
            df["season"] = season
            all_rosters.append(df)

    if not all_rosters:
        return pd.DataFrame()

    combined = pd.concat(all_rosters, ignore_index=True)
    return _format_rosters(combined)


def _format_rosters(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {
        "PLAYER_ID": "player_id", "PLAYER": "player_name",
        "TeamID": "team_id", "NUM": "jersey_num",
        "POSITION": "position", "HEIGHT": "height", "WEIGHT": "weight",
        "BIRTH_DATE": "birth_date", "AGE": "age", "EXP": "experience",
        "SCHOOL": "school",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    final = ["player_id", "player_name", "team_id", "team_abbr", "season",
             "jersey_num", "position", "height", "weight",
             "birth_date", "age", "experience", "school"]
    return df[[c for c in final if c in df.columns]]


def build_players_reference(rosters_df: pd.DataFrame) -> pd.DataFrame:
    """Build deduplicated player master list from rosters."""
    if rosters_df.empty:
        return pd.DataFrame()

    players = rosters_df[["player_id", "player_name"]].drop_duplicates(subset=["player_id"])

    name_parts = players["player_name"].str.split(" ", n=1, expand=True)
    players["first_name"] = name_parts[0] if 0 in name_parts.columns else ""
    players["last_name"] = name_parts[1] if 1 in name_parts.columns else ""

    logger.info("Built player reference with %d unique players", len(players))
    return players[["player_id", "player_name", "first_name", "last_name"]]
