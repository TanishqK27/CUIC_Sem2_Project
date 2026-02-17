"""Pre-game feature engineering pipeline.

Transforms raw NBA game/boxscore/roster data into pre-game feature sets
with strict no-leakage guarantees: every feature for game N uses only
data from games 1..N-1 within the same season.

Outputs three CSVs:
  - pregame_team.csv   (PK: game_id, team_id)
  - pregame_player.csv (PK: game_id, player_id)
  - pregame_availability.csv (PK: game_id, player_id)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from cuic_quant.data.nba.constants import CSV_CONFIG
from cuic_quant.data.nba.csv_writer import load_csv, save_csv

logger = logging.getLogger(__name__)

# Conference mapping: team_abbr -> conference
TEAM_CONFERENCE: dict[str, str] = {
    "ATL": "East", "BOS": "East", "BKN": "East", "CHA": "East",
    "CHI": "East", "CLE": "East", "DET": "East", "IND": "East",
    "MIA": "East", "MIL": "East", "NYK": "East", "ORL": "East",
    "PHI": "East", "TOR": "East", "WAS": "East",
    "DAL": "West", "DEN": "West", "GSW": "West", "HOU": "West",
    "LAC": "West", "LAL": "West", "MEM": "West", "MIN": "West",
    "NOP": "West", "OKC": "West", "PHX": "West", "POR": "West",
    "SAC": "West", "SAS": "West", "UTA": "West",
}

# Map DNP comments to categories
COMMENT_CATEGORY: dict[str, str] = {
    "DND": "rest",
    "DNP": "coach_decision",
    "NWT": "coach_decision",
    "NOT WITH TEAM": "coach_decision",
    "DND - REST": "rest",
    "DNP - REST": "rest",
    "DNP - COACH'S DECISION": "coach_decision",
    "DND - COACH'S DECISION": "coach_decision",
    "DNP - INJURY/ILLNESS": "injury",
    "DND - INJURY/ILLNESS": "injury",
    "DNP - PERSONAL REASONS": "personal",
    "DND - PERSONAL REASONS": "personal",
    "DNP - SUSPENSION": "suspension",
    "DND - SUSPENSION": "suspension",
    "DNP - TRADE PENDING": "trade",
    "DND - TRADE PENDING": "trade",
    "DNP - NOT WITH TEAM": "coach_decision",
    "DND - NOT WITH TEAM": "coach_decision",
}


def classify_comment(comment: str | float) -> str:
    """Classify a boxscore comment into a DNP category.

    Args:
        comment: Raw comment string from boxscore data.

    Returns:
        One of: injury, rest, coach_decision, suspension, trade, personal, other.
    """
    if pd.isna(comment) or str(comment).strip() == "":
        return ""
    comment_upper = str(comment).strip().upper()
    # Direct match
    if comment_upper in COMMENT_CATEGORY:
        return COMMENT_CATEGORY[comment_upper]
    # Substring matching for longer comments
    if any(kw in comment_upper for kw in ("INJURY", "ILLNESS", "SORE", "SPRAIN",
                                           "STRAIN", "FRACTURE", "CONCUSSION",
                                           "SURGERY", "REHAB", "RECOVERY",
                                           "KNEE", "ANKLE", "HAMSTRING", "BACK",
                                           "SHOULDER", "WRIST", "FOOT", "HIP",
                                           "CALF", "GROIN", "QUAD", "THUMB",
                                           "ELBOW", "FINGER", "TOE", "NECK",
                                           "ACHILLES", "ACL", "TORN")):
        return "injury"
    if "REST" in comment_upper:
        return "rest"
    if "SUSPENSION" in comment_upper or "SUSPENDED" in comment_upper:
        return "suspension"
    if "TRADE" in comment_upper or "WAIV" in comment_upper:
        return "trade"
    if "PERSONAL" in comment_upper or "FAMILY" in comment_upper:
        return "personal"
    if any(kw in comment_upper for kw in ("COACH", "DNP", "DND", "NWT")):
        return "coach_decision"
    return "other"


def _parse_minutes(min_str: str | float) -> float:
    """Parse minutes string like '37:58' or 'PT37M58S' to float minutes.

    Args:
        min_str: Minutes string from boxscore.

    Returns:
        Float minutes (e.g. 37.97). Returns 0.0 for invalid/empty.
    """
    if pd.isna(min_str) or str(min_str).strip() == "":
        return 0.0
    s = str(min_str).strip()
    # "MM:SS" format
    if ":" in s:
        parts = s.split(":")
        try:
            return int(parts[0]) + int(parts[1]) / 60
        except (ValueError, IndexError):
            return 0.0
    # "PTxxMxxS" ISO duration format
    if s.startswith("PT"):
        try:
            s = s[2:]
            mins = 0.0
            if "M" in s:
                m_part, s = s.split("M")
                mins += float(m_part)
            if "S" in s:
                s_part = s.replace("S", "")
                if s_part:
                    mins += float(s_part) / 60
            return mins
        except (ValueError, IndexError):
            return 0.0
    # Plain numeric
    try:
        return float(s)
    except ValueError:
        return 0.0


def _compute_streak(won_series: pd.Series) -> pd.Series:
    """Compute win/loss streak entering each game (pre-game, so shifted).

    Streak is a signed int: +3 = won last 3, -2 = lost last 2.
    First game of season = 0.

    Args:
        won_series: Boolean/int series of game outcomes (1=win, 0=loss).

    Returns:
        Series of streak values, shifted so game N gets streak after N-1.
    """
    streaks = []
    current = 0
    for w in won_series:
        streaks.append(current)
        if w == 1:
            current = current + 1 if current > 0 else 1
        else:
            current = current - 1 if current < 0 else -1
    return pd.Series(streaks, index=won_series.index)


class PreGameFeatureBuilder:
    """Builds pre-game feature CSVs from raw NBA data.

    Args:
        data_dir: Directory containing raw NBA CSVs and where
            output feature CSVs will be written.
    """

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)

    def _csv_path(self, name: str) -> Path:
        return self.data_dir / CSV_CONFIG[name]["file"]

    def _pk(self, name: str) -> list[str]:
        return CSV_CONFIG[name]["pk"]

    def _save(self, name: str, df: pd.DataFrame) -> None:
        if df.empty:
            return
        save_csv(df, self._csv_path(name), self._pk(name))

    def _load(self, name: str) -> pd.DataFrame:
        return load_csv(self._csv_path(name))

    def run(self) -> dict[str, int]:
        """Run full pre-game feature pipeline.

        Returns:
            Dict mapping output name to row count.
        """
        result: dict[str, int] = {}

        # Load games
        games = self._load("nba_games")
        if games.empty:
            logger.warning("No games data found. Skipping feature engineering.")
            return result

        games["game_date"] = pd.to_datetime(games["game_date"])
        games = games.sort_values("game_date").reset_index(drop=True)

        # Build team game log (unpivot: 2 rows per game)
        team_game_log = self._build_team_game_log(games)

        # Team features
        team_features = self._build_team_features(team_game_log, games)
        self._save("pregame_team", team_features)
        result["pregame_team"] = len(team_features)
        logger.info("pregame_team: %d rows", len(team_features))

        # Player features + availability (require boxscores)
        player_box = self._load("nba_game_boxscores_player")
        if not player_box.empty:
            player_features = self._build_player_features(games, player_box)
            self._save("pregame_player", player_features)
            result["pregame_player"] = len(player_features)
            logger.info("pregame_player: %d rows", len(player_features))

            availability = self._build_availability(games, player_box)
            self._save("pregame_availability", availability)
            result["pregame_availability"] = len(availability)
            logger.info("pregame_availability: %d rows", len(availability))
        else:
            logger.warning("No boxscore data found. Skipping player features.")

        return result

    @staticmethod
    def _build_team_game_log(games: pd.DataFrame) -> pd.DataFrame:
        """Unpivot games into per-team rows.

        Each game produces 2 rows (home team + away team) with columns:
        game_id, game_date, season, team_id, team_abbr, is_home,
        pts_for, pts_against, won, opp_team_id, opp_team_abbr.
        """
        home = games[["game_id", "game_date", "season",
                       "home_team_id", "home_team_abbr",
                       "home_score", "away_score", "home_win",
                       "away_team_id", "away_team_abbr"]].copy()
        home = home.rename(columns={
            "home_team_id": "team_id",
            "home_team_abbr": "team_abbr",
            "home_score": "pts_for",
            "away_score": "pts_against",
            "home_win": "won",
            "away_team_id": "opp_team_id",
            "away_team_abbr": "opp_team_abbr",
        })
        home["is_home"] = 1

        away = games[["game_id", "game_date", "season",
                       "away_team_id", "away_team_abbr",
                       "away_score", "home_score", "home_win",
                       "home_team_id", "home_team_abbr"]].copy()
        away = away.rename(columns={
            "away_team_id": "team_id",
            "away_team_abbr": "team_abbr",
            "away_score": "pts_for",
            "home_score": "pts_against",
            "home_team_id": "opp_team_id",
            "home_team_abbr": "opp_team_abbr",
        })
        away["won"] = (1 - games["home_win"]).astype(int)
        away["is_home"] = 0

        log = pd.concat([home, away], ignore_index=True)
        log = log.sort_values(["game_date", "game_id"]).reset_index(drop=True)
        return log

    def _build_team_features(
        self,
        team_game_log: pd.DataFrame,
        games: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build pre-game team features using only prior-game data.

        Features: record, home/away record, last5/last10 record, streak,
        days rest, rolling stats, conference rank.
        """
        tgl = team_game_log.copy()
        tgl = tgl.sort_values(["season", "team_id", "game_date"]).reset_index(drop=True)
        grp = tgl.groupby(["season", "team_id"], sort=False)

        # --- Record features (cumulative, shifted) ---
        tgl["season_gp"] = grp.cumcount()  # 0-indexed = games played before this game
        tgl["season_w"] = grp["won"].cumsum().shift(1).fillna(0).astype(int)
        # For first game, cumcount=0 so season_gp is already correct
        # But we need to recalculate: games played before = cumcount value
        # wins before = cumsum shifted by 1
        tgl["season_w"] = grp["won"].transform(
            lambda x: x.cumsum().shift(1).fillna(0)
        ).astype(int)
        tgl["season_l"] = tgl["season_gp"] - tgl["season_w"]
        tgl["season_w_pct"] = np.where(
            tgl["season_gp"] > 0,
            tgl["season_w"] / tgl["season_gp"],
            0.0,
        )

        # Home record (use intermediate columns to avoid grp.apply FutureWarning)
        tgl["_home_win"] = tgl["won"] * tgl["is_home"]
        tgl["home_w"] = grp["_home_win"].transform(
            lambda x: x.cumsum().shift(1).fillna(0)
        ).astype(int)
        tgl["home_gp"] = grp["is_home"].transform(
            lambda x: x.cumsum().shift(1).fillna(0)
        ).astype(int)
        tgl["home_l"] = tgl["home_gp"] - tgl["home_w"]

        # Away record
        tgl["_is_away"] = 1 - tgl["is_home"]
        tgl["_away_win"] = tgl["won"] * tgl["_is_away"]
        tgl["away_w"] = grp["_away_win"].transform(
            lambda x: x.cumsum().shift(1).fillna(0)
        ).astype(int)
        tgl["away_gp"] = grp["_is_away"].transform(
            lambda x: x.cumsum().shift(1).fillna(0)
        ).astype(int)
        tgl["away_l"] = tgl["away_gp"] - tgl["away_w"]
        tgl = tgl.drop(columns=["_home_win", "_is_away", "_away_win"])

        # Last 5 / Last 10 W-L (rolling, shifted)
        tgl["last5_w"] = grp["won"].transform(
            lambda x: x.rolling(5, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        tgl["last5_gp"] = grp["won"].transform(
            lambda x: x.rolling(5, min_periods=1).count().shift(1).fillna(0)
        ).astype(int)
        tgl["last5_l"] = tgl["last5_gp"] - tgl["last5_w"]

        tgl["last10_w"] = grp["won"].transform(
            lambda x: x.rolling(10, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        tgl["last10_gp"] = grp["won"].transform(
            lambda x: x.rolling(10, min_periods=1).count().shift(1).fillna(0)
        ).astype(int)
        tgl["last10_l"] = tgl["last10_gp"] - tgl["last10_w"]

        # Streak
        tgl["streak"] = grp["won"].transform(_compute_streak).astype(int)

        # Days rest
        tgl["days_rest"] = grp["game_date"].transform(
            lambda x: x.diff().dt.days
        )
        # First game of season has NaN days_rest - leave as NaN

        # --- Rolling box score stats ---
        # Join team boxscores (period=0 for full game)
        team_box = self._load("nba_game_boxscores_team")
        if not team_box.empty:
            team_box_full = team_box[team_box["period"] == 0].copy()
            # Ensure type alignment for merge
            team_box_full["game_id"] = team_box_full["game_id"].astype(str)
            team_box_full["team_id"] = team_box_full["team_id"].astype(str)
            tgl["game_id"] = tgl["game_id"].astype(str)
            tgl["team_id"] = tgl["team_id"].astype(str)

            box_cols = ["game_id", "team_id", "fg_pct", "fg3_pct",
                        "reb", "ast", "tov", "stl", "blk", "pts"]
            available_cols = [c for c in box_cols if c in team_box_full.columns]
            tgl = tgl.merge(
                team_box_full[available_cols],
                on=["game_id", "team_id"],
                how="left",
                suffixes=("", "_box"),
            )

            # Rename pts from boxscore to avoid conflict (we already have pts_for)
            if "pts" in tgl.columns and "pts_for" in tgl.columns:
                tgl = tgl.drop(columns=["pts"], errors="ignore")

            # Rolling averages for box score stats
            stat_cols = [c for c in ["fg_pct", "fg3_pct", "reb", "ast",
                                      "tov", "stl", "blk"] if c in tgl.columns]
            grp2 = tgl.groupby(["season", "team_id"], sort=False)
            for col in stat_cols:
                tgl[f"season_avg_{col}"] = grp2[col].transform(
                    lambda x: x.expanding().mean().shift(1)
                )
                tgl[f"last5_avg_{col}"] = grp2[col].transform(
                    lambda x: x.rolling(5, min_periods=1).mean().shift(1)
                )

        # PPG / PAPG (points per game / points against per game)
        grp3 = tgl.groupby(["season", "team_id"], sort=False)
        tgl["season_ppg"] = grp3["pts_for"].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        tgl["season_papg"] = grp3["pts_against"].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        tgl["last5_ppg"] = grp3["pts_for"].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        )
        tgl["last5_papg"] = grp3["pts_against"].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        )

        # Off/Def/Net rating (simple version: pts_for/pts_against based)
        tgl["season_off_rtg"] = tgl["season_ppg"]
        tgl["season_def_rtg"] = tgl["season_papg"]
        tgl["season_net_rtg"] = tgl["season_ppg"] - tgl["season_papg"]

        # Conference rank based on cumulative win_pct per game date
        tgl["conference"] = tgl["team_abbr"].map(TEAM_CONFERENCE)
        # Rank within conference by season_w_pct (descending), break ties by wins
        tgl["conf_rank"] = tgl.groupby(
            ["season", "game_date", "conference"], sort=False
        )["season_w_pct"].rank(method="min", ascending=False).fillna(0).astype(int)

        # Select output columns
        output_cols = [
            "game_id", "game_date", "season", "team_id", "team_abbr", "is_home",
            "season_gp", "season_w", "season_l", "season_w_pct",
            "home_w", "home_l", "away_w", "away_l",
            "last5_w", "last5_l", "last10_w", "last10_l",
            "streak", "days_rest",
            "season_ppg", "season_papg",
            "last5_ppg", "last5_papg",
            "season_off_rtg", "season_def_rtg", "season_net_rtg",
            "conference", "conf_rank",
        ]
        # Add rolling box stat columns if available
        for col in ["fg_pct", "fg3_pct", "reb", "ast", "tov", "stl", "blk"]:
            if f"season_avg_{col}" in tgl.columns:
                output_cols.append(f"season_avg_{col}")
            if f"last5_avg_{col}" in tgl.columns:
                output_cols.append(f"last5_avg_{col}")

        existing_cols = [c for c in output_cols if c in tgl.columns]
        return tgl[existing_cols].reset_index(drop=True)

    def _build_player_features(
        self,
        games: pd.DataFrame,
        player_box: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build pre-game player features from boxscore data.

        Features: games played, season & last5 averages for traditional
        and advanced stats.
        """
        # Use period=0 (full game) boxscores only
        box = player_box[player_box["period"] == 0].copy()
        box["game_id"] = box["game_id"].astype(str)

        # Merge with games for date and season
        games_slim = games[["game_id", "game_date", "season"]].copy()
        games_slim["game_id"] = games_slim["game_id"].astype(str)
        box = box.merge(games_slim, on="game_id", how="left")
        box = box.sort_values(["season", "player_id", "game_date"]).reset_index(drop=True)

        # Parse minutes
        if "min" in box.columns:
            box["minutes"] = box["min"].apply(_parse_minutes)
        else:
            box["minutes"] = 0.0

        # Determine who actually played (has minutes > 0 and no DNP comment)
        box["played"] = (box["minutes"] > 0).astype(int)

        # Filter to played-only for rolling averages
        played = box[box["played"] == 1].copy()
        if played.empty:
            return pd.DataFrame()

        played = played.sort_values(
            ["season", "player_id", "game_date"]
        ).reset_index(drop=True)

        grp = played.groupby(["season", "player_id"], sort=False)

        # Games played before this game
        played["season_gp"] = grp.cumcount()

        # Traditional stats rolling averages
        trad_stats = [c for c in ["pts", "reb", "ast", "stl", "blk", "tov",
                                   "fg_pct", "fg3_pct", "ft_pct"]
                      if c in played.columns]
        for col in trad_stats:
            played[f"season_avg_{col}"] = grp[col].transform(
                lambda x: x.expanding().mean().shift(1)
            )
            played[f"last5_avg_{col}"] = grp[col].transform(
                lambda x: x.rolling(5, min_periods=1).mean().shift(1)
            )

        # Minutes average
        played["season_avg_min"] = grp["minutes"].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        played["last5_avg_min"] = grp["minutes"].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        )

        # Advanced stats (merge if available)
        adv_box = self._load("nba_game_advanced_player")
        if not adv_box.empty:
            adv_full = adv_box[adv_box["period"] == 0].copy()
            adv_full["game_id"] = adv_full["game_id"].astype(str)
            adv_cols_wanted = ["game_id", "player_id", "usg_pct", "ts_pct",
                               "efg_pct", "pace", "pie"]
            adv_available = [c for c in adv_cols_wanted if c in adv_full.columns]
            if len(adv_available) > 2:  # at least game_id + player_id + 1 stat
                played["player_id"] = played["player_id"].astype(str)
                adv_full["player_id"] = adv_full["player_id"].astype(str)
                played = played.merge(
                    adv_full[adv_available],
                    on=["game_id", "player_id"],
                    how="left",
                )
                adv_stat_cols = [c for c in ["usg_pct", "ts_pct", "efg_pct",
                                              "pace", "pie"]
                                 if c in played.columns]
                grp2 = played.groupby(["season", "player_id"], sort=False)
                for col in adv_stat_cols:
                    played[f"season_avg_{col}"] = grp2[col].transform(
                        lambda x: x.expanding().mean().shift(1)
                    )
                    played[f"last5_avg_{col}"] = grp2[col].transform(
                        lambda x: x.rolling(5, min_periods=1).mean().shift(1)
                    )

        # Games missed in last 10 roster appearances
        # Use the full box (including DNP) to count appearances
        box_sorted = box.sort_values(
            ["season", "player_id", "game_date"]
        ).reset_index(drop=True)
        box_grp = box_sorted.groupby(["season", "player_id"], sort=False)
        box_sorted["last10_missed"] = box_grp["played"].transform(
            lambda x: (1 - x).rolling(10, min_periods=1).sum().shift(1)
        )
        # Merge last10_missed back into played
        miss_map = box_sorted[["game_id", "player_id", "last10_missed"]].copy()
        miss_map["game_id"] = miss_map["game_id"].astype(str)
        miss_map["player_id"] = miss_map["player_id"].astype(str)
        played["game_id"] = played["game_id"].astype(str)
        played["player_id"] = played["player_id"].astype(str)
        if "last10_missed" in played.columns:
            played = played.drop(columns=["last10_missed"])
        played = played.merge(
            miss_map, on=["game_id", "player_id"], how="left",
        )

        # Select output columns
        output_cols = [
            "game_id", "game_date", "season", "player_id", "player_name",
            "team_id", "team_abbr", "season_gp",
            "season_avg_min", "last5_avg_min",
        ]
        for col in trad_stats:
            output_cols.extend([f"season_avg_{col}", f"last5_avg_{col}"])
        for col in ["usg_pct", "ts_pct", "efg_pct", "pace", "pie"]:
            if f"season_avg_{col}" in played.columns:
                output_cols.extend([f"season_avg_{col}", f"last5_avg_{col}"])
        output_cols.append("last10_missed")

        existing_cols = [c for c in output_cols if c in played.columns]
        return played[existing_cols].reset_index(drop=True)

    def _build_availability(
        self,
        games: pd.DataFrame,
        player_box: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build per-player availability status for each game.

        Includes played flag, raw DNP comment, and classified category.
        """
        # Use period=0 (full game) boxscores
        box = player_box[player_box["period"] == 0].copy()
        box["game_id"] = box["game_id"].astype(str)

        # Merge with games for date/season
        games_slim = games[["game_id", "game_date", "season"]].copy()
        games_slim["game_id"] = games_slim["game_id"].astype(str)
        box = box.merge(games_slim, on="game_id", how="left")

        # Parse minutes
        if "min" in box.columns:
            box["minutes"] = box["min"].apply(_parse_minutes)
        else:
            box["minutes"] = 0.0

        # Determine played status
        box["played"] = (box["minutes"] > 0).astype(int)

        # DNP reason and category
        comment_col = "comment" if "comment" in box.columns else None
        if comment_col:
            box["dnp_reason"] = box[comment_col].where(box["played"] == 0, "")
            box["dnp_category"] = box[comment_col].apply(
                lambda c: classify_comment(c) if pd.notna(c) else ""
            )
            # Clear category for players who played
            box.loc[box["played"] == 1, "dnp_category"] = ""
        else:
            box["dnp_reason"] = ""
            box["dnp_category"] = ""

        output_cols = [
            "game_id", "game_date", "season", "player_id", "player_name",
            "team_id", "team_abbr", "played", "dnp_reason", "dnp_category",
        ]
        existing_cols = [c for c in output_cols if c in box.columns]
        return box[existing_cols].reset_index(drop=True)
