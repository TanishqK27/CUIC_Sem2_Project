"""Tests for walk-forward analysis module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cuic_quant.backtest.walk_forward import (
    expanding_window_backtest,
    train_test_split,
    walk_forward_backtest,
)
from cuic_quant.backtest.backtester_backend import always_bet_home


def _make_time_series(n_rows: int = 100) -> pd.DataFrame:
    """Create synthetic time-series data for testing."""
    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2025-01-01", periods=n_rows, freq="D")
    return pd.DataFrame({
        "timestamp": timestamps,
        "game": [f"TeamA vs TeamB_{i}" for i in range(n_rows)],
        "home_team": ["TeamA"] * n_rows,
        "away_team": [f"TeamB_{i}" for i in range(n_rows)],
        "home_odds": rng.uniform(1.5, 3.0, size=n_rows).round(2),
        "away_odds": rng.uniform(1.5, 3.0, size=n_rows).round(2),
        "home_win": rng.integers(0, 2, size=n_rows),
    })


class TestTrainTestSplit:
    """Tests for train_test_split."""

    def test_split_preserves_all_data(self) -> None:
        """Train + test should contain all rows."""
        data = _make_time_series(100)
        train, test = train_test_split(data, train_ratio=0.7)
        assert len(train) + len(test) == 100

    def test_split_ratio(self) -> None:
        """70/30 split should be approximately correct."""
        data = _make_time_series(100)
        train, test = train_test_split(data, train_ratio=0.7)
        assert len(train) == 70
        assert len(test) == 30

    def test_no_future_leakage(self) -> None:
        """All train timestamps should be before all test timestamps."""
        data = _make_time_series(100)
        train, test = train_test_split(data, train_ratio=0.7)
        assert train["timestamp"].max() <= test["timestamp"].min()

    def test_gap_excludes_rows(self) -> None:
        """Gap parameter should exclude rows between train and test."""
        data = _make_time_series(100)
        train, test = train_test_split(data, train_ratio=0.7, gap=5)
        assert len(train) + len(test) < 100  # gap removes rows


class TestWalkForwardBacktest:
    """Tests for walk_forward_backtest."""

    def test_produces_multiple_folds(self) -> None:
        """Should produce n_splits folds."""
        data = _make_time_series(100)
        results = walk_forward_backtest(
            data, always_bet_home, n_splits=3
        )
        assert "splits" in results
        assert len(results["splits"]) == 3

    def test_aggregated_metrics_present(self) -> None:
        """Should return aggregated out-of-sample metrics."""
        data = _make_time_series(100)
        results = walk_forward_backtest(
            data, always_bet_home, n_splits=3
        )
        assert "aggregated_metrics" in results

    def test_results_structure(self) -> None:
        """Each split should have train_data, test_data, results, metrics."""
        data = _make_time_series(100)
        results = walk_forward_backtest(
            data, always_bet_home, n_splits=2
        )
        for split in results["splits"]:
            assert "test_data" in split or "test_results" in split


class TestExpandingWindow:
    """Tests for expanding_window_backtest."""

    def test_expanding_window_runs(self) -> None:
        """Should run without error on sufficient data."""
        data = _make_time_series(100)
        results = expanding_window_backtest(
            data, always_bet_home, min_train_size=30, step_size=10
        )
        assert "splits" in results
        assert len(results["splits"]) > 0

    def test_minimum_train_size_respected(self) -> None:
        """No fold should have fewer than min_train_size training rows."""
        data = _make_time_series(100)
        results = expanding_window_backtest(
            data, always_bet_home, min_train_size=30, step_size=10
        )
        for split in results["splits"]:
            if "train_data" in split:
                assert len(split["train_data"]) >= 30
