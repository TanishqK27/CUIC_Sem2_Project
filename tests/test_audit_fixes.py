"""Tests for all audit-found bugs — engine edge cases, metrics known values,
walk-forward fixes, validator fixes, and data leakage prevention.

Created during the Feb 2026 comprehensive audit to fill coverage gaps.
"""
from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
import pandas as pd
import pytest

from cuic_quant.backtest.backtester_backend import (
    OUTPUT_COLUMNS,
    backtest,
    always_bet_home,
    validate_backtest_results,
)


# ============================================================================
# Helpers
# ============================================================================


def _make_input(
    n: int = 5,
    home_wins: list[int] | None = None,
    odds: float = 2.00,
) -> pd.DataFrame:
    if home_wins is None:
        home_wins = [1, 0] * ((n // 2) + 1)
    home_wins = home_wins[:n]
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="D"),
        "game": [f"T{i}A vs T{i}B" for i in range(n)],
        "home_team": [f"T{i}A" for i in range(n)],
        "away_team": [f"T{i}B" for i in range(n)],
        "home_odds": [odds] * n,
        "away_odds": [odds] * n,
        "home_win": home_wins,
    })


# ============================================================================
# ENGINE CRASH VECTORS (Agent 2)
# ============================================================================


class TestEngineCrashVectors:
    """Verify engine doesn't crash on bad strategy return types."""

    def test_strategy_returns_none(self) -> None:
        """Strategy returning None should skip row, not crash."""
        def none_strategy(row, ctx=None):
            return None

        data = _make_input(n=2, home_wins=[1, 1])
        results = backtest(data, none_strategy)
        assert len(results) == 0

    def test_strategy_returns_string(self) -> None:
        """Strategy returning a string should skip row, not crash."""
        def str_strategy(row, ctx=None):
            return "BUY_HOME"

        data = _make_input(n=2, home_wins=[1, 1])
        results = backtest(data, str_strategy)
        assert len(results) == 0

    def test_strategy_returns_list(self) -> None:
        """Strategy returning a list should skip row, not crash."""
        def list_strategy(row, ctx=None):
            return ["BUY_HOME", 100.0]

        data = _make_input(n=2, home_wins=[1, 1])
        results = backtest(data, list_strategy)
        assert len(results) == 0

    def test_strategy_returns_int(self) -> None:
        """Strategy returning an int should skip row, not crash."""
        def int_strategy(row, ctx=None):
            return 42

        data = _make_input(n=2, home_wins=[1, 1])
        results = backtest(data, int_strategy)
        assert len(results) == 0


class TestEngineInputValidation:
    """Verify engine validates parameters upfront."""

    def test_nan_bankroll_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="initial_bankroll"):
            backtest(data, always_bet_home, initial_bankroll=float("nan"))

    def test_nan_cost_pct_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="cost_pct"):
            backtest(data, always_bet_home, cost_pct=float("nan"))

    def test_nan_cost_flat_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="cost_flat"):
            backtest(data, always_bet_home, cost_flat=float("nan"))

    def test_cost_pct_5_raises(self) -> None:
        """cost_pct=5 is almost certainly a user mistake (should be 0.05)."""
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="cost_pct"):
            backtest(data, always_bet_home, cost_pct=5.0)

    def test_negative_cost_pct_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="cost_pct"):
            backtest(data, always_bet_home, cost_pct=-0.01)

    def test_negative_cost_flat_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="cost_flat"):
            backtest(data, always_bet_home, cost_flat=-10.0)

    def test_position_sizing_case_insensitive(self) -> None:
        """position_sizing='Kelly' (capital K) should work, not silently fail."""
        data = _make_input(n=3, home_wins=[1, 0, 1])

        def conf_strategy(row, ctx=None):
            return {"action": "BUY_HOME", "confidence": 0.6, "size": 100}

        results_lower = backtest(data, conf_strategy, position_sizing="kelly")
        results_upper = backtest(data, conf_strategy, position_sizing="Kelly")
        # Both should produce the same results (Kelly sizing)
        assert len(results_lower) == len(results_upper)
        if len(results_lower) > 0:
            assert results_lower["bet_size"].iloc[0] == results_upper["bet_size"].iloc[0]

    def test_invalid_position_sizing_warns(self) -> None:
        """Unrecognized position_sizing should warn, not silently ignore."""
        data = _make_input(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            backtest(data, always_bet_home, position_sizing="fibonacci")
        assert any("Unrecognized" in str(w.message) for w in caught)

    def test_kelly_fraction_zero_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="kelly_fraction"):
            backtest(data, always_bet_home, position_sizing="kelly", kelly_fraction=0.0)

    def test_kelly_fraction_negative_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="kelly_fraction"):
            backtest(data, always_bet_home, position_sizing="kelly", kelly_fraction=-0.5)

    def test_kelly_fraction_above_1_raises(self) -> None:
        data = _make_input(n=1, home_wins=[1])
        with pytest.raises(ValueError, match="kelly_fraction"):
            backtest(data, always_bet_home, position_sizing="kelly", kelly_fraction=2.0)


class TestNaNHomeWinHandling:
    """NaN in home_win should be skipped, not treated as LOSS."""

    def test_nan_home_win_skipped(self) -> None:
        data = _make_input(n=3, home_wins=[1, 1, 1])
        data.loc[1, "home_win"] = float("nan")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home)

        # Row 1 has NaN home_win, should be skipped -> 2 trades
        assert len(results) == 2
        # Should have warned
        assert any("NaN home_win" in str(w.message) for w in caught)

    def test_non_binary_home_win_skipped(self) -> None:
        data = _make_input(n=3, home_wins=[1, 1, 1])
        data.loc[1, "home_win"] = 2  # invalid

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home)

        assert len(results) == 2
        assert any("not 0 or 1" in str(w.message) for w in caught)

    def test_string_home_win_skipped(self) -> None:
        data = _make_input(n=2, home_wins=[1, 1])
        data["home_win"] = data["home_win"].astype(object)
        data.loc[0, "home_win"] = "yes"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home)

        assert len(results) == 1  # only row 1 should produce a trade


class TestStringOddsHandling:
    """String-typed odds should not crash the engine."""

    def test_string_odds_skipped(self) -> None:
        data = _make_input(n=2, home_wins=[1, 1])
        data["home_odds"] = data["home_odds"].astype(object)
        data.loc[0, "home_odds"] = "two"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home)

        assert len(results) == 1  # row 0 should be skipped


# ============================================================================
# DATA LEAKAGE PREVENTION (Agent 5)
# ============================================================================


class TestDataLeakagePrevention:
    """Verify that strategies cannot access home_win through any channel."""

    def test_past_games_does_not_expose_home_win(self) -> None:
        """context['past_games'] must NOT contain home_win column."""
        leaked = {"found": False}

        def spy_strategy(row, ctx=None):
            if ctx and ctx.get("past_games") is not None:
                pg = ctx["past_games"]
                if "home_win" in pg.columns:
                    leaked["found"] = True
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100}

        data = _make_input(n=5, home_wins=[1, 0, 1, 0, 1])
        backtest(data, spy_strategy)

        assert not leaked["found"], (
            "LEAK: context['past_games'] exposes home_win column!"
        )

    def test_past_games_is_a_copy(self) -> None:
        """Mutating past_games should not affect the source data."""
        def mutating_strategy(row, ctx=None):
            if ctx and ctx.get("past_games") is not None:
                pg = ctx["past_games"]
                if len(pg) > 0:
                    # Try to add a column - should not affect original
                    pg["hacked"] = True
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100}

        data = _make_input(n=3, home_wins=[1, 1, 1])
        backtest(data, mutating_strategy)
        assert "hacked" not in data.columns

    def test_history_dicts_are_deep_copies(self) -> None:
        """Mutating context['history'] dicts should not affect engine state."""
        def mutating_strategy(row, ctx=None):
            if ctx and ctx.get("history"):
                # Try to corrupt the first history entry
                ctx["history"][0]["pnl"] = 999999
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100}

        data = _make_input(n=3, home_wins=[1, 0, 1])
        results = backtest(data, mutating_strategy)

        # The actual PnL in results should be correct, not corrupted
        assert results.iloc[0]["pnl"] != 999999

    def test_confidence_clamped_to_01(self) -> None:
        """Confidence outside [0,1] should be clamped."""
        def bad_conf_strategy(row, ctx=None):
            return {"action": "BUY_HOME", "confidence": 1.5, "size": 100}

        data = _make_input(n=1, home_wins=[1])
        results = backtest(data, bad_conf_strategy)

        assert len(results) == 1
        conf = results.iloc[0]["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence should be clamped, got {conf}"


# ============================================================================
# METRICS MODULE — KNOWN-VALUE TESTS (Agent 4/7)
# ============================================================================


class TestSharpeRatioKnownValues:
    """Direct unit tests for calculate_sharpe_ratio with known values."""

    def test_constant_positive_returns(self) -> None:
        """Constant positive returns have 0 std dev — Sharpe returns 0.0 (degenerate)."""
        from cuic_quant.metrics import calculate_sharpe_ratio

        # 10 trades, all winning exactly 100.0 → std=0 → Sharpe=0 by convention
        returns = pd.Series([100.0] * 10)
        sr = calculate_sharpe_ratio(returns, periods_per_year=365)
        assert sr == 0.0 or math.isinf(sr)

    def test_mostly_positive_returns(self) -> None:
        """Mostly positive with some variation should give high Sharpe."""
        from cuic_quant.metrics import calculate_sharpe_ratio

        returns = pd.Series([100.0, 80.0, 120.0, 90.0, 110.0, 95.0, 105.0, 88.0, 115.0, 100.0])
        sr = calculate_sharpe_ratio(returns, periods_per_year=365)
        assert sr > 5, f"Expected high Sharpe for consistently positive returns, got {sr}"

    def test_zero_mean_returns(self) -> None:
        """Equal wins and losses of same size should give Sharpe ≈ 0."""
        from cuic_quant.metrics import calculate_sharpe_ratio

        returns = pd.Series([100.0, -100.0] * 50)
        sr = calculate_sharpe_ratio(returns, periods_per_year=365)
        assert abs(sr) < 0.5

    def test_negative_mean_returns(self) -> None:
        """Mostly negative returns with variation should give negative Sharpe."""
        from cuic_quant.metrics import calculate_sharpe_ratio

        # Varying negative returns so std != 0
        returns = pd.Series([-100.0, -80.0, -120.0, -90.0, -110.0, -95.0, -105.0, -88.0, -115.0, -100.0])
        sr = calculate_sharpe_ratio(returns, periods_per_year=365)
        assert sr < 0, f"Expected negative Sharpe for negative returns, got {sr}"


class TestSortinoRatioKnownValues:
    """Direct unit tests for calculate_sortino_ratio with known values."""

    def test_no_downside(self) -> None:
        """All positive returns → zero downside deviation → Sortino returns 0 by convention."""
        from cuic_quant.metrics import calculate_sortino_ratio

        returns = pd.Series([50.0, 100.0, 75.0, 200.0, 150.0])
        sortino = calculate_sortino_ratio(returns, periods_per_year=365)
        # With no negative returns, downside_dev=0, Sortino returns 0 or inf
        assert sortino >= 0

    def test_sortino_higher_than_sharpe_with_asymmetric_returns(self) -> None:
        """Sortino should be higher than Sharpe for right-skewed returns."""
        from cuic_quant.metrics import calculate_sharpe_ratio, calculate_sortino_ratio

        # Right-skewed: small losses, big wins
        returns = pd.Series([200.0, -20.0, 150.0, -30.0, 300.0, -10.0, 180.0, -25.0])
        sharpe = calculate_sharpe_ratio(returns, periods_per_year=365)
        sortino = calculate_sortino_ratio(returns, periods_per_year=365)
        # Sortino should be higher because it only penalizes downside
        assert sortino > sharpe, f"Sortino ({sortino}) should exceed Sharpe ({sharpe})"

    def test_negative_mean(self) -> None:
        """Mostly negative returns with variation should give negative Sortino."""
        from cuic_quant.metrics import calculate_sortino_ratio

        returns = pd.Series([-100.0, -50.0, -75.0, 10.0, -120.0])
        sortino = calculate_sortino_ratio(returns, periods_per_year=365)
        assert sortino < 0, f"Expected negative Sortino, got {sortino}"


class TestMaxDrawdownKnownValues:
    """Direct unit tests for calculate_max_drawdown with known values."""

    def test_known_drawdown(self) -> None:
        """Calculate max drawdown from known cumulative PnL sequence."""
        from cuic_quant.metrics import calculate_max_drawdown

        # initial_bankroll=1000, cumulative_pnl = [500, 1000, 200, -100, 300]
        # equity = [1500, 2000, 1200, 900, 1300]
        # peak   = [1500, 2000, 2000, 2000, 2000]
        # dd     = [0,    0,    800/2000=0.4, 1100/2000=0.55, 700/2000=0.35]
        # max_dd = 0.55
        cum = pd.Series([500, 1000, 200, -100, 300])
        dd = calculate_max_drawdown(cum, initial_bankroll=1000.0)
        assert abs(dd - 0.55) < 0.01, f"Expected 0.55, got {dd}"

    def test_no_drawdown(self) -> None:
        """Monotonically increasing cumulative PnL should have 0 drawdown."""
        from cuic_quant.metrics import calculate_max_drawdown

        cum = pd.Series([100, 200, 300, 400, 500])
        dd = calculate_max_drawdown(cum, initial_bankroll=10000.0)
        assert dd == 0.0

    def test_total_loss(self) -> None:
        """Losing entire bankroll should have 100% drawdown."""
        from cuic_quant.metrics import calculate_max_drawdown

        # Start with bankroll=1000, lose it all
        cum = pd.Series([0, -500, -1000])
        dd = calculate_max_drawdown(cum, initial_bankroll=1000.0)
        assert abs(dd - 1.0) < 0.01, f"Expected 1.0, got {dd}"


class TestProfitFactorKnownValues:
    """Direct unit tests for calculate_profit_factor with known values."""

    def test_two_to_one(self) -> None:
        """$200 gross profit / $100 gross loss = 2.0."""
        from cuic_quant.metrics import calculate_profit_factor

        pnl = pd.Series([100.0, 100.0, -50.0, -50.0])
        pf = calculate_profit_factor(pnl)
        assert abs(pf - 2.0) < 0.01

    def test_all_wins(self) -> None:
        """No losses should give inf or very large value."""
        from cuic_quant.metrics import calculate_profit_factor

        pnl = pd.Series([100.0, 50.0, 200.0])
        pf = calculate_profit_factor(pnl)
        assert pf > 100 or math.isinf(pf)

    def test_all_losses(self) -> None:
        """No wins should give 0."""
        from cuic_quant.metrics import calculate_profit_factor

        pnl = pd.Series([-100.0, -50.0])
        pf = calculate_profit_factor(pnl)
        assert pf == 0.0

    def test_equal_win_loss(self) -> None:
        """Equal gross profit and loss = 1.0."""
        from cuic_quant.metrics import calculate_profit_factor

        pnl = pd.Series([100.0, -100.0])
        pf = calculate_profit_factor(pnl)
        assert abs(pf - 1.0) < 0.01


# ============================================================================
# VALIDATOR FIXES (Agent 1/9)
# ============================================================================


class TestValidatorFixedBugs:
    """Validator should auto-read attrs and account for cost_flat."""

    def test_validator_auto_reads_attrs(self) -> None:
        """Validator should read cost params from results.attrs if not given."""
        data = _make_input(n=5, home_wins=[1, 0, 1, 0, 1])
        results = backtest(data, always_bet_home, cost_pct=0.02, cost_flat=5.0)

        # Don't pass cost params — should auto-read from attrs
        report = validate_backtest_results(results, data)
        assert report["passed"] is True, f"Failed: {report['failures']}"

    def test_overbetting_with_cost_flat(self) -> None:
        """Validator check 9 should account for cost_flat in overbetting check."""
        data = _make_input(n=3, home_wins=[1, 1, 1])
        results = backtest(data, always_bet_home, cost_flat=10.0)

        # Corrupt bet_size to be between bankroll and bankroll-cost_flat
        # This should be caught by the fixed validator
        corrupted = results.copy()
        # initial bankroll=10000, cost_flat=10 → max bet = 9990
        # Engine caps at 9990, so a bet of 10000 is invalid
        corrupted.loc[corrupted.index[0], "bet_size"] = 10000.0
        report = validate_backtest_results(corrupted, data, cost_flat=10.0)
        assert report["passed"] is False


# ============================================================================
# WALK-FORWARD FIXES (Agent 6)
# ============================================================================


class TestWalkForwardFixes:
    """Verify walk-forward fold 0 bug is fixed."""

    def test_fold_0_not_included_when_no_training(self) -> None:
        """walk_forward_backtest should skip fold 0 (zero training data)."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        rng = np.random.default_rng(42)
        data = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=100, freq="D"),
            "game": [f"G{i}" for i in range(100)],
            "home_team": [f"H{i}" for i in range(100)],
            "away_team": [f"A{i}" for i in range(100)],
            "home_odds": rng.uniform(1.5, 3.0, 100).round(2),
            "away_odds": rng.uniform(1.5, 3.0, 100).round(2),
            "home_win": rng.integers(0, 2, 100),
        })

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = walk_forward_backtest(data, always_bet_home, n_splits=3)

        # Every fold with results should have non-empty training data
        for split in results["splits"]:
            assert len(split["train_data"]) > 0, (
                f"Fold {split['fold']} has zero training data!"
            )

    def test_train_test_split_unsorted_warns(self) -> None:
        """train_test_split should warn if data is not sorted chronologically."""
        from cuic_quant.backtest.walk_forward import train_test_split

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-03", "2026-01-01", "2026-01-02"]),
            "game": ["G1", "G2", "G3"],
            "value": [1, 2, 3],
        })

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            train, test = train_test_split(data, train_ratio=0.7)

        assert any("not sorted chronologically" in str(w.message) for w in caught)


# ============================================================================
# STATISTICS FIXES (Agent 3)
# ============================================================================


class TestStatisticsFixes:
    """Verify statistical formula fixes."""

    def test_p_value_one_sided_by_default(self) -> None:
        """calculate_p_value should use one-sided test by default."""
        from cuic_quant.backtest.statistics import calculate_p_value

        # 30% win rate with one-sided "greater" test should NOT be significant
        p_30 = calculate_p_value(win_rate=0.30, n_trades=100)
        assert p_30 > 0.5, (
            f"30% win rate should not be significant with one-sided 'greater' test, "
            f"got p={p_30}"
        )

        # 70% win rate should be significant
        p_70 = calculate_p_value(win_rate=0.70, n_trades=100)
        assert p_70 < 0.01

    def test_deflated_sharpe_with_skewness(self) -> None:
        """DSR should accept and use skewness/kurtosis parameters."""
        from cuic_quant.backtest.statistics import deflated_sharpe_ratio

        # With Gaussian assumptions (default)
        dsr_normal = deflated_sharpe_ratio(
            observed_sharpe=1.5, n_trials=10, n_observations=252,
            skewness=0.0, kurtosis=3.0,
        )
        # With heavy-tailed skewed returns (typical for betting)
        dsr_skewed = deflated_sharpe_ratio(
            observed_sharpe=1.5, n_trials=10, n_observations=252,
            skewness=-2.0, kurtosis=8.0,
        )
        # Skewed/fat-tailed returns → larger SE → different DSR
        assert dsr_normal != dsr_skewed
        assert 0 <= dsr_normal <= 1
        assert 0 <= dsr_skewed <= 1


# ============================================================================
# COMPARISON MODULE FIXES (Agent 6/8/9)
# ============================================================================


class TestComparisonFixes:
    """Verify comparison module fixes."""

    def test_detect_suspicious_catches_cheater(self) -> None:
        """A strategy that bets big on known wins should be flagged."""
        comparison = pytest.importorskip("cuic_quant.backtest.comparison")

        # Create a scenario where a "cheating" strategy wins 20/20 at 2.5 odds
        data = pd.DataFrame({
            "timestamp": pd.to_datetime([f"2026-01-{i+1:02d}" for i in range(20)]),
            "game": [f"G{i}" for i in range(20)],
            "home_team": [f"H{i}" for i in range(20)],
            "away_team": [f"A{i}" for i in range(20)],
            "home_odds": [2.50] * 20,
            "away_odds": [1.60] * 20,
            "home_win": [1] * 20,
        })

        def always_home(row, ctx=None):
            return {"action": "BUY_HOME", "confidence": 0.99, "size": 100.0}

        results = backtest(data, always_home)
        flags = comparison.detect_suspicious_results(results)

        if isinstance(flags, dict):
            assert flags.get("is_suspicious") is True, (
                f"20/20 wins at 2.50 odds should be flagged, got: {flags}"
            )
        elif isinstance(flags, list):
            assert len(flags) > 0

    def test_display_comparison_all_nan_columns(self, capsys) -> None:
        """display_comparison should handle all-NaN columns without crashing."""
        comparison = pytest.importorskip("cuic_quant.backtest.comparison")

        df = pd.DataFrame({
            "strategy_name": ["A", "B"],
            "total_pnl": [100.0, -50.0],
            "win_rate": [float("nan"), float("nan")],  # all-NaN column
        })
        df = df.set_index("strategy_name")
        # Should not crash
        comparison.display_comparison(df)
        captured = capsys.readouterr()
        assert "STRATEGY COMPARISON" in captured.out

    def test_rank_strategies_handles_ties(self) -> None:
        """Tied values should get the same rank."""
        comparison = pytest.importorskip("cuic_quant.backtest.comparison")

        df = pd.DataFrame({
            "strategy_name": ["A", "B", "C"],
            "total_pnl": [100.0, 100.0, 50.0],
            "win_rate": [0.5, 0.5, 0.4],
        })
        df = df.set_index("strategy_name")
        ranked = comparison.rank_strategies(df, metric="total_pnl")
        # A and B have same PnL, should have same rank
        rank_values = ranked["rank"].tolist()
        assert rank_values[0] == rank_values[1] == 1
        assert rank_values[2] == 2
