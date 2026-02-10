"""Tests for NBA CSV writer with deduplication."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from cuic_quant.data.nba.csv_writer import save_csv, load_csv


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    return tmp_path / "test.csv"


class TestCsvWriter:
    """Tests for CSV save/load with deduplication."""

    def test_save_new_file(self, csv_path: Path) -> None:
        df = pd.DataFrame({"game_id": ["001", "002"], "pts": [100, 110]})
        save_csv(df, csv_path, primary_keys=["game_id"])
        assert csv_path.exists()
        result = pd.read_csv(csv_path)
        assert len(result) == 2

    def test_append_deduplicates(self, csv_path: Path) -> None:
        df1 = pd.DataFrame({"game_id": ["001", "002"], "pts": [100, 110]})
        save_csv(df1, csv_path, primary_keys=["game_id"])

        df2 = pd.DataFrame({"game_id": ["002", "003"], "pts": [115, 120]})
        save_csv(df2, csv_path, primary_keys=["game_id"])

        result = pd.read_csv(csv_path, dtype=str)
        assert len(result) == 3
        # "002" should have the newer value (115)
        row = result[result["game_id"] == "002"].iloc[0]
        assert int(row["pts"]) == 115

    def test_composite_primary_key(self, csv_path: Path) -> None:
        df1 = pd.DataFrame({
            "game_id": ["001", "001"],
            "player_id": [10, 20],
            "pts": [30, 25],
        })
        save_csv(df1, csv_path, primary_keys=["game_id", "player_id"])

        df2 = pd.DataFrame({
            "game_id": ["001"],
            "player_id": [10],
            "pts": [35],
        })
        save_csv(df2, csv_path, primary_keys=["game_id", "player_id"])

        result = pd.read_csv(csv_path, dtype=str)
        assert len(result) == 2
        row = result[(result["game_id"] == "001") & (result["player_id"] == "10")].iloc[0]
        assert int(row["pts"]) == 35

    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        result = load_csv(tmp_path / "nope.csv")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
