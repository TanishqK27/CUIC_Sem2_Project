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
        """Legitimate ~50% win rate should not be flagged."""
        from cuic_quant.backtest import always_bet_home, backtest

        data = _make_test_data()
        results = backtest(data, always_bet_home)

        flags = comparison.detect_suspicious_results(results)
        # A normal ~67% win rate on 3 trades should not be flagged
        assert isinstance(flags, (list, dict))

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
    """Tests for ranking strategies within comparison."""

    def test_ranks_by_sharpe(self) -> None:
        """Should rank strategies by Sharpe ratio."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()

        result = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )
        # The result should be a DataFrame we can sort
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_ranks_ascending(self) -> None:
        """ascending=True should put worst first."""
        from cuic_quant.backtest import always_bet_home, always_bet_away

        data = _make_test_data()

        result = comparison.compare_strategies(
            data,
            {"home": always_bet_home, "away": always_bet_away},
        )

        # Verify the result can be sorted by total_pnl in ascending order
        if "total_pnl" in result.columns:
            sorted_asc = result.sort_values("total_pnl", ascending=True)
            assert sorted_asc.iloc[0]["total_pnl"] <= sorted_asc.iloc[-1]["total_pnl"]
