"""Tests for strategy comparison and anomaly detection module."""
from __future__ import annotations

import pytest
import pandas as pd

# Try to import - skip if not available
comparison = pytest.importorskip("cuic_quant.backtest.comparison")


def _make_test_data() -> pd.DataFrame:
    """Create a small test DataFrame for backtest input."""
    return pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        "game": ["A vs B", "C vs D", "E vs F"],
        "home_team": ["A", "C", "E"],
        "away_team": ["B", "D", "F"],
        "home_odds": [2.00, 1.80, 2.20],
        "away_odds": [2.00, 2.20, 1.80],
        "home_win": [1, 0, 1],
    })


class TestCompareStrategies:
    """Tests for compare_strategies function."""

    def test_compares_two_strategies(self) -> None:
        """Should produce comparison DataFrame with 2 rows."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()

        result = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )
        assert len(result) == 2
        assert "strategy_name" in result.columns or result.index.name == "strategy_name"

    def test_includes_key_metrics(self) -> None:
        """Comparison should include win_rate, total_pnl, sharpe_ratio."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()

        result = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )
        # Check that key metrics are present as columns
        columns = result.columns.tolist()
        for metric in ["win_rate", "total_pnl"]:
            assert metric in columns, f"Missing metric column: {metric}"

    def test_handles_strategy_that_skips_all(self) -> None:
        """Strategy that skips everything should still appear in comparison."""
        from cuic_quant.backtest import always_bet_home

        def skip_all(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "SKIP", "confidence": 0, "size": 0}

        data = _make_test_data()

        result = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "skip": skip_all},
        )
        assert len(result) == 2


class TestDetectSuspiciousResults:
    """Tests for detect_suspicious_results function."""

    def test_normal_results_not_suspicious(self) -> None:
        """Legitimate ~50% win rate should not be flagged as suspicious."""
        from cuic_quant.backtest import always_bet_home, backtest

        data = _make_test_data()
        results = backtest(data, always_bet_home)

        flags = comparison.detect_suspicious_results(results)
        # Must actually check the is_suspicious field
        if isinstance(flags, dict):
            assert flags.get("is_suspicious") is False, (
                f"Normal results should not be suspicious, got: {flags}"
            )
        elif isinstance(flags, list):
            assert len(flags) == 0, (
                f"Normal results should have no flags, got: {flags}"
            )

    def test_100_percent_win_rate_flagged(self) -> None:
        """100% win rate should be flagged as suspicious."""
        from cuic_quant.backtest import always_bet_home, backtest

        # All home wins so always_bet_home gets 100% win rate
        data = pd.DataFrame({
            "timestamp": pd.to_datetime([
                "2026-01-01", "2026-01-02", "2026-01-03",
                "2026-01-04", "2026-01-05", "2026-01-06",
                "2026-01-07", "2026-01-08", "2026-01-09",
                "2026-01-10",
            ]),
            "game": [f"G{i}" for i in range(10)],
            "home_team": [f"H{i}" for i in range(10)],
            "away_team": [f"A{i}" for i in range(10)],
            "home_odds": [2.00] * 10,
            "away_odds": [2.00] * 10,
            "home_win": [1] * 10,  # all home wins
        })

        results = backtest(data, always_bet_home)
        flags = comparison.detect_suspicious_results(results)

        # Should flag the perfect win rate
        if isinstance(flags, list):
            assert len(flags) > 0, "100% win rate on 10 trades should be flagged"
        elif isinstance(flags, dict):
            assert any(flags.values()), "100% win rate on 10 trades should be flagged"

    def test_cheating_strategy_detected(self) -> None:
        """Strategy using data leakage should be detected."""
        from cuic_quant.backtest import backtest

        # A "cheating" strategy that somehow always wins -- simulate by
        # feeding data where every game is a home win and betting home
        def always_home(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.99, "size": 100.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime([f"2026-01-{i+1:02d}" for i in range(20)]),
            "game": [f"G{i}" for i in range(20)],
            "home_team": [f"H{i}" for i in range(20)],
            "away_team": [f"A{i}" for i in range(20)],
            "home_odds": [2.50] * 20,
            "away_odds": [1.60] * 20,
            "home_win": [1] * 20,
        })

        results = backtest(data, always_home)
        flags = comparison.detect_suspicious_results(results)

        if isinstance(flags, list):
            assert len(flags) > 0, "20/20 wins at 2.50 odds should be flagged"
        elif isinstance(flags, dict):
            assert any(flags.values()), "20/20 wins at 2.50 odds should be flagged"


class TestRankStrategies:
    """Tests for rank_strategies() function."""

    def _get_comparison_df(self) -> pd.DataFrame:
        """Helper: build a comparison DataFrame for ranking tests."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()
        return comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )

    def test_rank_strategies_adds_rank_column(self) -> None:
        """rank_strategies() should add a 'rank' column."""
        comp = self._get_comparison_df()
        ranked = comparison.rank_strategies(comp)
        assert "rank" in ranked.columns
        assert list(ranked["rank"]) == [1, 2]

    def test_rank_strategies_sorts_descending_by_default(self) -> None:
        """Default sort is descending (highest metric first)."""
        comp = self._get_comparison_df()
        ranked = comparison.rank_strategies(comp, metric="total_pnl")
        pnl_values = ranked["total_pnl"].tolist()
        assert pnl_values[0] >= pnl_values[-1]

    def test_rank_strategies_ascending(self) -> None:
        """ascending=True should put lowest value first."""
        comp = self._get_comparison_df()
        ranked = comparison.rank_strategies(comp, metric="total_pnl", ascending=True)
        pnl_values = ranked["total_pnl"].tolist()
        assert pnl_values[0] <= pnl_values[-1]
        assert ranked["rank"].iloc[0] == 1

    def test_rank_strategies_invalid_metric_raises(self) -> None:
        """Ranking by a nonexistent metric should raise ValueError."""
        comp = self._get_comparison_df()
        with pytest.raises(ValueError, match="not found"):
            comparison.rank_strategies(comp, metric="nonexistent_metric")


class TestDisplayComparison:
    """Tests for display_comparison() function."""

    def test_display_comparison_prints_output(self, capsys: pytest.CaptureFixture) -> None:
        """display_comparison() should print a formatted table."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()
        comp = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )
        comparison.display_comparison(comp)
        captured = capsys.readouterr()
        assert "STRATEGY COMPARISON" in captured.out
        assert "Best by metric:" in captured.out

    def test_display_comparison_empty_df(self, capsys: pytest.CaptureFixture) -> None:
        """display_comparison() with empty DataFrame should print message."""
        empty_df = pd.DataFrame()
        comparison.display_comparison(empty_df)
        captured = capsys.readouterr()
        assert "No strategies to compare" in captured.out

    def test_display_comparison_single_strategy(self, capsys: pytest.CaptureFixture) -> None:
        """display_comparison() with one strategy should skip 'Best by metric'."""
        from cuic_quant.backtest import always_bet_home

        data = _make_test_data()
        comp = comparison.compare_strategies(data, {"home": always_bet_home})
        comparison.display_comparison(comp)
        captured = capsys.readouterr()
        assert "STRATEGY COMPARISON" in captured.out
        # With only 1 strategy, "Best by metric" is skipped (needs len > 1)
        assert "Best by metric:" not in captured.out
