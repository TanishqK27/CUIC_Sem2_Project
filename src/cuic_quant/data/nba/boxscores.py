"""Box score collectors: traditional, advanced, hustle, and player tracking."""

from __future__ import annotations

import logging

import pandas as pd
from nba_api.stats.endpoints import (
    boxscoreadvancedv2,
    boxscoreplayertrackv3,
    boxscoretraditionalv2,
    hustlestatsboxscore,
)

from cuic_quant.data.nba.api_helper import fetch_endpoint
from cuic_quant.data.nba.constants import standardize_team_abbr

logger = logging.getLogger(__name__)


def _standardize_abbr_col(df: pd.DataFrame, col: str = "TEAM_ABBREVIATION") -> pd.DataFrame:
    """Apply team abbreviation standardization to a column."""
    if col in df.columns:
        df["team_abbr"] = df[col].apply(
            lambda x: standardize_team_abbr(x) if pd.notna(x) else x
        )
    return df


def collect_traditional_boxscore(
    game_id: str,
    periods: list[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Collect traditional box score for a game, optionally per period."""
    if periods is None:
        periods = [0, 1, 2, 3, 4]

    player_frames = []
    team_frames = []

    for period in periods:
        kwargs = {"game_id": game_id}
        if period > 0:
            kwargs["start_period"] = period
            kwargs["end_period"] = period
            kwargs["range_type"] = 1
        else:
            kwargs["start_period"] = 0
            kwargs["end_period"] = 0

        player_df = fetch_endpoint(boxscoretraditionalv2.BoxScoreTraditionalV2, dataset_index=0, **kwargs)
        team_df = fetch_endpoint(boxscoretraditionalv2.BoxScoreTraditionalV2, dataset_index=1, **kwargs)

        if not player_df.empty:
            player_df["period"] = period
            player_frames.append(player_df)
        if not team_df.empty:
            team_df["period"] = period
            team_frames.append(team_df)

    player_result = _format_traditional_player(pd.concat(player_frames, ignore_index=True)) if player_frames else pd.DataFrame()
    team_result = _format_traditional_team(pd.concat(team_frames, ignore_index=True)) if team_frames else pd.DataFrame()

    return player_result, team_result


def _format_traditional_player(df: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_abbr_col(df)
    col_map = {
        "GAME_ID": "game_id", "PLAYER_ID": "player_id", "PLAYER_NAME": "player_name",
        "TEAM_ID": "team_id", "START_POSITION": "start_position", "COMMENT": "comment",
        "MIN": "min", "FGM": "fgm", "FGA": "fga", "FG_PCT": "fg_pct",
        "FG3M": "fg3m", "FG3A": "fg3a", "FG3_PCT": "fg3_pct",
        "FTM": "ftm", "FTA": "fta", "FT_PCT": "ft_pct",
        "OREB": "oreb", "DREB": "dreb", "REB": "reb",
        "AST": "ast", "STL": "stl", "BLK": "blk", "TO": "tov", "PF": "pf",
        "PTS": "pts", "PLUS_MINUS": "plus_minus",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    final = ["game_id", "player_id", "player_name", "team_id", "team_abbr", "period",
             "start_position", "comment", "min", "fgm", "fga", "fg_pct",
             "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct",
             "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "pts", "plus_minus"]
    return df[[c for c in final if c in df.columns]]


def _format_traditional_team(df: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_abbr_col(df)
    col_map = {
        "GAME_ID": "game_id", "TEAM_ID": "team_id", "TEAM_NAME": "team_name",
        "MIN": "min", "FGM": "fgm", "FGA": "fga", "FG_PCT": "fg_pct",
        "FG3M": "fg3m", "FG3A": "fg3a", "FG3_PCT": "fg3_pct",
        "FTM": "ftm", "FTA": "fta", "FT_PCT": "ft_pct",
        "OREB": "oreb", "DREB": "dreb", "REB": "reb",
        "AST": "ast", "STL": "stl", "BLK": "blk", "TO": "tov", "PF": "pf",
        "PTS": "pts", "PLUS_MINUS": "plus_minus",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    final = ["game_id", "team_id", "team_abbr", "period",
             "min", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
             "ftm", "fta", "ft_pct", "oreb", "dreb", "reb",
             "ast", "stl", "blk", "tov", "pf", "pts", "plus_minus"]
    return df[[c for c in final if c in df.columns]]


def collect_advanced_boxscore(
    game_id: str,
    periods: list[int] | None = None,
) -> pd.DataFrame:
    """Collect advanced box score for a game, optionally per period."""
    if periods is None:
        periods = [0, 1, 2, 3, 4]

    frames = []
    for period in periods:
        kwargs = {"game_id": game_id}
        if period > 0:
            kwargs["start_period"] = period
            kwargs["end_period"] = period
            kwargs["range_type"] = 1
        else:
            kwargs["start_period"] = 0
            kwargs["end_period"] = 0

        df = fetch_endpoint(boxscoreadvancedv2.BoxScoreAdvancedV2, dataset_index=0, **kwargs)
        if not df.empty:
            df["period"] = period
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return _format_advanced_player(combined)


def _format_advanced_player(df: pd.DataFrame) -> pd.DataFrame:
    df = _standardize_abbr_col(df)
    col_map = {
        "GAME_ID": "game_id", "PLAYER_ID": "player_id", "PLAYER_NAME": "player_name",
        "TEAM_ID": "team_id", "MIN": "min",
        "OFF_RATING": "off_rating", "DEF_RATING": "def_rating", "NET_RATING": "net_rating",
        "AST_PCT": "ast_pct", "AST_TOV": "ast_tov", "AST_RATIO": "ast_ratio",
        "OREB_PCT": "oreb_pct", "DREB_PCT": "dreb_pct", "REB_PCT": "reb_pct",
        "TM_TOV_PCT": "tov_pct", "EFG_PCT": "efg_pct", "TS_PCT": "ts_pct",
        "USG_PCT": "usg_pct", "PACE": "pace", "POSS": "poss", "PIE": "pie",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    final = ["game_id", "player_id", "player_name", "team_id", "team_abbr", "period",
             "min", "off_rating", "def_rating", "net_rating",
             "ast_pct", "ast_tov", "ast_ratio", "oreb_pct", "dreb_pct", "reb_pct",
             "tov_pct", "efg_pct", "ts_pct", "usg_pct", "pace", "poss", "pie"]
    return df[[c for c in final if c in df.columns]]


def collect_hustle_boxscore(game_id: str) -> pd.DataFrame:
    """Collect hustle stats for a game (full game only)."""
    df = fetch_endpoint(
        hustlestatsboxscore.HustleStatsBoxScore,
        dataset_index=1,
        game_id=game_id,
    )
    if df.empty:
        return df

    df = _standardize_abbr_col(df)
    col_map = {
        "GAME_ID": "game_id", "PLAYER_ID": "player_id", "PLAYER_NAME": "player_name",
        "TEAM_ID": "team_id", "MIN": "min",
        "CONTESTED_SHOTS": "contested_shots",
        "CONTESTED_SHOTS_2PT": "contested_shots_2pt",
        "CONTESTED_SHOTS_3PT": "contested_shots_3pt",
        "DEFLECTIONS": "deflections", "CHARGES_DRAWN": "charges_drawn",
        "SCREEN_ASSISTS": "screen_assists", "SCREEN_AST_PTS": "screen_ast_pts",
        "OFF_LOOSE_BALLS_RECOVERED": "off_loose_balls_recovered",
        "DEF_LOOSE_BALLS_RECOVERED": "def_loose_balls_recovered",
        "LOOSE_BALLS_RECOVERED": "loose_balls_recovered",
        "OFF_BOXOUTS": "off_boxouts", "DEF_BOXOUTS": "def_boxouts",
        "BOX_OUTS": "box_outs",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    final = ["game_id", "player_id", "player_name", "team_id", "team_abbr", "min",
             "contested_shots", "contested_shots_2pt", "contested_shots_3pt",
             "deflections", "charges_drawn", "screen_assists", "screen_ast_pts",
             "off_loose_balls_recovered", "def_loose_balls_recovered", "loose_balls_recovered",
             "off_boxouts", "def_boxouts", "box_outs"]
    return df[[c for c in final if c in df.columns]]


def collect_tracking_boxscore(game_id: str) -> pd.DataFrame:
    """Collect player tracking stats for a game (speed, distance, touches)."""
    df = fetch_endpoint(
        boxscoreplayertrackv3.BoxScorePlayerTrackV3,
        dataset_index=0,
        game_id=game_id,
    )
    if df.empty:
        return df

    df = _standardize_abbr_col(df)
    col_map = {
        "GAME_ID": "game_id", "PLAYER_ID": "player_id", "PLAYER_NAME": "player_name",
        "TEAM_ID": "team_id", "MIN": "min",
        "SPD": "speed", "DIST": "distance",
        "ORBC": "oreb_chances", "DRBC": "dreb_chances", "RBC": "reb_chances",
        "TCHS": "touches", "SAST": "secondary_ast", "FTAST": "ft_ast",
        "PASS": "passes", "AST": "ast",
        "CFGM": "contested_fgm", "CFGA": "contested_fga", "CFG_PCT": "contested_fg_pct",
        "UFGM": "uncontested_fgm", "UFGA": "uncontested_fga", "UFG_PCT": "uncontested_fg_pct",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    final = ["game_id", "player_id", "player_name", "team_id", "team_abbr", "min",
             "speed", "distance", "oreb_chances", "dreb_chances", "reb_chances",
             "touches", "secondary_ast", "ft_ast", "passes", "ast",
             "contested_fgm", "contested_fga", "contested_fg_pct",
             "uncontested_fgm", "uncontested_fga", "uncontested_fg_pct"]
    return df[[c for c in final if c in df.columns]]
