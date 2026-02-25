"""Tests for statistical significance and overfitting protection module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cuic_quant.backtest.statistics import (
    bonferroni_correction,
    bootstrap_confidence_interval,
    calculate_p_value,
    deflated_sharpe_ratio,
    holm_bonferroni_correction,
    minimum_sample_size,
    overfitting_report,
    probability_of_backtest_overfitting,
    significance_report,
)


class TestPValue:
    """Tests for calculate_p_value."""

    def test_50_percent_win_rate_not_significant(self) -> None:
        """50% win rate should have large p-value (not significant)."""
        p = calculate_p_value(win_rate=0.5, n_trades=100)
        assert p > 0.05

    def test_high_win_rate_large_sample_significant(self) -> None:
        """70% win rate with 100 trades should be significant."""
        p = calculate_p_value(win_rate=0.70, n_trades=100)
        assert p < 0.01

    def test_small_sample_not_significant(self) -> None:
        """Even high win rate with 5 trades shouldn't be p < 0.01."""
        p = calculate_p_value(win_rate=0.80, n_trades=5)
        assert p > 0.01

    def test_zero_trades(self) -> None:
        """Zero trades should return p=1.0."""
        assert calculate_p_value(0.5, 0) == 1.0


class TestBootstrapCI:
    """Tests for bootstrap_confidence_interval."""

    def test_ci_contains_true_mean(self) -> None:
        """95% CI should contain the true mean for normal data."""
        rng = np.random.default_rng(42)
        data = pd.Series(rng.normal(10.0, 1.0, size=200))
        lower, point, upper = bootstrap_confidence_interval(data, seed=42)
        assert lower < 10.0 < upper
        assert lower < point < upper

    def test_narrow_ci_with_large_sample(self) -> None:
        """CI should be narrower with more data."""
        rng = np.random.default_rng(42)
        small = pd.Series(rng.normal(0, 1, size=20))
        large = pd.Series(rng.normal(0, 1, size=2000))
        l_small, _, u_small = bootstrap_confidence_interval(small, seed=42)
        l_large, _, u_large = bootstrap_confidence_interval(large, seed=42)
        assert (u_large - l_large) < (u_small - l_small)

    def test_empty_series(self) -> None:
        """Empty series should return (0, 0, 0)."""
        assert bootstrap_confidence_interval(pd.Series(dtype=float)) == (0.0, 0.0, 0.0)


class TestMinimumSampleSize:
    """Tests for minimum_sample_size."""

    def test_55_percent_edge(self) -> None:
        """Detecting 55% vs 50% needs substantial sample."""
        n = minimum_sample_size(expected_edge=0.05, power=0.80, alpha=0.01)
        assert 500 < n < 5000

    def test_larger_edge_needs_fewer_samples(self) -> None:
        """10% edge should require fewer samples than 5% edge."""
        n_small = minimum_sample_size(expected_edge=0.05)
        n_large = minimum_sample_size(expected_edge=0.10)
        assert n_large < n_small

    def test_zero_edge(self) -> None:
        """Zero edge should return 0."""
        assert minimum_sample_size(expected_edge=0.0) == 0


class TestBonferroniCorrection:
    """Tests for bonferroni_correction."""

    def test_single_test_no_change(self) -> None:
        """With 1 test, Bonferroni threshold = alpha."""
        result = bonferroni_correction([0.03], alpha=0.05)
        assert result == [True]

    def test_multiple_tests_stricter(self) -> None:
        """With 55 tests, threshold = alpha/55."""
        p_values = [0.001] + [0.9] * 54
        result = bonferroni_correction(p_values, alpha=0.05)
        # 0.05/55 ≈ 0.00091, so 0.001 is NOT significant
        assert result[0] is False
        assert all(not r for r in result[1:])

    def test_marginal_p_values_rejected(self) -> None:
        """p=0.04 should be rejected with 2+ tests at alpha=0.05."""
        result = bonferroni_correction([0.04, 0.04], alpha=0.05)
        # 0.05/2 = 0.025, so 0.04 > 0.025 → not significant
        assert result == [False, False]

    def test_empty_list(self) -> None:
        assert bonferroni_correction([]) == []


class TestHolmBonferroni:
    """Tests for holm_bonferroni_correction."""

    def test_less_conservative_than_bonferroni(self) -> None:
        """Holm should be less conservative than Bonferroni."""
        p_values = [0.001, 0.02, 0.04]
        bonf = bonferroni_correction(p_values, alpha=0.05)
        holm = holm_bonferroni_correction(p_values, alpha=0.05)
        # Holm should accept at least as many as Bonferroni
        assert sum(holm) >= sum(bonf)


class TestDeflatedSharpe:
    """Tests for deflated_sharpe_ratio."""

    def test_single_trial_no_deflation(self) -> None:
        """With 1 trial, DSR p-value should be reasonable."""
        dsr = deflated_sharpe_ratio(
            observed_sharpe=2.0, n_trials=1, n_observations=252
        )
        assert 0 <= dsr <= 1

    def test_many_trials_inflates_pvalue(self) -> None:
        """With 55 trials, DSR p-value should be higher (less significant)."""
        dsr_1 = deflated_sharpe_ratio(
            observed_sharpe=1.5, n_trials=1, n_observations=252
        )
        dsr_55 = deflated_sharpe_ratio(
            observed_sharpe=1.5, n_trials=55, n_observations=252
        )
        assert dsr_55 > dsr_1


class TestPBO:
    """Tests for probability_of_backtest_overfitting."""

    def test_no_overfitting(self) -> None:
        """If IS best also has best OOS, PBO should be 0."""
        pbo = probability_of_backtest_overfitting(
            [1.0, 0.5, 0.3], [2.0, 0.4, 0.2]
        )
        assert pbo == 0.0

    def test_complete_overfitting(self) -> None:
        """If IS best has worst OOS, PBO should be high."""
        pbo = probability_of_backtest_overfitting(
            [2.0, 0.5, 0.3], [0.1, 1.0, 0.8]
        )
        assert pbo > 0.5


class TestSignificanceReport:
    """Tests for significance_report."""

    def test_report_structure(self) -> None:
        """Report should have required keys."""
        data = pd.DataFrame({
            "outcome": ["WIN", "LOSS"] * 50,
            "pnl": [100.0, -100.0] * 50,
            "bet_size": [100.0] * 100,
            "cumulative_pnl": list(range(100)),
            "bankroll": [10000 + i for i in range(100)],
        })
        report = significance_report(data)
        assert "p_value" in report
        assert "is_significant" in report
        assert "warnings" in report

    def test_small_sample_warning(self) -> None:
        """Should warn when sample size is too small."""
        data = pd.DataFrame({
            "outcome": ["WIN", "LOSS"] * 5,
            "pnl": [100.0, -100.0] * 5,
            "cumulative_pnl": list(range(10)),
            "bankroll": [10000 + i for i in range(10)],
        })
        report = significance_report(data)
        assert len(report["warnings"]) > 0

    def test_empty_results(self) -> None:
        """Empty results should not crash."""
        data = pd.DataFrame(columns=["outcome", "pnl", "cumulative_pnl", "bankroll"])
        report = significance_report(data)
        assert report["is_significant"] is False


class TestOverfittingReport:
    """Tests for overfitting_report."""

    def test_report_with_multiple_strategies(self) -> None:
        """Should produce report for multiple strategy results."""
        strategies = [
            {"name": f"strat_{i}", "sharpe": 1.0 + i * 0.1, "p_value": 0.05 - i * 0.01, "n_trades": 100}
            for i in range(5)
        ]
        report = overfitting_report(strategies, alpha=0.05)
        assert report["n_strategies"] == 5
        assert "bonferroni_significant" in report
        assert "holm_significant" in report
        assert len(report["deflated_sharpe_pvalues"]) == 5

    def test_empty_strategies(self) -> None:
        """Empty list should not crash."""
        report = overfitting_report([])
        assert report["n_strategies"] == 0
