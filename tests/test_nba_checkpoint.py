"""Tests for NBA collection checkpoint/resume logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from cuic_quant.data.nba.checkpoint import Checkpoint


@pytest.fixture
def checkpoint_path(tmp_path: Path) -> Path:
    return tmp_path / ".nba_checkpoint.json"


class TestCheckpoint:
    """Tests for checkpoint save/load/update."""

    def test_fresh_checkpoint_has_defaults(self, checkpoint_path: Path) -> None:
        cp = Checkpoint(checkpoint_path)
        assert cp.last_update is None
        assert cp.seasons_completed == []
        assert cp.games_collected == {}
        assert cp.total_api_calls == 0

    def test_save_and_load_roundtrip(self, checkpoint_path: Path) -> None:
        cp = Checkpoint(checkpoint_path)
        cp.last_update = "2026-02-10"
        cp.mark_season_completed("2021-22")
        cp.mark_game_collected("boxscores", "0022100001")
        cp.total_api_calls = 100
        cp.save()

        cp2 = Checkpoint(checkpoint_path)
        assert cp2.last_update == "2026-02-10"
        assert "2021-22" in cp2.seasons_completed
        assert "0022100001" in cp2.games_collected["boxscores"]
        assert cp2.total_api_calls == 100

    def test_is_game_collected(self, checkpoint_path: Path) -> None:
        cp = Checkpoint(checkpoint_path)
        cp.mark_game_collected("boxscores", "0022100001")
        assert cp.is_game_collected("boxscores", "0022100001") is True
        assert cp.is_game_collected("boxscores", "0022100002") is False
        assert cp.is_game_collected("hustle", "0022100001") is False

    def test_is_season_completed(self, checkpoint_path: Path) -> None:
        cp = Checkpoint(checkpoint_path)
        cp.mark_season_completed("2021-22")
        assert cp.is_season_completed("2021-22") is True
        assert cp.is_season_completed("2022-23") is False

    def test_increment_api_calls(self, checkpoint_path: Path) -> None:
        cp = Checkpoint(checkpoint_path)
        cp.increment_api_calls(5)
        cp.increment_api_calls(3)
        assert cp.total_api_calls == 8
