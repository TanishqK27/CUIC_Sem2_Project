"""League standings collector."""

from __future__ import annotations

import logging

import pandas as pd
from nba_api.stats.endpoints import leaguestandingsv3

from cuic_quant.data.nba.api_helper import fetch_endpoint
from cuic_quant.data.nba.constants import SEASONS, standardize_team_abbr

logger = logging.getLogger(__name__)


def collect_standings(seasons: list[str] | None = None) -> pd.DataFrame:
    """Collect league standings for specified seasons."""
    seasons = seasons or SEASONS
    all_standings = []

    for season in seasons:
        logger.info("Collecting standings for %s", season)
        df = fetch_endpoint(
            leaguestandingsv3.LeagueStandingsV3,
            dataset_index=0,
            season=season,
            league_id="00",
            season_type="Regular Season",
        )
        if df.empty:
            logger.warning("No standings data for %s", season)
            continue

        col_map = {
            "TeamID": "team_id",
            "TeamCity": "city",
            "TeamName": "team_name",
            "TeamSlug": "team_slug",
            "Conference": "conference",
            "Division": "division",
            "WINS": "w",
            "LOSSES": "l",
            "WinPCT": "w_pct",
            "DivisionRank": "div_rank",
            "HOME": "home_record",
            "ROAD": "road_record",
            "L10": "l10",
            "CurrentStreak": "streak",
        }
        rename = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=rename)

        if "TeamAbbreviation" in df.columns:
            df["team_abbr"] = df["TeamAbbreviation"].apply(
                lambda x: standardize_team_abbr(x) if pd.notna(x) else x
            )
        elif "team_slug" in df.columns:
            df["team_abbr"] = df["team_slug"].str.upper().apply(
                lambda x: standardize_team_abbr(x) if pd.notna(x) else x
            )

        df["season"] = season

        if "conference" in df.columns:
            df["conf_rank"] = df.groupby("conference").cumcount() + 1
        else:
            df["conf_rank"] = 0

        final_cols = [
            "team_id", "team_abbr", "season", "conference", "division",
            "w", "l", "w_pct", "conf_rank", "div_rank",
            "home_record", "road_record", "l10", "streak",
        ]
        existing_cols = [c for c in final_cols if c in df.columns]
        all_standings.append(df[existing_cols])

    if not all_standings:
        return pd.DataFrame()
    result = pd.concat(all_standings, ignore_index=True)
    logger.info("Collected %d standing rows across %d seasons", len(result), len(seasons))
    return result
