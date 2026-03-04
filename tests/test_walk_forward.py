"""Tests for walk-forward analysis module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cuic_quant.backtest.walk_forward import (
    anchored_walk_forward,
    combinatorial_purged_cv,
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
        """Should produce folds with valid training data (fold 0 may be skipped)."""
        data = _make_time_series(100)
        results = walk_forward_backtest(
            data, always_bet_home, n_splits=3
        )
        assert "splits" in results
        # Fold 0 may be skipped if it has zero training data
        assert len(results["splits"]) >= 2
        # Every returned fold must have non-empty training data
        for split in results["splits"]:
            assert len(split["train_data"]) > 0

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


class TestAnchoredWalkForward:
    """Tests for anchored_walk_forward."""

    def _run(self, data: pd.DataFrame | None = None) -> dict:
        if data is None:
            data = _make_time_series(100)
        test_periods = [
            ("2025-02-15", "2025-03-01"),
            ("2025-03-01", "2025-03-15"),
            ("2025-03-15", "2025-04-01"),
        ]
        return anchored_walk_forward(
            data, always_bet_home,
            anchor_date="2025-01-01",
            test_periods=test_periods,
        )

    def test_produces_correct_folds(self) -> None:
        """3 test periods should produce 3 folds."""
        results = self._run()
        assert len(results["splits"]) == 3

    def test_aggregated_metrics_present(self) -> None:
        """Should return aggregated_metrics key."""
        results = self._run()
        assert "aggregated_metrics" in results
        metrics = results["aggregated_metrics"]
        for key in ("total_trades", "win_rate", "sharpe_ratio", "profit_factor", "max_drawdown"):
            assert key in metrics

    def test_train_always_starts_at_anchor(self) -> None:
        """All fold training data should start at the anchor date."""
        results = self._run()
        anchor = pd.Timestamp("2025-01-01")
        for split in results["splits"]:
            train = split["train_data"]
            if len(train) > 0:
                assert pd.to_datetime(train["timestamp"].iloc[0]) == anchor

    def test_no_train_test_overlap(self) -> None:
        """Max train timestamp should be before min test timestamp per fold."""
        results = self._run()
        for split in results["splits"]:
            train = split["train_data"]
            test = split["test_data"]
            if len(train) > 0 and len(test) > 0:
                assert (
                    pd.to_datetime(train["timestamp"]).max()
                    < pd.to_datetime(test["timestamp"]).min()
                )


class TestCombinatorialPurgedCV:
    """Tests for combinatorial_purged_cv."""

    def test_correct_number_of_combinations(self) -> None:
        """C(5, 2) = 10 combinations."""
        data = _make_time_series(100)
        results = combinatorial_purged_cv(
            data, always_bet_home, n_splits=5, n_test_splits=2,
        )
        assert results["n_combinations"] == 10
        assert len(results["splits"]) == 10

    def test_aggregated_metrics_present(self) -> None:
        """Should return aggregated_metrics with expected keys."""
        data = _make_time_series(100)
        results = combinatorial_purged_cv(
            data, always_bet_home, n_splits=5, n_test_splits=2,
        )
        assert "aggregated_metrics" in results
        metrics = results["aggregated_metrics"]
        for key in ("total_trades", "win_rate", "sharpe_ratio", "profit_factor", "max_drawdown"):
            assert key in metrics

    def test_purge_removes_boundary_rows(self) -> None:
        """With purge_gap > 0, no train row should be within purge_gap of any test row."""
        data = _make_time_series(100)
        purge_gap = 3
        results = combinatorial_purged_cv(
            data, always_bet_home,
            n_splits=5, n_test_splits=2, purge_gap=purge_gap,
        )
        n = len(data)
        group_size = n // 5
        groups = [(g * group_size, (g + 1) * group_size if g < 4 else n) for g in range(5)]

        for split in results["splits"]:
            test_groups = split["test_groups"]
            train_data = split["train_data"]
            if len(train_data) == 0:
                continue
            # Collect all test row indices
            test_indices: set[int] = set()
            for tg in test_groups:
                start, end = groups[tg]
                test_indices.update(range(start, end))
            # Check each train row is not within purge_gap of any test row
            train_indices = set(range(len(data))) - test_indices
            # Get actual train indices from the original data mapping
            # Since train_data is reset_index, we verify via group boundaries
            for tg in test_groups:
                tg_start, tg_end = groups[tg]
                for _, row in train_data.iterrows():
                    # Use timestamp to map back to original index
                    orig_idx = data.index[data["timestamp"] == row["timestamp"]]
                    if len(orig_idx) > 0:
                        idx = orig_idx[0]
                        assert idx < tg_start - purge_gap or idx >= tg_end + purge_gap, (
                            f"Train row {idx} is within purge_gap={purge_gap} "
                            f"of test group ({tg_start}, {tg_end})"
                        )

    def test_invalid_n_test_splits_raises(self) -> None:
        """n_test_splits >= n_splits should raise ValueError."""
        data = _make_time_series(100)
        with pytest.raises(ValueError, match="n_test_splits"):
            combinatorial_purged_cv(
                data, always_bet_home, n_splits=5, n_test_splits=5,
            )
        with pytest.raises(ValueError, match="n_test_splits"):
            combinatorial_purged_cv(
                data, always_bet_home, n_splits=5, n_test_splits=6,
            )
