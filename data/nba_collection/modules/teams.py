"""Team reference data collector."""

from __future__ import annotations

import logging

import pandas as pd
from nba_api.stats.static import teams as nba_teams_static

from cuic_quant.data.nba.constants import standardize_team_abbr

logger = logging.getLogger(__name__)

TEAM_CONFERENCE: dict[str, str] = {
    "ATL": "East", "BOS": "East", "BKN": "East", "CHA": "East", "CHI": "East",
    "CLE": "East", "DET": "East", "IND": "East", "MIA": "East", "MIL": "East",
    "NYK": "East", "ORL": "East", "PHI": "East", "TOR": "East", "WAS": "East",
    "DAL": "West", "DEN": "West", "GSW": "West", "HOU": "West", "LAC": "West",
    "LAL": "West", "MEM": "West", "MIN": "West", "NOP": "West", "OKC": "West",
    "PHX": "West", "POR": "West", "SAC": "West", "SAS": "West", "UTA": "West",
}

TEAM_DIVISION: dict[str, str] = {
    "ATL": "Southeast", "BOS": "Atlantic", "BKN": "Atlantic", "CHA": "Southeast",
    "CHI": "Central", "CLE": "Central", "DAL": "Southwest", "DEN": "Northwest",
    "DET": "Central", "GSW": "Pacific", "HOU": "Southwest", "IND": "Central",
    "LAC": "Pacific", "LAL": "Pacific", "MEM": "Southwest", "MIA": "Southeast",
    "MIL": "Central", "MIN": "Northwest", "NOP": "Southwest", "NYK": "Atlantic",
    "OKC": "Northwest", "ORL": "Southeast", "PHI": "Atlantic", "PHX": "Pacific",
    "POR": "Northwest", "SAC": "Pacific", "SAS": "Southwest", "TOR": "Atlantic",
    "UTA": "Northwest", "WAS": "Southeast",
}


def collect_teams() -> pd.DataFrame:
    """Collect NBA team reference data from static nba_api data."""
    logger.info("Collecting team reference data")
    raw_teams = nba_teams_static.get_teams()

    rows = []
    for t in raw_teams:
        abbr = standardize_team_abbr(t["abbreviation"])
        rows.append({
            "team_id": t["id"],
            "team_abbr": abbr,
            "team_name": t["full_name"],
            "city": t["city"],
            "state": t["state"],
            "conference": TEAM_CONFERENCE.get(abbr, ""),
            "division": TEAM_DIVISION.get(abbr, ""),
        })

    df = pd.DataFrame(rows)
    logger.info("Collected %d teams", len(df))
    return df
