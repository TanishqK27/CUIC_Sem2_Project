"""Fetch real NBA game results from the NBA API and save as nba_games.csv.

Pulls regular season games for 2021-22 through 2024-25, builds per-game
home/away rows, and writes to data/nba_collection/nba_games.csv in the
format expected by the backtest data loader.

Usage:
    python scripts/fetch_nba_games.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder

SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25"]
OUT_PATH = Path("data/nba_collection/nba_games.csv")
DELAY = 1.5  # seconds between API calls to avoid rate limiting


def fetch_season(season: str) -> pd.DataFrame:
    print(f"  Fetching {season}...", end=" ", flush=True)
    df = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable="00",
        season_type_nullable="Regular Season",
    ).get_data_frames()[0]
    print(f"{len(df)} rows")
    return df


def build_games(raw: pd.DataFrame) -> pd.DataFrame:
    """Pivot per-team rows into per-game home/away rows."""
    home = raw[raw["MATCHUP"].str.contains("vs.", na=False)].copy()
    away = raw[raw["MATCHUP"].str.contains("@", na=False)].copy()

    home = home.rename(columns={
        "TEAM_ID": "home_team_id",
        "TEAM_ABBREVIATION": "home_team_abbr",
        "PTS": "home_score",
        "FGM": "home_fgm", "FGA": "home_fga", "FG_PCT": "home_fg_pct",
        "FG3M": "home_fg3m", "FG3A": "home_fg3a", "FG3_PCT": "home_fg3_pct",
        "FTM": "home_ftm", "FTA": "home_fta", "FT_PCT": "home_ft_pct",
        "OREB": "home_oreb", "DREB": "home_dreb", "REB": "home_reb",
        "AST": "home_ast", "STL": "home_stl", "BLK": "home_blk",
        "TOV": "home_tov", "PF": "home_pf", "PLUS_MINUS": "home_plus_minus",
    })
    away = away.rename(columns={
        "TEAM_ID": "away_team_id",
        "TEAM_ABBREVIATION": "away_team_abbr",
        "PTS": "away_score",
        "FGM": "away_fgm", "FGA": "away_fga", "FG_PCT": "away_fg_pct",
        "FG3M": "away_fg3m", "FG3A": "away_fg3a", "FG3_PCT": "away_fg3_pct",
        "FTM": "away_ftm", "FTA": "away_fta", "FT_PCT": "away_ft_pct",
        "OREB": "away_oreb", "DREB": "away_dreb", "REB": "away_reb",
        "AST": "away_ast", "STL": "away_stl", "BLK": "away_blk",
        "TOV": "away_tov", "PF": "away_pf", "PLUS_MINUS": "away_plus_minus",
    })

    away_cols = [
        "GAME_ID", "away_team_id", "away_team_abbr", "away_score",
        "away_fgm", "away_fga", "away_fg_pct", "away_fg3m", "away_fg3a",
        "away_fg3_pct", "away_ftm", "away_fta", "away_ft_pct",
        "away_oreb", "away_dreb", "away_reb", "away_ast", "away_stl",
        "away_blk", "away_tov", "away_pf", "away_plus_minus",
    ]

    merged = home.merge(away[away_cols], on="GAME_ID", how="inner")

    merged["home_win"] = (merged["home_score"] > merged["away_score"]).astype(int)
    merged["game_date"] = pd.to_datetime(merged["GAME_DATE"]).dt.strftime("%Y-%m-%d")

    keep = [
        "GAME_ID", "game_date", "SEASON_ID",
        "home_team_id", "home_team_abbr", "away_team_id", "away_team_abbr",
        "home_score", "away_score", "home_win",
        "home_fgm", "home_fga", "home_fg_pct",
        "home_fg3m", "home_fg3a", "home_fg3_pct",
        "home_ftm", "home_fta", "home_ft_pct",
        "home_oreb", "home_dreb", "home_reb",
        "home_ast", "home_stl", "home_blk", "home_tov", "home_pf",
        "away_fgm", "away_fga", "away_fg_pct",
        "away_fg3m", "away_fg3a", "away_fg3_pct",
        "away_ftm", "away_fta", "away_ft_pct",
        "away_oreb", "away_dreb", "away_reb",
        "away_ast", "away_stl", "away_blk", "away_tov", "away_pf",
    ]
    result = merged[keep].rename(columns={"GAME_ID": "game_id", "SEASON_ID": "season_id"})
    return result.drop_duplicates(subset=["game_id"]).sort_values("game_date")


def main() -> None:
    print(f"Fetching NBA regular season games for: {SEASONS}")
    all_frames: list[pd.DataFrame] = []

    for i, season in enumerate(SEASONS):
        df = fetch_season(season)
        all_frames.append(df)
        if i < len(SEASONS) - 1:
            time.sleep(DELAY)

    raw = pd.concat(all_frames, ignore_index=True)
    print(f"\nTotal raw rows: {len(raw):,}")

    games = build_games(raw)
    print(f"Unique games:   {len(games):,}")
    print(f"Home win rate:  {games['home_win'].mean():.1%}")
    print(f"Date range:     {games['game_date'].min()} → {games['game_date'].max()}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    games.to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
