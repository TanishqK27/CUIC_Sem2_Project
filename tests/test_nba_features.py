"""Tests for NBA pre-game feature engineering pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cuic_quant.data.nba.features import (
    PreGameFeatureBuilder,
    _compute_streak,
    _parse_minutes,
    classify_comment,
)


# ---------------------------------------------------------------------------
# Fixtures: synthetic data
# ---------------------------------------------------------------------------

def _make_games(tmp_path: Path) -> pd.DataFrame:
    """Create a minimal games CSV with 5 games between 2 teams."""
    games = pd.DataFrame({
        "game_id": ["G001", "G002", "G003", "G004", "G005"],
        "game_date": [
            "2024-10-22", "2024-10-24", "2024-10-26", "2024-10-28", "2024-10-30",
        ],
        "season": ["2024-25"] * 5,
        "home_team_id": [1, 2, 1, 2, 1],
        "home_team_abbr": ["BOS", "LAL", "BOS", "LAL", "BOS"],
        "away_team_id": [2, 1, 2, 1, 2],
        "away_team_abbr": ["LAL", "BOS", "LAL", "BOS", "LAL"],
        "home_score": [110, 105, 98, 112, 100],
        "away_score": [100, 108, 102, 100, 95],
        "home_win": [1, 0, 0, 1, 1],
    })
    games.to_csv(tmp_path / "nba_games.csv", index=False)
    return games


def _make_player_boxscores(tmp_path: Path) -> pd.DataFrame:
    """Create minimal player boxscores for 3 players across 5 games.

    Player 101 (BOS) plays all 5 games.
    Player 102 (BOS) plays 4 games, DNP in G003.
    Player 201 (LAL) plays all 5 games.
    """
    rows = []
    # Player 101 - BOS - plays all 5
    for i, gid in enumerate(["G001", "G002", "G003", "G004", "G005"]):
        pts = [20, 25, 30, 15, 22][i]
        rows.append({
            "game_id": gid, "player_id": 101, "player_name": "Player A",
            "team_id": 1, "team_abbr": "BOS", "period": 0,
            "start_position": "F", "comment": "",
            "min": "30:00", "fgm": 8, "fga": 15, "fg_pct": 0.533,
            "fg3m": 2, "fg3a": 5, "fg3_pct": 0.4,
            "ftm": 2, "fta": 3, "ft_pct": 0.667,
            "oreb": 1, "dreb": 5, "reb": 6,
            "ast": 4, "stl": 1, "blk": 0, "tov": 2, "pf": 3,
            "pts": pts, "plus_minus": 5,
        })

    # Player 102 - BOS - DNP in G003
    for i, gid in enumerate(["G001", "G002", "G003", "G004", "G005"]):
        if gid == "G003":
            rows.append({
                "game_id": gid, "player_id": 102, "player_name": "Player B",
                "team_id": 1, "team_abbr": "BOS", "period": 0,
                "start_position": "", "comment": "DNP - INJURY/ILLNESS",
                "min": "", "fgm": 0, "fga": 0, "fg_pct": 0,
                "fg3m": 0, "fg3a": 0, "fg3_pct": 0,
                "ftm": 0, "fta": 0, "ft_pct": 0,
                "oreb": 0, "dreb": 0, "reb": 0,
                "ast": 0, "stl": 0, "blk": 0, "tov": 0, "pf": 0,
                "pts": 0, "plus_minus": 0,
            })
        else:
            pts = [10, 12, 0, 14, 8][i]
            rows.append({
                "game_id": gid, "player_id": 102, "player_name": "Player B",
                "team_id": 1, "team_abbr": "BOS", "period": 0,
                "start_position": "G", "comment": "",
                "min": "25:00", "fgm": 4, "fga": 10, "fg_pct": 0.4,
                "fg3m": 1, "fg3a": 3, "fg3_pct": 0.333,
                "ftm": 1, "fta": 2, "ft_pct": 0.5,
                "oreb": 0, "dreb": 3, "reb": 3,
                "ast": 6, "stl": 2, "blk": 0, "tov": 1, "pf": 2,
                "pts": pts, "plus_minus": 3,
            })

    # Player 201 - LAL - plays all 5
    for i, gid in enumerate(["G001", "G002", "G003", "G004", "G005"]):
        pts = [18, 22, 28, 16, 20][i]
        rows.append({
            "game_id": gid, "player_id": 201, "player_name": "Player C",
            "team_id": 2, "team_abbr": "LAL", "period": 0,
            "start_position": "C", "comment": "",
            "min": "32:00", "fgm": 7, "fga": 14, "fg_pct": 0.5,
            "fg3m": 1, "fg3a": 4, "fg3_pct": 0.25,
            "ftm": 3, "fta": 4, "ft_pct": 0.75,
            "oreb": 2, "dreb": 7, "reb": 9,
            "ast": 2, "stl": 0, "blk": 2, "tov": 3, "pf": 4,
            "pts": pts, "plus_minus": -3,
        })

    df = pd.DataFrame(rows)
    df.to_csv(tmp_path / "nba_game_boxscores_player.csv", index=False)
    return df


def _make_team_boxscores(tmp_path: Path) -> pd.DataFrame:
    """Create minimal team boxscores for 2 teams across 5 games."""
    rows = []
    for i, gid in enumerate(["G001", "G002", "G003", "G004", "G005"]):
        # Home team
        home_id = [1, 2, 1, 2, 1][i]
        home_abbr = ["BOS", "LAL", "BOS", "LAL", "BOS"][i]
        home_pts = [110, 105, 98, 112, 100][i]
        rows.append({
            "game_id": gid, "team_id": home_id, "team_abbr": home_abbr, "period": 0,
            "min": "240:00", "fgm": 40, "fga": 85, "fg_pct": 0.471,
            "fg3m": 10, "fg3a": 30, "fg3_pct": 0.333,
            "ftm": 20, "fta": 25, "ft_pct": 0.8,
            "oreb": 10, "dreb": 30, "reb": 40,
            "ast": 25, "stl": 8, "blk": 5, "tov": 12, "pf": 20,
            "pts": home_pts, "plus_minus": 0,
        })
        # Away team
        away_id = [2, 1, 2, 1, 2][i]
        away_abbr = ["LAL", "BOS", "LAL", "BOS", "LAL"][i]
        away_pts = [100, 108, 102, 100, 95][i]
        rows.append({
            "game_id": gid, "team_id": away_id, "team_abbr": away_abbr, "period": 0,
            "min": "240:00", "fgm": 38, "fga": 82, "fg_pct": 0.463,
            "fg3m": 9, "fg3a": 28, "fg3_pct": 0.321,
            "ftm": 15, "fta": 20, "ft_pct": 0.75,
            "oreb": 8, "dreb": 28, "reb": 36,
            "ast": 22, "stl": 6, "blk": 3, "tov": 14, "pf": 22,
            "pts": away_pts, "plus_minus": 0,
        })

    df = pd.DataFrame(rows)
    df.to_csv(tmp_path / "nba_game_boxscores_team.csv", index=False)
    return df


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Set up a temp data directory with synthetic NBA data."""
    _make_games(tmp_path)
    _make_player_boxscores(tmp_path)
    _make_team_boxscores(tmp_path)
    return tmp_path


@pytest.fixture
def builder(data_dir: Path) -> PreGameFeatureBuilder:
    return PreGameFeatureBuilder(data_dir)


# ---------------------------------------------------------------------------
# Unit tests: helper functions
# ---------------------------------------------------------------------------

class TestParseMinutes:
    def test_colon_format(self) -> None:
        assert _parse_minutes("37:58") == pytest.approx(37.967, abs=0.01)

    def test_pt_format(self) -> None:
        assert _parse_minutes("PT37M58S") == pytest.approx(37.967, abs=0.01)

    def test_empty(self) -> None:
        assert _parse_minutes("") == 0.0
        assert _parse_minutes(np.nan) == 0.0

    def test_plain_numeric(self) -> None:
        assert _parse_minutes("30") == 30.0
        assert _parse_minutes("0") == 0.0


class TestClassifyComment:
    def test_empty(self) -> None:
        assert classify_comment("") == ""
        assert classify_comment(np.nan) == ""

    def test_exact_match(self) -> None:
        assert classify_comment("DNP - INJURY/ILLNESS") == "injury"
        assert classify_comment("DND - REST") == "rest"
        assert classify_comment("DNP - COACH'S DECISION") == "coach_decision"
        assert classify_comment("DNP - SUSPENSION") == "suspension"
        assert classify_comment("DNP - TRADE PENDING") == "trade"
        assert classify_comment("DNP - PERSONAL REASONS") == "personal"

    def test_injury_keywords(self) -> None:
        assert classify_comment("Left Knee Soreness") == "injury"
        assert classify_comment("Right Ankle Sprain") == "injury"
        assert classify_comment("Hamstring Strain") == "injury"

    def test_rest(self) -> None:
        assert classify_comment("DND - REST") == "rest"
        assert classify_comment("Rest Day") == "rest"

    def test_other(self) -> None:
        assert classify_comment("Some unknown reason") == "other"


class TestComputeStreak:
    def test_basic_streak(self) -> None:
        won = pd.Series([1, 1, 0, 0, 1])
        result = _compute_streak(won)
        # Pre-game: [0, W1, W2, L1, L2]
        # game 0: streak entering = 0
        # game 1: after W -> streak entering = +1
        # game 2: after W,W -> streak entering = +2
        # game 3: after W,W,L -> streak entering = -1
        # game 4: after W,W,L,L -> streak entering = -2
        expected = [0, 1, 2, -1, -2]
        assert list(result) == expected

    def test_first_game_zero(self) -> None:
        won = pd.Series([0])
        assert list(_compute_streak(won)) == [0]

    def test_alternating(self) -> None:
        won = pd.Series([1, 0, 1, 0])
        result = _compute_streak(won)
        expected = [0, 1, -1, 1]
        assert list(result) == expected


# ---------------------------------------------------------------------------
# Integration tests: PreGameFeatureBuilder
# ---------------------------------------------------------------------------

class TestTeamFeatures:
    def test_row_count(self, builder: PreGameFeatureBuilder) -> None:
        """Should produce 2 rows per game (10 for 5 games)."""
        result = builder.run()
        assert result["pregame_team"] == 10

    def test_first_game_no_leakage(self, builder: PreGameFeatureBuilder) -> None:
        """First game of season should have all cumulative stats as 0/NaN."""
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))
        # BOS first game is G001
        bos_g1 = team_df[
            (team_df["game_id"] == "G001") & (team_df["team_id"] == 1)
        ]
        assert len(bos_g1) == 1
        row = bos_g1.iloc[0]
        assert row["season_gp"] == 0
        assert row["season_w"] == 0
        assert row["season_l"] == 0
        assert row["season_w_pct"] == 0.0
        assert row["streak"] == 0

    def test_cumulative_correctness(self, builder: PreGameFeatureBuilder) -> None:
        """Game N should reflect only games 1..N-1 stats."""
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))

        # BOS results: G001=W(home), G002=W(away), G003=L(home), G004=L(away), G005=W(home)
        # Before G003: BOS has 2W-0L
        bos_g3 = team_df[
            (team_df["game_id"] == "G003") & (team_df["team_id"] == 1)
        ].iloc[0]
        assert bos_g3["season_gp"] == 2
        assert bos_g3["season_w"] == 2
        assert bos_g3["season_l"] == 0
        assert bos_g3["season_w_pct"] == pytest.approx(1.0)

        # Before G005: BOS has 2W-2L
        bos_g5 = team_df[
            (team_df["game_id"] == "G005") & (team_df["team_id"] == 1)
        ].iloc[0]
        assert bos_g5["season_gp"] == 4
        assert bos_g5["season_w"] == 2
        assert bos_g5["season_l"] == 2
        assert bos_g5["season_w_pct"] == pytest.approx(0.5)

    def test_streak_values(self, builder: PreGameFeatureBuilder) -> None:
        """Verify streak computation across games."""
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))
        bos = team_df[team_df["team_id"] == 1].sort_values("game_date")
        streaks = list(bos["streak"])
        # BOS: W, W, L, L, W -> entering streaks: [0, 1, 2, -1, -2]
        assert streaks == [0, 1, 2, -1, -2]

    def test_days_rest(self, builder: PreGameFeatureBuilder) -> None:
        """Days rest should be the gap between consecutive games."""
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))
        bos = team_df[team_df["team_id"] == 1].sort_values("game_date")
        rest = list(bos["days_rest"])
        # Games: Oct 22, 24, 26, 28, 30 -> rest: NaN, 2, 2, 2, 2
        assert pd.isna(rest[0])
        assert rest[1:] == [2.0, 2.0, 2.0, 2.0]

    def test_home_away_record(self, builder: PreGameFeatureBuilder) -> None:
        """Home/away W-L should be tracked separately."""
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))
        # BOS before G005: home games G001(W), G003(L) -> home: 1W-1L
        #                   away games G002(W), G004(L) -> away: 1W-1L
        bos_g5 = team_df[
            (team_df["game_id"] == "G005") & (team_df["team_id"] == 1)
        ].iloc[0]
        assert bos_g5["home_w"] == 1
        assert bos_g5["home_l"] == 1
        assert bos_g5["away_w"] == 1
        assert bos_g5["away_l"] == 1


class TestPlayerFeatures:
    def test_produces_rows(self, builder: PreGameFeatureBuilder) -> None:
        """Should produce player feature rows for players who played."""
        result = builder.run()
        # 3 players across 5 games, but P102 DNP in G003 -> 14 played rows
        assert result["pregame_player"] == 14

    def test_first_game_no_leakage(self, builder: PreGameFeatureBuilder) -> None:
        """First game features should be NaN (no prior data)."""
        builder.run()
        player_df = pd.read_csv(builder._csv_path("pregame_player"))
        p101_g1 = player_df[
            (player_df["game_id"] == "G001") & (player_df["player_id"] == 101)
        ].iloc[0]
        assert p101_g1["season_gp"] == 0
        assert pd.isna(p101_g1["season_avg_pts"])

    def test_season_avg_correctness(self, builder: PreGameFeatureBuilder) -> None:
        """Season average for game N should be mean of games 1..N-1."""
        builder.run()
        player_df = pd.read_csv(builder._csv_path("pregame_player"))
        # P101 scores: G001=20, G002=25, G003=30
        # Before G003: avg_pts = (20+25)/2 = 22.5
        p101_g3 = player_df[
            (player_df["game_id"] == "G003") & (player_df["player_id"] == 101)
        ].iloc[0]
        assert p101_g3["season_avg_pts"] == pytest.approx(22.5)
        assert p101_g3["season_gp"] == 2


class TestAvailability:
    def test_produces_rows(self, builder: PreGameFeatureBuilder) -> None:
        """Should produce availability rows for all players in boxscores."""
        result = builder.run()
        # 3 players * 5 games = 15 rows
        assert result["pregame_availability"] == 15

    def test_played_flag(self, builder: PreGameFeatureBuilder) -> None:
        """played should be 1 for active players, 0 for DNP."""
        builder.run()
        avail_df = pd.read_csv(builder._csv_path("pregame_availability"))
        # P102 DNP in G003
        p102_g3 = avail_df[
            (avail_df["game_id"] == "G003") & (avail_df["player_id"] == 102)
        ].iloc[0]
        assert p102_g3["played"] == 0
        assert p102_g3["dnp_category"] == "injury"

        # P101 played in G003
        p101_g3 = avail_df[
            (avail_df["game_id"] == "G003") & (avail_df["player_id"] == 101)
        ].iloc[0]
        assert p101_g3["played"] == 1

    def test_comment_classification(self, builder: PreGameFeatureBuilder) -> None:
        """DNP comments should be correctly classified."""
        builder.run()
        avail_df = pd.read_csv(builder._csv_path("pregame_availability"))
        p102_g3 = avail_df[
            (avail_df["game_id"] == "G003") & (avail_df["player_id"] == 102)
        ].iloc[0]
        assert p102_g3["dnp_reason"] == "DNP - INJURY/ILLNESS"
        assert p102_g3["dnp_category"] == "injury"


class TestIdempotency:
    def test_double_run_same_result(self, builder: PreGameFeatureBuilder) -> None:
        """Running the pipeline twice should produce the same output."""
        result1 = builder.run()
        result2 = builder.run()
        assert result1 == result2

        # Check actual row counts match
        for name in ["pregame_team", "pregame_player", "pregame_availability"]:
            df = pd.read_csv(builder._csv_path(name))
            assert len(df) == result1[name]


class TestSeasonBoundary:
    def test_cross_season_isolation(self, tmp_path: Path) -> None:
        """Stats should not leak across season boundaries."""
        # Create games in two different seasons
        games = pd.DataFrame({
            "game_id": ["G001", "G002", "G003", "G004"],
            "game_date": ["2024-04-10", "2024-04-12", "2024-10-22", "2024-10-24"],
            "season": ["2023-24", "2023-24", "2024-25", "2024-25"],
            "home_team_id": [1, 2, 1, 2],
            "home_team_abbr": ["BOS", "LAL", "BOS", "LAL"],
            "away_team_id": [2, 1, 2, 1],
            "away_team_abbr": ["LAL", "BOS", "LAL", "BOS"],
            "home_score": [110, 105, 100, 108],
            "away_score": [100, 108, 95, 100],
            "home_win": [1, 0, 1, 1],
        })
        games.to_csv(tmp_path / "nba_games.csv", index=False)

        builder = PreGameFeatureBuilder(tmp_path)
        builder.run()
        team_df = pd.read_csv(builder._csv_path("pregame_team"))

        # First game of 2024-25 season (G003) should have season_gp=0
        bos_g3 = team_df[
            (team_df["game_id"] == "G003") & (team_df["team_id"] == 1)
        ].iloc[0]
        assert bos_g3["season_gp"] == 0
        assert bos_g3["season_w"] == 0
        assert bos_g3["streak"] == 0
