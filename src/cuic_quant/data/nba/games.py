"""Game discovery and quarter score collection."""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, scoreboardv2

from cuic_quant.data.nba.api_helper import fetch_endpoint
from cuic_quant.data.nba.constants import SEASONS, standardize_team_abbr

logger = logging.getLogger(__name__)


def discover_games(
    seasons: list[str] | None = None,
    since_date: str | None = None,
) -> pd.DataFrame:
    """Discover all NBA regular season games for given seasons."""
    seasons = seasons or SEASONS
    all_games = []

    for season in seasons:
        logger.info("Discovering games for %s", season)
        df = fetch_endpoint(
            leaguegamefinder.LeagueGameFinder,
            dataset_index=0,
            season_nullable=season,
            league_id_nullable="00",
            season_type_nullable="Regular Season",
        )
        if df.empty:
            logger.warning("No games found for %s", season)
            continue

        df["season"] = season
        all_games.append(df)

    if not all_games:
        return pd.DataFrame()

    raw = pd.concat(all_games, ignore_index=True)

    if since_date:
        raw["GAME_DATE"] = pd.to_datetime(raw["GAME_DATE"])
        raw = raw[raw["GAME_DATE"] >= since_date]

    return _build_games_df(raw)


def _build_games_df(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform per-team game rows into per-game rows with home/away."""
    home = raw[raw["MATCHUP"].str.contains("vs.", na=False)].copy()
    away = raw[raw["MATCHUP"].str.contains("@", na=False)].copy()

    home = home.rename(columns={
        "TEAM_ID": "home_team_id",
        "TEAM_ABBREVIATION": "home_team_abbr",
        "PTS": "home_score",
    })
    away = away.rename(columns={
        "TEAM_ID": "away_team_id",
        "TEAM_ABBREVIATION": "away_team_abbr",
        "PTS": "away_score",
    })

    merged = home.merge(
        away[["GAME_ID", "away_team_id", "away_team_abbr", "away_score"]],
        on="GAME_ID",
        how="inner",
    )

    merged["home_team_abbr"] = merged["home_team_abbr"].apply(standardize_team_abbr)
    merged["away_team_abbr"] = merged["away_team_abbr"].apply(standardize_team_abbr)
    merged["home_win"] = (merged["home_score"] > merged["away_score"]).astype(int)
    merged["game_date"] = pd.to_datetime(merged["GAME_DATE"]).dt.strftime("%Y-%m-%d")

    result = merged.rename(columns={"GAME_ID": "game_id"})[
        ["game_id", "game_date", "season", "home_team_id", "home_team_abbr",
         "away_team_id", "away_team_abbr", "home_score", "away_score", "home_win"]
    ].drop_duplicates(subset=["game_id"])

    logger.info("Discovered %d unique games", len(result))
    return result


def collect_quarter_scores(games_df: pd.DataFrame) -> pd.DataFrame:
    """Add quarter-by-quarter scores to the games DataFrame."""
    if games_df.empty:
        return games_df

    unique_dates = sorted(games_df["game_date"].unique())
    logger.info("Collecting quarter scores for %d unique dates", len(unique_dates))

    all_line_scores = []
    for date_str in unique_dates:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted = dt.strftime("%m/%d/%Y")

        df = fetch_endpoint(
            scoreboardv2.ScoreboardV2,
            dataset_index=1,
            game_date=formatted,
        )
        if not df.empty:
            all_line_scores.append(df)

    if not all_line_scores:
        for col in ["home_q1", "home_q2", "home_q3", "home_q4",
                     "away_q1", "away_q2", "away_q3", "away_q4",
                     "home_ot", "away_ot", "num_ot"]:
            games_df[col] = None
        return games_df

    line_scores = pd.concat(all_line_scores, ignore_index=True)

    quarter_data = {}
    for _, row in line_scores.iterrows():
        key = (str(row.get("GAME_ID", "")), int(row.get("TEAM_ID", 0)))
        ot_cols = [c for c in line_scores.columns if c.startswith("PTS_OT")]
        ot_total = sum(row.get(c, 0) or 0 for c in ot_cols)
        num_ot = sum(1 for c in ot_cols if (row.get(c, 0) or 0) > 0)
        quarter_data[key] = {
            "q1": row.get("PTS_QTR1"),
            "q2": row.get("PTS_QTR2"),
            "q3": row.get("PTS_QTR3"),
            "q4": row.get("PTS_QTR4"),
            "ot": ot_total,
            "num_ot": num_ot,
        }

    def _map_quarters(row: pd.Series) -> pd.Series:
        home_key = (str(row["game_id"]), int(row["home_team_id"]))
        away_key = (str(row["game_id"]), int(row["away_team_id"]))
        home_q = quarter_data.get(home_key, {})
        away_q = quarter_data.get(away_key, {})
        return pd.Series({
            "home_q1": home_q.get("q1"),
            "home_q2": home_q.get("q2"),
            "home_q3": home_q.get("q3"),
            "home_q4": home_q.get("q4"),
            "away_q1": away_q.get("q1"),
            "away_q2": away_q.get("q2"),
            "away_q3": away_q.get("q3"),
            "away_q4": away_q.get("q4"),
            "home_ot": home_q.get("ot", 0),
            "away_ot": away_q.get("ot", 0),
            "num_ot": max(home_q.get("num_ot", 0), away_q.get("num_ot", 0)),
        })

    quarter_df = games_df.apply(_map_quarters, axis=1)
    result = pd.concat([games_df.reset_index(drop=True), quarter_df], axis=1)
    logger.info("Added quarter scores to %d games", len(result))
    return result
