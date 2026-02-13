"""Tests for backtester backend module."""

from __future__ import annotations

import pandas as pd
import pytest


class TestAlwaysBetHome:
    """Tests for the always_bet_home example strategy."""

    def test_returns_buy_home_action(self) -> None:
        """Should always return BUY_HOME action."""
        from cuic_quant.backtest.backtester_backend import always_bet_home

        row = pd.Series({
            "timestamp": pd.Timestamp("2026-01-01"),
            "game": "Lakers vs Celtics",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_odds": 1.95,
            "away_odds": 2.05,
        })

        signal = always_bet_home(row)
        assert signal["action"] == "BUY_HOME"
        assert signal["size"] == 100.0
        assert signal["confidence"] == 0.5

    def test_accepts_context(self) -> None:
        """Should accept optional context dict without error."""
        from cuic_quant.backtest.backtester_backend import always_bet_home

        row = pd.Series({"home_odds": 1.95, "away_odds": 2.05})
        context = {"bankroll": 5000.0, "trade_count": 3}
        signal = always_bet_home(row, context)
        assert signal["action"] == "BUY_HOME"


class TestLoadBacktestData:
    """Tests for load_backtest_data function."""

    def test_loads_dummy_csv(self) -> None:
        """Should load dummy_backtest_input.csv and return correct columns."""
        from cuic_quant.backtest.backtester_backend import load_backtest_data, DUMMY_CSV

        df = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        expected_cols = [
            "timestamp", "game", "home_team", "away_team",
            "home_odds", "away_odds", "home_win",
        ]
        assert df.columns.tolist() == expected_cols
        assert len(df) == 25

    def test_filters_by_date_range(self) -> None:
        """Should only return rows within the date range."""
        from cuic_quant.backtest.backtester_backend import load_backtest_data, DUMMY_CSV

        df = load_backtest_data("2026-01-10", "2026-01-15", csv_path=DUMMY_CSV)
        assert len(df) > 0
        assert len(df) < 25
        assert df["timestamp"].min() >= pd.Timestamp("2026-01-10")
        assert df["timestamp"].max() <= pd.Timestamp("2026-01-15")

    def test_sorted_by_timestamp(self) -> None:
        """Should return data sorted by timestamp ascending."""
        from cuic_quant.backtest.backtester_backend import load_backtest_data, DUMMY_CSV

        df = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        assert df["timestamp"].is_monotonic_increasing

    def test_missing_csv_raises_error(self) -> None:
        """Should raise FileNotFoundError for non-existent CSV."""
        from cuic_quant.backtest.backtester_backend import load_backtest_data

        with pytest.raises(FileNotFoundError):
            load_backtest_data("2026-01-01", "2026-01-31", csv_path="/fake/path.csv")

    def test_loads_test_games_csv(self) -> None:
        """Should load Mya's test_games.csv (100 rows)."""
        from cuic_quant.backtest.backtester_backend import load_backtest_data, TEST_CSV

        if not TEST_CSV.exists():
            pytest.skip("test_games.csv not present")

        df = load_backtest_data("2026-01-01", "2026-12-31", csv_path=TEST_CSV)
        assert len(df) == 100
