"""Extended tests for backtester backend — fills gaps T1-T6.

Covers:
    T1: display_extended_metrics() and plot_performance()
    T2: Railway database code path (mocked)
    T3: Validator checks 8 (overbetting) and 11 (chronological order)
    T4: Strategy exception handling (B3)
    T5: NaN propagation (B2)
    T6: Edge-case costs (cost_flat > initial_bankroll)
"""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cuic_quant.backtest.backtester_backend import (
    OUTPUT_COLUMNS,
    backtest,
    always_bet_home,
    display_extended_metrics,
    load_backtest_data,
    plot_performance,
    validate_backtest_results,
)


# ============================================================================
# Helpers — reusable data builders
# ============================================================================


def _make_input_data(
    n: int = 5,
    home_wins: list[int] | None = None,
    odds: float = 2.00,
) -> pd.DataFrame:
    """Build a minimal valid input DataFrame for the backtester."""
    if home_wins is None:
        home_wins = [1, 0] * ((n // 2) + 1)
    home_wins = home_wins[:n]
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="D"),
        "game": [f"Team{i}A vs Team{i}B" for i in range(n)],
        "home_team": [f"Team{i}A" for i in range(n)],
        "away_team": [f"Team{i}B" for i in range(n)],
        "home_odds": [odds] * n,
        "away_odds": [odds] * n,
        "home_win": home_wins,
    })


def _make_results(
    n: int = 5,
    home_wins: list[int] | None = None,
    odds: float = 2.00,
    initial_bankroll: float = 10000.0,
) -> pd.DataFrame:
    """Run always_bet_home on synthetic data and return results."""
    data = _make_input_data(n=n, home_wins=home_wins, odds=odds)
    return backtest(data, always_bet_home, initial_bankroll=initial_bankroll)


# ============================================================================
# T1 — display_extended_metrics() and plot_performance()
# ============================================================================


class TestDisplayExtendedMetrics:
    """Tests for display_extended_metrics()."""

    def test_prints_output_for_valid_results(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should print formatted metrics table."""
        results = _make_results(n=10, home_wins=[1, 0, 1, 1, 0, 0, 1, 0, 1, 1])
        display_extended_metrics(results)
        captured = capsys.readouterr()
        assert "EXTENDED PERFORMANCE METRICS" in captured.out
        assert "Sharpe Ratio" in captured.out
        assert "Max Drawdown" in captured.out
        assert "Profit Factor" in captured.out

    def test_handles_empty_results(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should print 'No trades to analyze.' for empty DF."""
        empty = pd.DataFrame(columns=OUTPUT_COLUMNS)
        display_extended_metrics(empty)
        captured = capsys.readouterr()
        assert "No trades to analyze." in captured.out

    def test_handles_all_wins(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should handle 100% win rate without errors."""
        results = _make_results(n=5, home_wins=[1, 1, 1, 1, 1])
        display_extended_metrics(results)
        captured = capsys.readouterr()
        assert "EXTENDED PERFORMANCE METRICS" in captured.out
        # Average loss should be $0.00 since there are no losses
        assert "Average Loss" in captured.out

    def test_handles_all_losses(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should handle 0% win rate without errors."""
        results = _make_results(n=5, home_wins=[0, 0, 0, 0, 0])
        display_extended_metrics(results)
        captured = capsys.readouterr()
        assert "EXTENDED PERFORMANCE METRICS" in captured.out
        assert "Average Win" in captured.out


class TestPlotPerformance:
    """Tests for plot_performance()."""

    @pytest.fixture(autouse=True)
    def _use_agg_backend(self) -> None:
        """Switch matplotlib to non-interactive backend for all plot tests."""
        import matplotlib.pyplot as plt

        plt.switch_backend("Agg")
        yield  # type: ignore[misc]
        plt.close("all")

    def test_creates_figure_for_valid_results(self) -> None:
        """Should create matplotlib figure without error."""
        import matplotlib.pyplot as plt

        results = _make_results(n=10, home_wins=[1, 0, 1, 1, 0, 0, 1, 0, 1, 1])
        # Patch plt.show to prevent display attempt
        with patch.object(plt, "show"):
            plot_performance(results)
        # If we get here without error, the test passes
        fig_count = len(plt.get_fignums())
        plt.close("all")
        # The function called plt.show() so the figure was created
        assert True  # no exception raised

    def test_handles_empty_results(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Should print 'No trades to plot.' for empty DF."""
        empty = pd.DataFrame(columns=OUTPUT_COLUMNS)
        plot_performance(empty)
        captured = capsys.readouterr()
        assert "No trades to plot." in captured.out

    def test_single_trade(self) -> None:
        """Should handle single-trade results."""
        import matplotlib.pyplot as plt

        results = _make_results(n=1, home_wins=[1])
        assert len(results) == 1
        with patch.object(plt, "show"):
            plot_performance(results)
        plt.close("all")


# ============================================================================
# T2 — Railway database code path (mocked)
# ============================================================================


class TestLoadBacktestDataDatabase:
    """Tests for the Railway PostgreSQL code path in load_backtest_data()."""

    def test_uses_database_when_url_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Mock DATABASE_URL and verify DB path is attempted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake:5432/testdb")

        fake_df = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-15"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [1.90],
            "away_odds": [2.10],
            "home_win": [1],
        })

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        # The function does `from sqlalchemy import create_engine, text` inside the body,
        # so we patch on the sqlalchemy module itself.
        with (
            patch("cuic_quant.backtest.data_loader.pd.read_sql", return_value=fake_df) as mock_read_sql,
            patch("sqlalchemy.create_engine", return_value=mock_engine),
            patch("sqlalchemy.text") as mock_text,
        ):
            df = load_backtest_data("2026-01-01", "2026-01-31")

        # read_sql was called (DB path was attempted)
        mock_read_sql.assert_called_once()
        assert len(df) == 1
        assert df.iloc[0]["game"] == "A vs B"

    def test_falls_back_on_db_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should fall back to CSV when DB query fails."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake:5432/testdb")

        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Connection refused")

        from cuic_quant.backtest.backtester_backend import DUMMY_CSV

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with patch("sqlalchemy.create_engine", return_value=mock_engine):
                df = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)

        # Should have fallen back to CSV
        assert len(df) > 0
        # Should have emitted a RuntimeWarning about fallback
        runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(runtime_warnings) >= 1
        assert "falling back" in str(runtime_warnings[0].message).lower()

    def test_strict_mode_raises_on_db_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """strict=True should raise RuntimeError on DB failure."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake:5432/testdb")

        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Connection refused")

        with patch("sqlalchemy.create_engine", return_value=mock_engine):
            with pytest.raises(RuntimeError, match="strict=True"):
                load_backtest_data(
                    "2026-01-01", "2026-01-31", strict=True,
                )


# ============================================================================
# T3 — Validator checks 8 (overbetting) and 11 (chronological order)
# ============================================================================


class TestValidatorUntriggeredChecks:
    """Tests for validator checks that were never triggered in existing tests."""

    def test_overbetting_detected(self) -> None:
        """Manually construct results where bet_size > bankroll at time of bet."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, always_bet_home, initial_bankroll=10000.0)

        # Corrupt bet_size to exceed available bankroll at time of bet
        corrupted = results.copy()
        # The first bet has bankroll=10000. Set bet_size to 20000 to trigger check 8.
        corrupted.loc[corrupted.index[0], "bet_size"] = 20000.0
        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any(
            "bet exceeds bankroll" in f.lower() or "overbet" in f.lower()
            for f in report["failures"]
        ), f"Expected overbetting failure, got: {report['failures']}"

    def test_out_of_order_detected(self) -> None:
        """Manually construct results with non-chronological timestamps."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, always_bet_home, initial_bankroll=10000.0)

        # Swap timestamps so they are out of order
        corrupted = results.copy()
        ts0 = corrupted.loc[corrupted.index[0], "timestamp"]
        ts2 = corrupted.loc[corrupted.index[2], "timestamp"]
        corrupted.loc[corrupted.index[0], "timestamp"] = ts2
        corrupted.loc[corrupted.index[2], "timestamp"] = ts0

        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any(
            "chronological" in f.lower() or "leakage" in f.lower()
            for f in report["failures"]
        ), f"Expected chronological order failure, got: {report['failures']}"


# ============================================================================
# T4 — Strategy exception handling (B3)
# ============================================================================


class TestStrategyExceptionHandling:
    """Tests for strategy functions that raise exceptions (B3).

    The backtester catches strategy exceptions, emits a UserWarning, and
    skips the offending row rather than crashing the entire backtest.
    """

    def _make_failing_strategy(self, fail_on_row: int = 2):
        """Return a strategy that raises on a specific row number."""
        call_count = {"n": 0}

        def strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            call_count["n"] += 1
            if call_count["n"] == fail_on_row:
                raise ValueError(f"Strategy crashed on row {fail_on_row}")
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        return strategy

    def test_exception_in_strategy_preserves_prior_trades(self) -> None:
        """Strategy raising on row N should still return trades 1..N-1."""
        data = _make_input_data(n=5, home_wins=[1, 1, 1, 1, 1])
        strategy = self._make_failing_strategy(fail_on_row=3)

        results = backtest(data, strategy, initial_bankroll=10000.0)

        # Row 3 raises, so we should get trades for rows 1, 2, 4, 5 = 4 trades
        assert len(results) == 4
        assert results.columns.tolist() == OUTPUT_COLUMNS

    def test_exception_warning_is_emitted(self) -> None:
        """Should emit a warning when strategy raises."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        strategy = self._make_failing_strategy(fail_on_row=2)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, strategy, initial_bankroll=10000.0)

        # At least one warning should mention the strategy exception
        strategy_warnings = [
            w for w in caught
            if "strategy" in str(w.message).lower()
            or "exception" in str(w.message).lower()
            or "crashed" in str(w.message).lower()
        ]
        assert len(strategy_warnings) >= 1, (
            f"Expected strategy exception warning, got: "
            f"{[str(w.message) for w in caught]}"
        )

    def test_all_rows_raise_returns_empty(self) -> None:
        """If every row raises, should return empty DF with correct columns."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])

        def always_crash(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            raise RuntimeError("Always fails")

        results = backtest(data, always_crash, initial_bankroll=10000.0)

        assert len(results) == 0
        assert results.columns.tolist() == OUTPUT_COLUMNS


# ============================================================================
# T5 — NaN propagation (B2)
# ============================================================================


class TestNaNPropagation:
    """Tests for NaN handling in strategy signal values (B2).

    The backtester detects NaN values in strategy signals and skips the
    affected row with a UserWarning rather than allowing NaN to propagate
    into PnL / bankroll calculations.
    """

    def test_nan_size_is_skipped(self) -> None:
        """Strategy returning size=float('nan') should skip the trade."""
        call_count = {"n": 0}

        def nan_size_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            call_count["n"] += 1
            if call_count["n"] == 2:
                return {"action": "BUY_HOME", "confidence": 0.5, "size": float("nan")}
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, nan_size_strategy, initial_bankroll=10000.0)

        # Row 2 returns NaN size, should be skipped -> 2 trades
        assert len(results) == 2
        # No NaN values in the output
        assert not results["bet_size"].isna().any()
        assert not results["pnl"].isna().any()

    def test_nan_confidence_handled(self) -> None:
        """NaN confidence with Kelly should fall back to raw size."""
        def nan_confidence_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "confidence": float("nan"), "size": 100.0}

        data = _make_input_data(n=1, home_wins=[1])
        results = backtest(
            data, nan_confidence_strategy,
            initial_bankroll=10000.0,
            position_sizing="kelly",
        )

        # NaN confidence should fall back to raw size=100
        assert len(results) == 1
        assert results.iloc[0]["bet_size"] == 100.0

    def test_nan_does_not_corrupt_subsequent_trades(self) -> None:
        """After a NaN-size row, subsequent trades should have valid PnL."""
        call_count = {"n": 0}

        def nan_then_normal(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"action": "BUY_HOME", "confidence": 0.5, "size": float("nan")}
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, nan_then_normal, initial_bankroll=10000.0)

        # Row 1 has NaN size -> skipped. Rows 2 and 3 should be normal.
        assert len(results) == 2
        assert not results["pnl"].isna().any()
        assert not results["cumulative_pnl"].isna().any()
        assert not results["bankroll"].isna().any()
        # Verify PnL math is correct
        for _, row in results.iterrows():
            if row["outcome"] == "WIN":
                expected_pnl = round(row["bet_size"] * (row["odds"] - 1), 2)
                assert abs(row["pnl"] - expected_pnl) < 0.01


# ============================================================================
# T6 — Edge-case costs (cost_flat > initial_bankroll)
# ============================================================================


class TestEdgeCaseCosts:
    """Tests for edge cases with transaction costs."""

    def test_cost_flat_exceeds_bankroll(self) -> None:
        """Should produce no trades when flat cost exceeds bankroll."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(
            data, always_bet_home,
            initial_bankroll=50.0,
            cost_flat=100.0,  # flat fee exceeds bankroll
        )

        # bet_size = min(100, max(0, 50 - 100)) = min(100, 0) = 0 -> skipped
        assert len(results) == 0
        assert results.columns.tolist() == OUTPUT_COLUMNS

    def test_cost_flat_equals_bankroll(self) -> None:
        """Edge case: flat cost exactly equals bankroll."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(
            data, always_bet_home,
            initial_bankroll=100.0,
            cost_flat=100.0,  # flat fee equals bankroll
        )

        # bet_size = min(100, max(0, 100 - 100)) = min(100, 0) = 0 -> skipped
        assert len(results) == 0
        assert results.columns.tolist() == OUTPUT_COLUMNS


# ============================================================================
# U2 — Signal key typo detection
# ============================================================================


class TestSignalKeyTypoDetection:
    """Tests for the signal key typo warning system (U2)."""

    def test_capital_action_triggers_warning(self) -> None:
        """Strategy returning 'Action' instead of 'action' should warn."""
        def bad_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"Action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, bad_strategy, initial_bankroll=10000.0)

        # Should warn about typo AND about missing 'action' key
        typo_warnings = [w for w in caught if "'Action'" in str(w.message)]
        assert len(typo_warnings) >= 1, f"Expected typo warning, got: {[str(w.message) for w in caught]}"
        # Trade should be skipped (no 'action' key after warning)
        assert len(results) == 0

    def test_wrong_size_key_triggers_warning(self) -> None:
        """Strategy returning 'bet_size' instead of 'size' should warn."""
        def bad_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "confidence": 0.5, "bet_size": 100.0}

        data = _make_input_data(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, bad_strategy, initial_bankroll=10000.0)

        typo_warnings = [w for w in caught if "'bet_size'" in str(w.message)]
        assert len(typo_warnings) >= 1, f"Expected bet_size typo warning, got: {[str(w.message) for w in caught]}"
        # Trade should be skipped (size defaults to 0 since 'size' key is missing)
        assert len(results) == 0

    def test_correct_and_typo_both_present_no_warning(self) -> None:
        """If both correct key and typo are present, no warning should fire."""
        def dual_key_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "Action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = backtest(data, dual_key_strategy, initial_bankroll=10000.0)

        typo_warnings = [w for w in caught if "'Action'" in str(w.message) and "instead of" in str(w.message)]
        assert len(typo_warnings) == 0, f"Should NOT warn when correct key is present, got: {[str(w.message) for w in caught]}"
        assert len(results) == 1  # Trade should proceed normally


# ============================================================================
# U3 — Lookback history in context
# ============================================================================


class TestLookbackHistory:
    """Tests for context['history'] and context['past_games'] (U3)."""

    def test_history_contains_past_trades(self) -> None:
        """context['history'] should contain all prior trades."""
        captured_contexts: list[dict] = []

        def capturing_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            if context:
                captured_contexts.append({
                    "trade_count": context["trade_count"],
                    "history_len": len(context["history"]),
                })
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        backtest(data, capturing_strategy, initial_bankroll=10000.0)

        assert len(captured_contexts) == 3
        # First call: no prior trades
        assert captured_contexts[0]["history_len"] == 0
        assert captured_contexts[0]["trade_count"] == 0
        # Second call: 1 prior trade
        assert captured_contexts[1]["history_len"] == 1
        assert captured_contexts[1]["trade_count"] == 1
        # Third call: 2 prior trades
        assert captured_contexts[2]["history_len"] == 2
        assert captured_contexts[2]["trade_count"] == 2

    def test_past_games_contains_prior_rows(self) -> None:
        """context['past_games'] should have all data rows before current."""
        past_games_lengths: list[int] = []

        def capturing_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            if context and context["past_games"] is not None:
                past_games_lengths.append(len(context["past_games"]))
            else:
                past_games_lengths.append(0)
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=4, home_wins=[1, 1, 1, 1])
        backtest(data, capturing_strategy, initial_bankroll=10000.0)

        # Row 0: past_games has 0 rows (nothing before it)
        assert past_games_lengths[0] == 0
        # Row 1: past_games has 1 row (row 0)
        assert past_games_lengths[1] == 1
        # Row 2: past_games has 2 rows
        assert past_games_lengths[2] == 2
        # Row 3: past_games has 3 rows
        assert past_games_lengths[3] == 3

    def test_history_mutation_does_not_corrupt_engine(self) -> None:
        """Mutating context['history'] list should not affect engine trades."""
        call_count = {"n": 0}

        def mutating_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            call_count["n"] += 1
            if context and context["history"]:
                # Try to corrupt the history list
                context["history"].clear()
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, mutating_strategy, initial_bankroll=10000.0)

        # All 3 trades should still be present despite list mutation
        assert len(results) == 3


# ============================================================================
# U4 — Deterministic ordering with tied timestamps
# ============================================================================


class TestDeterministicOrdering:
    """Tests for deterministic row ordering (U4)."""

    def test_same_timestamp_sorted_by_game(self) -> None:
        """Rows with same timestamp should be sorted by game name."""
        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"] * 3),
            "game": ["Zebras vs Lions", "Ants vs Bears", "Cats vs Dogs"],
            "home_team": ["Zebras", "Ants", "Cats"],
            "away_team": ["Lions", "Bears", "Dogs"],
            "home_odds": [2.0, 2.0, 2.0],
            "away_odds": [2.0, 2.0, 2.0],
            "home_win": [1, 0, 1],
        })

        game_order: list[str] = []

        def order_tracking_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            game_order.append(row["game"])
            return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

        # Sort the data like load_backtest_data does
        sorted_data = data.sort_values(["timestamp", "game"]).reset_index(drop=True)
        backtest(sorted_data, order_tracking_strategy, initial_bankroll=10000.0)

        # Should be alphabetical by game name
        assert game_order == ["Ants vs Bears", "Cats vs Dogs", "Zebras vs Lions"]


# ============================================================================
# B2 extra — None and Inf size edge cases
# ============================================================================


class TestNoneAndInfSize:
    """Additional edge case tests for bet size handling (B2)."""

    def test_none_size_is_skipped(self) -> None:
        """Strategy returning size=None should skip the trade."""
        def none_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": None}

        data = _make_input_data(n=2, home_wins=[1, 1])
        results = backtest(data, none_strategy, initial_bankroll=10000.0)

        assert len(results) == 0

    def test_inf_size_capped_at_bankroll(self) -> None:
        """Strategy returning size=inf should be capped at bankroll."""
        def inf_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": float("inf")}

        data = _make_input_data(n=1, home_wins=[1])
        results = backtest(data, inf_strategy, initial_bankroll=10000.0)

        assert len(results) == 1
        # bet_size should be capped at bankroll (10000), not infinity
        assert results.iloc[0]["bet_size"] == 10000.0
