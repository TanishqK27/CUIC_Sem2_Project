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


# ============================================================================
# VALIDATE_STRATEGY_SIZE — unit tests (Task 1 of nan-size-guard plan)
# ============================================================================


class TestValidateStrategySize:
    """Unit tests for _validate_strategy_size helper — math audit + fuzzing."""

    # --- Math audit: valid inputs return correct Python float ---

    def test_valid_float_returns_exact_value(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        assert _validate_strategy_size(100.0, "game1") == 100.0

    def test_valid_int_returns_float(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        result = _validate_strategy_size(50, "game1")
        assert result == 50.0
        assert isinstance(result, float)

    def test_numpy_float64_returns_python_float(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        result = _validate_strategy_size(np.float64(200.0), "game1")
        assert result == 200.0
        assert isinstance(result, float)

    def test_numpy_float32_valid_returns_python_float(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        result = _validate_strategy_size(np.float32(75.0), "game1")
        assert result == pytest.approx(75.0)
        assert isinstance(result, float)

    def test_small_valid_size_accepted(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        result = _validate_strategy_size(0.01, "game1")
        assert result == pytest.approx(0.01)
        assert isinstance(result, float)

    # --- Fuzzing: all invalid inputs must raise ValueError ---

    @pytest.mark.parametrize("invalid_size", [
        None,
        float("nan"),
        np.float32("nan"),
        np.float64("nan"),
        math.nan,
        np.nan,
        float("inf"),
        float("-inf"),
        0.0,
        -1.0,
        -100.0,
        "100",
        "nan",
        pd.NA,
        pd.NaT,
        [],
        {},
    ])
    def test_invalid_size_raises_value_error(self, invalid_size: object) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError):
            _validate_strategy_size(invalid_size, "game1")

    def test_error_message_contains_game_name(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="my_special_game"):
            _validate_strategy_size(float("nan"), "my_special_game")

    def test_error_message_contains_size_keyword(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="size"):
            _validate_strategy_size(float("nan"), "game1")

    def test_nan_error_message_contains_nan(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="nan"):
            _validate_strategy_size(float("nan"), "game1")

    def test_zero_error_message_contains_zero(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match=r"size.*0|0.*size"):
            _validate_strategy_size(0.0, "game1")

    def test_inf_raises(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="inf"):
            _validate_strategy_size(float("inf"), "game1")

    def test_negative_inf_raises(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="inf"):
            _validate_strategy_size(float("-inf"), "game1")

    def test_string_raises(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="non-numeric"):
            _validate_strategy_size("100", "game1")

    def test_pd_na_raises(self) -> None:
        from cuic_quant.backtest.engine import _validate_strategy_size
        with pytest.raises(ValueError, match="non-numeric|size"):
            _validate_strategy_size(pd.NA, "game1")


# ============================================================================
# NAN SIZE STRICT — integration tests (Task 2 of nan-size-guard plan)
# ============================================================================


class TestNaNSizeStrict:
    """Integration: NaN/invalid size in strategy signal handled strictly."""

    def test_numpy_float32_nan_skipped_with_warning(self) -> None:
        """np.float32('nan') must skip the trade and emit a warning."""
        call_count = {"n": 0}

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 2:
                return {"action": "BUY_HOME", "confidence": 0.5,
                        "size": np.float32("nan")}
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=5, home_wins=[1, 1, 1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 4  # 2nd call returns NaN size — that row is skipped
        assert not results["bet_size"].isna().any()
        assert not results["pnl"].isna().any()
        assert not results["cumulative_pnl"].isna().any()
        assert not results["bankroll"].isna().any()
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)

    def test_pd_na_size_skipped_with_warning(self) -> None:
        """pd.NA as size must skip the trade and emit a warning."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": pd.NA}

        data = _make_input(n=3, home_wins=[1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)
        assert len(results) == 0
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)

    def test_zero_size_skipped_with_warning(self) -> None:
        """size=0.0 must emit a warning and skip (previously silent skip)."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 0.0}

        data = _make_input(n=3, home_wins=[1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)
        assert len(results) == 0
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)

    def test_negative_size_skipped_with_warning(self) -> None:
        """Negative size must emit a warning and skip."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": -50.0}

        data = _make_input(n=2, home_wins=[1, 1], odds=2.0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)
        assert len(results) == 0
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)

    def test_nan_size_does_not_corrupt_subsequent_trades(self) -> None:
        """NaN size on row 1 must not corrupt rows 2-10 cumulative_pnl."""
        call_count = {"n": 0}

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"action": "BUY_HOME", "confidence": 0.5,
                        "size": float("nan")}
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=10, home_wins=[1] * 10, odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 9
        assert results.iloc[-1]["cumulative_pnl"] == pytest.approx(900.0)
        assert not results["cumulative_pnl"].isna().any()
        assert not results["bankroll"].isna().any()

    def test_metrics_all_finite_after_nan_skip(self) -> None:
        """calculate_all_metrics must return all-finite values after a NaN skip."""
        call_count = {"n": 0}

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 3:
                return {"action": "BUY_HOME", "confidence": 0.5,
                        "size": float("nan")}
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(
            n=10,
            home_wins=[1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
            odds=2.0,
        )
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 9  # row 3 skipped, 9 of 10 rows trade
        from cuic_quant.metrics import calculate_all_metrics
        metrics = calculate_all_metrics(results)
        for key, value in metrics.items():
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                try:
                    assert math.isfinite(float(value)), f"Metric '{key}' is not finite: {value}"
                except (TypeError, ValueError):
                    pass  # non-numeric metric values are fine

    def test_inf_size_skipped_with_warning(self) -> None:
        """float('inf') as size must emit a warning and skip."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": float("inf")}

        data = _make_input(n=3, home_wins=[1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)
        assert len(results) == 0
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)

    def test_warning_message_human_readable(self) -> None:
        """Warning must name the game, mention 'size', be a UserWarning."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": float("nan")}

        data = _make_input(n=1, home_wins=[1], odds=2.0)
        data = data.copy()
        data["game"] = ["Liverpool vs Arsenal"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            backtest(data, strategy, initial_bankroll=10000.0)

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        msg = str(user_warnings[0].message)
        assert "Liverpool vs Arsenal" in msg
        assert "size" in msg.lower()


# ============================================================================
# PER-ROW BASEEXCEPTION GUARD (Bug Fix 2)
# ============================================================================


class TestStrategyExceptionGuard:
    """Verify the outer per-row BaseException guard introduced in Bug Fix 2.

    The outer guard wraps the entire loop body so any crash on any row is
    isolated. Previously computed trades are always returned.

    B3 (the inner guard) handles Exception from strategy_fn specifically.
    The outer guard handles non-fatal BaseException subclasses (e.g. MemoryError,
    GeneratorExit) by warning and skipping the row. KeyboardInterrupt and SystemExit
    are re-raised after emitting a "partial results" warning — they must never be
    swallowed. B3 handles Exception subclasses from strategy_fn with a specific message.
    """

    # ------------------------------------------------------------------
    # Behaviour tests — exception in strategy skips row, preserves trades
    # ------------------------------------------------------------------

    def test_exception_in_strategy_skips_row(self) -> None:
        """RuntimeError on row 2 → warning emitted, row skipped, others complete."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("strategy crash on row 2")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=4, home_wins=[1, 1, 1, 1])
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 3  # row 2 skipped, 3 of 4 rows trade

    def test_exception_in_strategy_no_corruption(self) -> None:
        """RuntimeError on row 2 → cumulative_pnl and bankroll unaffected by skip."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("crash")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        # All rows win at 2.0 odds → each trade earns 100.0
        data = _make_input(n=4, home_wins=[1, 1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        # 3 winning trades of 100 each → cumulative_pnl = 300
        assert results["cumulative_pnl"].iloc[-1] == pytest.approx(300.0)
        assert results["bankroll"].iloc[-1] == pytest.approx(10300.0)
        # No NaN in any numeric column
        for col in ("pnl", "cumulative_pnl", "bankroll"):
            assert results[col].notna().all(), f"NaN found in column '{col}'"

    def test_exception_message_contains_game_and_type(self) -> None:
        """Warning contains game name and the exception class name."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("test error")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=2, home_wins=[1, 1])
        data["game"] = ["ManCity vs Arsenal", "Chelsea vs Spurs"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            backtest(data, strategy, initial_bankroll=10000.0)

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        msg = str(user_warnings[0].message)
        assert "ManCity vs Arsenal" in msg
        assert "ValueError" in msg

    def test_multiple_exceptions_skip_multiple_rows(self) -> None:
        """Rows 2, 4 raise RuntimeError → rows 1, 3, 5 complete (3 trades)."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count in (2, 4):
                raise RuntimeError(f"crash on call {call_count}")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=5, home_wins=[1, 1, 1, 1, 1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 3
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 2

    def test_exception_after_valid_trades_preserves_history(self) -> None:
        """3 good trades, then crash, then 2 more good trades → 5 total trades."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 4:
                raise RuntimeError("mid-run crash")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=6, home_wins=[1, 1, 1, 1, 1, 1])
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 5  # 6 rows − 1 crashed = 5 trades
        # 5 winning trades of 100 each at default odds=2.0 → cumulative_pnl = 500
        assert results["cumulative_pnl"].iloc[-1] == pytest.approx(500.0)

    # ------------------------------------------------------------------
    # BaseException tests — outer guard (NOT B3)
    # ------------------------------------------------------------------

    def test_base_exception_in_row_processing_skips_row(self) -> None:
        """Strategy raising BaseException (not Exception) is caught by outer guard.

        BaseException is NOT caught by B3's `except Exception`. Before the fix,
        this crashes the entire backtest. After the fix, the row is skipped with
        a warning and the remaining rows complete normally.
        """
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                # BaseException is not caught by B3's `except Exception`.
                # It escapes B3 and must be caught by the outer guard.
                raise BaseException("direct base exception — not an Exception subclass")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=4, home_wins=[1, 1, 1, 1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Before fix: raises BaseException, crashing the entire backtest.
            # After fix: row 2 skipped, 3 trades returned.
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 3  # row 2 skipped
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("BaseException" in str(uw.message) for uw in user_warnings)

    def test_keyboard_interrupt_reraises_with_partial_results(self) -> None:
        """KeyboardInterrupt is re-raised after emitting a 'partial results' warning.

        Before fix: KeyboardInterrupt propagates silently, no warning.
        After fix: Warning emitted with 'partial' / 'completed', then re-raised.
        The warning is the signal to callers that partial results are available.
        """
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise KeyboardInterrupt()
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=5, home_wins=[1, 1, 1, 1, 1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Must re-raise: KeyboardInterrupt must not be swallowed.
            with pytest.raises(KeyboardInterrupt):
                backtest(data, strategy, initial_bankroll=10000.0)

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        # Must emit a warning about partial results BEFORE re-raising.
        # Before fix: no warning → assertion fails.
        assert len(user_warnings) >= 1
        msg = str(user_warnings[-1].message).lower()
        assert "partial" in msg or "completed" in msg

    def test_system_exit_reraises(self) -> None:
        """SystemExit is re-raised (not swallowed) after emitting a warning."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise SystemExit(1)
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=4, home_wins=[1, 1, 1, 1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with pytest.raises(SystemExit):
                backtest(data, strategy, initial_bankroll=10000.0)

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        # Must warn before re-raising, and warning must name partial results.
        assert len(user_warnings) >= 1
        msg = str(user_warnings[-1].message).lower()
        assert "partial" in msg or "completed" in msg

    # ------------------------------------------------------------------
    # Statistical integrity
    # ------------------------------------------------------------------

    def test_exception_skip_no_nan_in_results(self) -> None:
        """10-row backtest with exception on row 5 → no NaN in output columns."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 5:
                raise RuntimeError("mid-run crash")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=10, home_wins=[1] * 10, odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 9  # row 5 skipped
        for col in ("pnl", "cumulative_pnl", "bankroll"):
            assert results[col].notna().all(), f"NaN found in '{col}'"
        # 9 winning trades of 100 each at odds=2.0 → cumulative_pnl = 900
        assert results["cumulative_pnl"].iloc[-1] == pytest.approx(900.0)

    def test_all_metrics_finite_after_exception_skip(self) -> None:
        """calculate_all_metrics() on backtest with mid-run crash → all metrics finite."""
        call_count = 0

        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 5:
                raise RuntimeError("crash")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input(n=10, home_wins=[1, 0] * 5, odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        assert len(results) == 9
        from cuic_quant.metrics import calculate_all_metrics
        metrics = calculate_all_metrics(results)
        for key, value in metrics.items():
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                try:
                    assert math.isfinite(float(value)), (
                        f"Metric '{key}' is not finite: {value}"
                    )
                except (TypeError, ValueError):
                    pass  # non-numeric metric values are fine

    # ------------------------------------------------------------------
    # Warning usability
    # ------------------------------------------------------------------

    def test_exception_warning_is_user_warning(self) -> None:
        """Warning is a UserWarning — catchable with standard warnings.catch_warnings."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            raise RuntimeError("test")

        data = _make_input(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            backtest(data, strategy, initial_bankroll=10000.0)

        assert any(issubclass(x.category, UserWarning) for x in w)

    def test_exception_warning_contains_exception_type(self) -> None:
        """Warning string contains the exception class name."""
        def strategy(row: pd.Series, ctx: dict | None = None) -> dict:
            raise TypeError("wrong type")

        data = _make_input(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            backtest(data, strategy, initial_bankroll=10000.0)

        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert "TypeError" in str(user_warnings[0].message)


# ============================================================================
# INITIAL BANKROLL RESOLUTION FIX (Bug Fix 3)
# ============================================================================


def _make_trades_no_attrs(
    n: int = 5,
    home_wins: list[int] | None = None,
    initial_bankroll: float = 10000.0,
    odds: float = 2.0,
) -> pd.DataFrame:
    """Run backtest and strip attrs['initial_bankroll'] to test derivation/failure paths."""
    data = _make_input(n=n, home_wins=home_wins or [1, 0] * (n // 2 + 1), odds=odds)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        results = backtest(data, always_bet_home, initial_bankroll=initial_bankroll)
    results.attrs.pop("initial_bankroll", None)
    return results


def _run_backtest(
    n: int = 5,
    home_wins: list[int] | None = None,
    initial_bankroll: float = 10000.0,
    odds: float = 2.0,
) -> pd.DataFrame:
    """Run backtest and return results with attrs['initial_bankroll'] intact."""
    data = _make_input(n=n, home_wins=home_wins or [1, 0] * (n // 2 + 1), odds=odds)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        results = backtest(data, always_bet_home, initial_bankroll=initial_bankroll)
    return results


class TestInitialBankrollResolution:
    """Verify that calculate_all_metrics resolves initial_bankroll correctly.

    Three resolution paths:
    1. attrs["initial_bankroll"] present (set by backtest()) -> used directly
    2. attrs absent, bankroll column present -> derived as bankroll[0] - pnl[0]
    3. attrs absent, no bankroll column -> ValueError (strict fail)

    All downstream metric sites (max_drawdown, return_on_capital, calmar_ratio)
    must use the single resolved variable -- no secondary attrs reads.

    Expected outcome (TDD): 8 failing tests until Bug Fix 3 is implemented.
    """

    # ------------------------------------------------------------------
    # Math audit -- correctness of the resolved value in each metric
    # ------------------------------------------------------------------

    def test_attrs_used_not_bankroll_iloc0(self) -> None:
        """attrs['initial_bankroll'] is used, not bankroll.iloc[0].

        bankroll.iloc[0] is the bankroll AFTER the first trade (e.g. $15,000 after
        a $5,000 win). The correct initial_bankroll is $10,000. The two values
        are different only when the first trade has non-zero PnL.
        """
        from cuic_quant.metrics import calculate_all_metrics

        # First trade: BUY_HOME, home wins, size=5000 at odds=2.0 -> PnL = +5000
        # bankroll.iloc[0] = 15000 (after win)
        # attrs["initial_bankroll"] = 10000 (set by backtest)
        data = _make_input(n=3, home_wins=[1, 1, 1], odds=2.0)

        call_count = 0

        def big_first_bet(row, ctx=None):
            nonlocal call_count
            call_count += 1
            size = 5000.0 if call_count == 1 else 100.0
            return {"action": "BUY_HOME", "confidence": 0.6, "size": size}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, big_first_bet, initial_bankroll=10000.0)

        assert results.attrs["initial_bankroll"] == 10000.0
        assert results["bankroll"].iloc[0] == pytest.approx(15000.0)  # after first win

        metrics = calculate_all_metrics(results)
        # With correct initial_bankroll=10000 and only wins, max_drawdown = 0
        assert metrics["max_drawdown"] == pytest.approx(0.0)
        # return_on_capital = total_pnl / 10000, not / 15000
        expected_roc = metrics["total_pnl"] / 10000.0
        assert metrics["return_on_capital"] == pytest.approx(expected_roc)

    def test_max_drawdown_correct_with_large_first_loss(self) -> None:
        """Known-value: first trade loses $5,000 from $10,000 bankroll.

        Equity curve: [10000, 5000, 6000, 7000]  (start + after each trade)
        Using correct initial_bankroll=10000:
          peak=[10000,10000,10000,10000], dd=[0, 0.5, 0.4, 0.3] -> max_dd=0.5
        Using wrong initial_bankroll=5000 (bankroll.iloc[0] after the loss):
          equity=[5000, 0, 1000, 2000], peak=[5000,5000,5000,5000]
          dd=[0, 1.0, 0.8, 0.6] -> max_dd=1.0 (WRONG)
        """
        from cuic_quant.metrics import calculate_all_metrics

        data = _make_input(n=3, home_wins=[0, 1, 1], odds=2.0)

        call_count = 0

        def sized_strategy(row, ctx=None):
            nonlocal call_count
            call_count += 1
            size = 5000.0 if call_count == 1 else 1000.0
            return {"action": "BUY_HOME", "confidence": 0.6, "size": size}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, sized_strategy, initial_bankroll=10000.0)

        # Verify setup: first trade lost $5,000
        assert results["pnl"].iloc[0] == pytest.approx(-5000.0)
        assert results["bankroll"].iloc[0] == pytest.approx(5000.0)
        assert results.attrs["initial_bankroll"] == 10000.0

        metrics = calculate_all_metrics(results)
        # Equity: 10000 -> 5000 -> 6000 -> 7000
        # Peak: 10000 throughout. Max DD = 5000/10000 = 0.5
        assert metrics["max_drawdown"] == pytest.approx(0.5, abs=0.01)

    def test_return_on_capital_uses_initial_bankroll_from_attrs(self) -> None:
        """return_on_capital = total_pnl / attrs['initial_bankroll'] (attrs path)."""
        from cuic_quant.metrics import calculate_all_metrics

        data = _make_input(n=5, home_wins=[1, 1, 1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home, initial_bankroll=10000.0)

        metrics = calculate_all_metrics(results)
        expected_roc = metrics["total_pnl"] / 10000.0
        assert metrics["return_on_capital"] == pytest.approx(expected_roc)

    def test_return_on_capital_uses_derived_initial_bankroll(self) -> None:
        """return_on_capital uses derived initial_bankroll when attrs is absent.

        Before fix: falls back to metrics['roi'] (yield-on-turnover).
        After fix: total_pnl / derived_initial_bankroll (correct).

        These two quantities are different when initial_bankroll != total_wagered,
        which is always true in practice (e.g. 10000 bankroll, 500 total wagered).
        """
        from cuic_quant.metrics import calculate_all_metrics

        # All wins, bet_size=100, odds=2.0 -> total_wagered=500, total_pnl=500
        # initial_bankroll=10000 -> return_on_capital = 500/10000 = 0.05
        # roi (yield-on-turnover) = 500/500 = 1.0 <- completely different
        results = _make_trades_no_attrs(
            n=5, home_wins=[1, 1, 1, 1, 1], initial_bankroll=10000.0, odds=2.0
        )
        assert "initial_bankroll" not in results.attrs  # confirm attrs stripped

        metrics = calculate_all_metrics(results)

        # Derived initial_bankroll = bankroll[0] - pnl[0]
        derived_ib = float(results["bankroll"].iloc[0] - results["pnl"].iloc[0])
        expected_roc = metrics["total_pnl"] / derived_ib
        assert metrics["return_on_capital"] == pytest.approx(expected_roc)
        # Must NOT equal roi (they differ when initial_bankroll != total_wagered)
        assert abs(metrics["return_on_capital"] - metrics["roi"]) > 0.01

    def test_calmar_ratio_uses_correct_initial_bankroll(self) -> None:
        """Calmar ratio uses the correctly resolved initial_bankroll, not bankroll.iloc[0]."""
        from cuic_quant.metrics import calculate_all_metrics

        df = _make_trades_no_attrs(odds=2.5)  # derivation path: attrs absent
        # bankroll.iloc[0] is the bankroll AFTER the first trade -- NOT initial_bankroll
        derived_ib = float(df["bankroll"].iloc[0] - df["pnl"].iloc[0])

        metrics = calculate_all_metrics(df)

        # return_on_capital = total_pnl / initial_bankroll uses the derived value
        # Calmar numerator (total_return) = total_pnl / initial_bankroll (same denominator)
        # Verify: return_on_capital is consistent with derived_ib, not bankroll.iloc[0]
        expected_roc = metrics["total_pnl"] / derived_ib
        assert metrics["return_on_capital"] == pytest.approx(expected_roc, rel=1e-6)
        # Calmar = annualized_return / max_drawdown -- verify it's finite when max_drawdown > 0
        if metrics["max_drawdown"] > 0:
            assert math.isfinite(metrics["calmar_ratio"])
            assert metrics["calmar_ratio"] != pytest.approx(0.0, abs=1e-10)

    # ------------------------------------------------------------------
    # Resolution path tests
    # ------------------------------------------------------------------

    def test_attrs_path_used_when_present(self) -> None:
        """attrs['initial_bankroll'] = 10000.0 is used directly."""
        from cuic_quant.metrics import calculate_all_metrics

        data = _make_input(n=3, home_wins=[1, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, always_bet_home, initial_bankroll=10000.0)

        assert results.attrs.get("initial_bankroll") == 10000.0
        metrics = calculate_all_metrics(results)
        expected_roc = metrics["total_pnl"] / 10000.0
        assert metrics["return_on_capital"] == pytest.approx(expected_roc, rel=1e-6)

    def test_derivation_path_when_attrs_absent(self) -> None:
        """When attrs is absent, initial_bankroll is derived as bankroll[0] - pnl[0]."""
        from cuic_quant.metrics import calculate_all_metrics

        # initial_bankroll=8000, bet_size=100, first trade wins at 2.0 -> pnl=100
        # bankroll[0] = 8100. derived = 8100 - 100 = 8000
        results = _make_trades_no_attrs(
            n=3, home_wins=[1, 1, 1], initial_bankroll=8000.0, odds=2.0
        )
        assert "initial_bankroll" not in results.attrs

        metrics = calculate_all_metrics(results)
        assert isinstance(metrics, dict)
        # return_on_capital must use derived value (8000), not roi
        expected_roc = metrics["total_pnl"] / 8000.0
        assert metrics["return_on_capital"] == pytest.approx(expected_roc, abs=0.001)

    def test_derivation_gives_same_result_as_attrs(self) -> None:
        """Derivation path and attrs path give identical max_drawdown and return_on_capital."""
        from cuic_quant.metrics import calculate_all_metrics

        data = _make_input(n=5, home_wins=[0, 1, 0, 1, 1], odds=2.0)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results_with_attrs = backtest(data, always_bet_home, initial_bankroll=10000.0)

        results_no_attrs = results_with_attrs.copy()
        results_no_attrs.attrs = dict(results_with_attrs.attrs)
        results_no_attrs.attrs.pop("initial_bankroll", None)

        metrics_attrs = calculate_all_metrics(results_with_attrs)
        metrics_derived = calculate_all_metrics(results_no_attrs)

        assert metrics_attrs["max_drawdown"] == pytest.approx(
            metrics_derived["max_drawdown"], abs=1e-9
        )
        assert metrics_attrs["return_on_capital"] == pytest.approx(
            metrics_derived["return_on_capital"], rel=1e-6
        )

    def test_raises_when_attrs_absent_and_no_bankroll_column(self) -> None:
        """ValueError when attrs absent and no bankroll column to derive from.

        Before fix: silently uses 10000.0 default -> wrong metrics, no warning.
        After fix: raises ValueError immediately.
        """
        from cuic_quant.metrics import calculate_all_metrics

        df = pd.DataFrame({
            "pnl": [100.0, -50.0, 200.0],
            "cumulative_pnl": [100.0, 50.0, 250.0],
            "outcome": ["WIN", "LOSS", "WIN"],
        })
        assert "initial_bankroll" not in df.attrs
        assert "bankroll" not in df.columns

        with pytest.raises(ValueError):
            calculate_all_metrics(df)

    def test_raises_when_attrs_absent_and_empty_dataframe(self) -> None:
        """ValueError when attrs absent and DataFrame is empty."""
        from cuic_quant.metrics import calculate_all_metrics

        df = pd.DataFrame(columns=["pnl", "cumulative_pnl", "outcome"])
        assert "initial_bankroll" not in df.attrs

        with pytest.raises(ValueError):
            calculate_all_metrics(df)

    def test_error_message_is_actionable(self) -> None:
        """ValueError message names attrs['initial_bankroll'] and backtest()."""
        from cuic_quant.metrics import calculate_all_metrics

        df = pd.DataFrame({
            "pnl": [100.0],
            "cumulative_pnl": [100.0],
            "outcome": ["WIN"],
        })

        with pytest.raises(ValueError, match=r"attrs\[.initial_bankroll.\]"):
            calculate_all_metrics(df.copy())
        with pytest.raises(ValueError, match=r"backtest\(\)"):
            calculate_all_metrics(df.copy())

    # ------------------------------------------------------------------
    # Full pipeline sanity check
    # ------------------------------------------------------------------

    def test_all_metrics_finite_after_fix(self) -> None:
        """Full calculate_all_metrics() run with large first loss -> all metrics finite."""
        from cuic_quant.metrics import calculate_all_metrics

        data = _make_input(n=6, home_wins=[0, 1, 0, 1, 1, 1], odds=2.0)

        call_count = 0

        def variable_size(row, ctx=None):
            nonlocal call_count
            call_count += 1
            size = 5000.0 if call_count == 1 else 100.0
            return {"action": "BUY_HOME", "confidence": 0.6, "size": size}

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            results = backtest(data, variable_size, initial_bankroll=10000.0)

        metrics = calculate_all_metrics(results)
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                assert math.isfinite(value), f"metrics['{key}'] = {value} is not finite"

    def test_raises_when_initial_bankroll_is_zero(self):
        """Zero initial_bankroll in attrs raises ValueError before corrupting metrics."""
        from cuic_quant.metrics import calculate_all_metrics

        results = _run_backtest()
        results.attrs["initial_bankroll"] = 0.0
        with pytest.raises(ValueError, match="positive"):
            calculate_all_metrics(results)

    def test_calculate_max_drawdown_raises_on_zero_bankroll(self):
        """calculate_max_drawdown raises directly when called with initial_bankroll=0."""
        from cuic_quant.metrics import calculate_max_drawdown
        import pandas as pd

        with pytest.raises(ValueError, match="positive"):
            calculate_max_drawdown(pd.Series([100.0, 200.0]), initial_bankroll=0.0)


class TestComputePeriodsPerYear:
    """Unit tests for _compute_periods_per_year fencepost fix and fallbacks."""

    def test_one_bet_per_day(self):
        """10 bets on consecutive days 0-9: (10-1)/9 * 365.25 = 365.25."""
        from cuic_quant.metrics import _compute_periods_per_year

        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        df = pd.DataFrame({"timestamp": dates, "pnl": [1.0] * 10})
        result = _compute_periods_per_year(df)
        assert result == pytest.approx(365.25, rel=1e-6), f"Expected 365.25, got {result}"

    def test_three_bets_per_day(self):
        """30 bets over days 0-9 (3/day): (30-1)/9 * 365.25 ≈ 1176.9."""
        from cuic_quant.metrics import _compute_periods_per_year

        # 3 bets per day for 10 days = 30 bets, all at midnight → time span = 9 days exactly
        dates = []
        for d in range(10):
            base = pd.Timestamp("2025-01-01") + pd.Timedelta(days=d)
            dates.extend([base, base, base])
        df = pd.DataFrame({"timestamp": dates, "pnl": [1.0] * 30})
        result = _compute_periods_per_year(df)
        expected = 29.0 / 9.0 * 365.25  # ≈ 1176.9
        assert result == pytest.approx(expected, rel=1e-6), f"Expected {expected}, got {result}"

    def test_one_bet_per_week(self):
        """5 bets on days 0,7,14,21,28: (5-1)/28 * 365.25 ≈ 52.18."""
        from cuic_quant.metrics import _compute_periods_per_year

        dates = [pd.Timestamp("2025-01-01") + pd.Timedelta(weeks=w) for w in range(5)]
        df = pd.DataFrame({"timestamp": dates, "pnl": [1.0] * 5})
        result = _compute_periods_per_year(df)
        expected = 4.0 / 28.0 * 365.25  # ≈ 52.18
        assert result == pytest.approx(expected, rel=1e-6), f"Expected {expected}, got {result}"

    def test_two_bets_fencepost(self):
        """2 bets 7 days apart: (2-1)/7 * 365.25 = 52.18, NOT 104.36."""
        from cuic_quant.metrics import _compute_periods_per_year

        dates = [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-08")]
        df = pd.DataFrame({"timestamp": dates, "pnl": [1.0] * 2})
        result = _compute_periods_per_year(df)
        correct = 1.0 / 7.0 * 365.25  # 52.18
        wrong = 2.0 / 7.0 * 365.25    # 104.36 (old formula)
        assert result == pytest.approx(correct, rel=1e-6), f"Expected {correct}, got {result}"
        assert result != pytest.approx(wrong, rel=0.01), "Got the old fencepost-error value"

    def test_no_timestamp_column_warns(self):
        """DataFrame without timestamp column returns 365.0 and emits warning."""
        from cuic_quant.metrics import _compute_periods_per_year

        df = pd.DataFrame({"pnl": [1.0, 2.0, 3.0]})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _compute_periods_per_year(df)
        assert result == 365.0
        assert any("timestamp" in str(wn.message).lower() for wn in w), \
            f"Expected warning about missing timestamp, got: {[str(wn.message) for wn in w]}"

    def test_same_timestamp_warns(self):
        """All bets at identical timestamp returns 365.0 and emits warning."""
        from cuic_quant.metrics import _compute_periods_per_year

        ts = pd.Timestamp("2025-06-01")
        df = pd.DataFrame({"timestamp": [ts, ts, ts], "pnl": [1.0] * 3})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _compute_periods_per_year(df)
        assert result == 365.0
        assert any("timestamp" in str(wn.message).lower() or "same" in str(wn.message).lower()
                    for wn in w), \
            f"Expected warning about same timestamps, got: {[str(wn.message) for wn in w]}"


class TestAnnualizationIntegration:
    """Integration tests for Sharpe/Sortino annualization through calculate_all_metrics."""

    def test_periods_per_year_in_metrics(self):
        """calculate_all_metrics stores computed periods_per_year in output."""
        from cuic_quant.metrics import calculate_all_metrics

        results = _run_backtest()
        metrics = calculate_all_metrics(results)
        assert "periods_per_year" in metrics
        assert metrics["periods_per_year"] > 0
        assert math.isfinite(metrics["periods_per_year"])

    def test_sharpe_scales_with_sqrt_frequency(self):
        """Sharpe with periods_per_year=400 is 2x Sharpe with periods_per_year=100."""
        from cuic_quant.metrics import calculate_sharpe_ratio

        # Use returns with non-zero mean and non-zero variance
        returns = pd.Series([0.05, -0.02, 0.03, -0.01, 0.04, -0.03, 0.02, 0.01])
        sharpe_100 = calculate_sharpe_ratio(returns, periods_per_year=100)
        sharpe_400 = calculate_sharpe_ratio(returns, periods_per_year=400)
        # sqrt(400) / sqrt(100) = 20/10 = 2.0
        if sharpe_100 != 0.0:
            ratio = sharpe_400 / sharpe_100
            assert ratio == pytest.approx(2.0, rel=1e-6), \
                f"Expected ratio 2.0 (sqrt scaling), got {ratio}"

    def test_sortino_scales_with_sqrt_frequency(self):
        """Sortino with periods_per_year=400 is 2x Sortino with periods_per_year=100."""
        from cuic_quant.metrics import calculate_sortino_ratio

        # Use returns with some negative values (needed for non-zero downside deviation)
        returns = pd.Series([0.05, -0.02, 0.03, -0.01, 0.04, -0.03, 0.02, 0.01])
        sortino_100 = calculate_sortino_ratio(returns, periods_per_year=100)
        sortino_400 = calculate_sortino_ratio(returns, periods_per_year=400)
        if sortino_100 != 0.0:
            ratio = sortino_400 / sortino_100
            assert ratio == pytest.approx(2.0, rel=1e-6), \
                f"Expected ratio 2.0 (sqrt scaling), got {ratio}"

    def test_sharpe_default_matches_sortino_default(self):
        """Both functions use 365.0 as default periods_per_year."""
        from cuic_quant.metrics import calculate_sharpe_ratio, calculate_sortino_ratio

        returns = pd.Series([0.05, -0.02, 0.03, -0.01, 0.04, -0.03, 0.02, 0.01])
        # Call without specifying periods_per_year — both should use 365.0
        sharpe_default = calculate_sharpe_ratio(returns)
        sharpe_365 = calculate_sharpe_ratio(returns, periods_per_year=365.0)
        assert sharpe_default == pytest.approx(sharpe_365, rel=1e-10), \
            "Sharpe default should be 365.0"

        sortino_default = calculate_sortino_ratio(returns)
        sortino_365 = calculate_sortino_ratio(returns, periods_per_year=365.0)
        assert sortino_default == pytest.approx(sortino_365, rel=1e-10), \
            "Sortino default should be 365.0"


def _make_wf_data(n: int = 100) -> pd.DataFrame:
    """Create n-row DataFrame suitable for walk-forward tests."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n, freq="D"),
        "game": [f"TeamA vs TeamB_{i}" for i in range(n)],
        "home_team": ["TeamA"] * n,
        "away_team": [f"TeamB_{i}" for i in range(n)],
        "home_odds": rng.uniform(1.5, 3.0, size=n).round(2),
        "away_odds": rng.uniform(1.5, 3.0, size=n).round(2),
        "home_win": rng.integers(0, 2, size=n),
    })


class TestTrainableStrategyProtocol:
    """Tests for TrainableStrategy protocol detection and walk-forward integration."""

    def test_protocol_detected(self):
        """Class with fit + predict is recognized as TrainableStrategy."""
        from cuic_quant.backtest.walk_forward.protocol import TrainableStrategy

        class MyModel:
            def fit(self, train_data: pd.DataFrame) -> None:
                pass
            def predict(self, row: pd.Series, context=None) -> dict:
                return {"action": "SKIP"}

        assert isinstance(MyModel(), TrainableStrategy)

    def test_plain_function_not_detected(self):
        """Regular function is NOT a TrainableStrategy."""
        from cuic_quant.backtest.walk_forward.protocol import TrainableStrategy

        def plain_strategy(row, context=None):
            return {"action": "SKIP"}

        assert not isinstance(plain_strategy, TrainableStrategy)

    def test_fit_called_before_each_fold(self):
        """walk_forward_backtest calls fit() before each fold's backtest."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        fit_calls: list[int] = []

        class TrackingModel:
            def fit(self, train_data: pd.DataFrame) -> None:
                fit_calls.append(len(train_data))

            def predict(self, row: pd.Series, context=None) -> dict:
                return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.5}

        data = _make_wf_data(100)
        model = TrackingModel()
        results = walk_forward_backtest(data, model, n_splits=3)
        # fit() must be called once per non-skipped fold
        n_folds = len(results["splits"])
        assert len(fit_calls) == n_folds, (
            f"fit() called {len(fit_calls)} times but {n_folds} folds ran"
        )
        # Each fit call must have received a positive number of training rows
        assert all(n > 0 for n in fit_calls), (
            f"fit() received empty training data: {fit_calls}"
        )

    def test_trained_model_affects_predictions(self):
        """A model that learns from training data produces different predictions."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        class OddsThresholdModel:
            """Bets home only when odds < mean training odds."""
            def __init__(self):
                self.threshold = 999.0  # untrained: bets on everything

            def fit(self, train_data: pd.DataFrame) -> None:
                self.threshold = float(train_data["home_odds"].mean())

            def predict(self, row: pd.Series, context=None) -> dict:
                if row["home_odds"] < self.threshold:
                    return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.6}
                return {"action": "SKIP"}

        data = _make_wf_data(100)
        model = OddsThresholdModel()
        results = walk_forward_backtest(data, model, n_splits=3)

        # With training, threshold is ~2.25 (mean of uniform 1.5-3.0),
        # so roughly half the bets should be skipped.
        # Without training (threshold=999), ALL bets would be placed.
        total_trades = results["aggregated_metrics"]["total_trades"]
        total_possible = sum(len(s["test_data"]) for s in results["splits"])
        # Trained model should skip SOME bets (not bet on everything)
        assert total_trades < total_possible, (
            f"Model bet on all {total_possible} games — training had no effect"
        )
        assert total_trades > 0, "Model placed zero bets — threshold too restrictive"

    def test_no_future_data_in_fit(self):
        """fit() receives ONLY data chronologically before the test window."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        # Collect (max_train_ts, fold_index) pairs inside fit()
        fit_max_timestamps: dict[int, pd.Timestamp] = {}
        fold_counter = [0]

        class TimestampTracker:
            def fit(self, train_data: pd.DataFrame) -> None:
                idx = fold_counter[0]
                fold_counter[0] += 1
                max_ts = pd.to_datetime(train_data["timestamp"]).max()
                fit_max_timestamps[idx] = max_ts

            def predict(self, row: pd.Series, context=None) -> dict:
                return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.5}

        data = _make_wf_data(100)
        model = TimestampTracker()
        results = walk_forward_backtest(data, model, n_splits=3)

        # For each fold, max training timestamp must be < min test timestamp
        assert len(fit_max_timestamps) == len(results["splits"]), (
            f"fit() called {len(fit_max_timestamps)} times but "
            f"{len(results['splits'])} folds ran"
        )
        for fold_idx, split in enumerate(results["splits"]):
            train_max = fit_max_timestamps[fold_idx]
            test_min = pd.to_datetime(split["test_data"]["timestamp"]).min()
            assert train_max < test_min, (
                f"Fold {fold_idx}: training data max timestamp {train_max} >= "
                f"test start {test_min} — FUTURE DATA LEAKED INTO TRAINING"
            )

    def test_plain_function_still_works(self):
        """Existing always_bet_home works unchanged through walk-forward."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        data = _make_wf_data(100)
        # Should not raise — plain function backward compat
        results = walk_forward_backtest(data, always_bet_home, n_splits=3)
        assert results["aggregated_metrics"]["total_trades"] > 0


class TestWalkForwardDataLeakage:
    """Integration tests verifying walk-forward data isolation end-to-end.

    Complements TestTrainableStrategyProtocol by focusing on data integrity
    rather than protocol mechanics.
    """

    def test_train_test_no_overlap(self):
        """For every fold, assert zero row overlap between train and test."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        data = _make_wf_data(100)
        results = walk_forward_backtest(data, always_bet_home, n_splits=3)

        for split in results["splits"]:
            train_games = set(split["train_data"]["game"].tolist())
            test_games = set(split["test_data"]["game"].tolist())
            overlap = train_games & test_games
            assert len(overlap) == 0, (
                f"Fold {split['fold']}: {len(overlap)} games in both train and test: "
                f"{list(overlap)[:5]}"
            )

    def test_fit_receives_home_win(self):
        """Training data passed to fit() includes home_win (correct for training)."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        received_columns: list[list[str]] = []

        class ColumnTracker:
            def fit(self, train_data: pd.DataFrame) -> None:
                received_columns.append(list(train_data.columns))

            def predict(self, row: pd.Series, context=None) -> dict:
                return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.5}

        data = _make_wf_data(100)
        model = ColumnTracker()
        walk_forward_backtest(data, model, n_splits=3)

        assert len(received_columns) > 0, "fit() was never called"
        for cols in received_columns:
            assert "home_win" in cols, (
                f"Training data missing home_win — columns: {cols}"
            )

    def test_predict_row_no_home_win(self):
        """Rows passed to predict() during backtest do NOT contain home_win."""
        from cuic_quant.backtest.walk_forward import walk_forward_backtest

        predict_columns: list[list[str]] = []

        class RowInspector:
            def fit(self, train_data: pd.DataFrame) -> None:
                pass

            def predict(self, row: pd.Series, context=None) -> dict:
                predict_columns.append(list(row.index))
                return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.5}

        data = _make_wf_data(100)
        model = RowInspector()
        walk_forward_backtest(data, model, n_splits=3)

        assert len(predict_columns) > 0, "predict() was never called"
        for cols in predict_columns:
            assert "home_win" not in cols, (
                f"predict() received home_win — DATA LEAKAGE! columns: {cols}"
            )

    def test_expanding_window_trainable(self):
        """expanding_window_backtest also calls fit() per fold."""
        from cuic_quant.backtest.walk_forward import expanding_window_backtest

        fit_sizes: list[int] = []

        class ExpandTracker:
            def fit(self, train_data: pd.DataFrame) -> None:
                fit_sizes.append(len(train_data))

            def predict(self, row: pd.Series, context=None) -> dict:
                return {"action": "BUY_HOME", "size": 100.0, "confidence": 0.5}

        data = _make_wf_data(100)
        model = ExpandTracker()
        results = expanding_window_backtest(
            data, model, min_train_size=30, step_size=10,
        )

        n_folds = len(results["splits"])
        assert len(fit_sizes) == n_folds, (
            f"fit() called {len(fit_sizes)} times, expected {n_folds}"
        )
        # Expanding window: each fit must receive more data than the previous
        for i in range(1, len(fit_sizes)):
            assert fit_sizes[i] > fit_sizes[i - 1], (
                f"Fold {i} training size {fit_sizes[i]} not larger than "
                f"fold {i-1} size {fit_sizes[i-1]}"
            )
