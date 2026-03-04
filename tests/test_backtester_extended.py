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
        """Should create matplotlib figure with 4 subplots."""
        import matplotlib.pyplot as plt

        results = _make_results(n=10, home_wins=[1, 0, 1, 1, 0, 0, 1, 0, 1, 1])
        # Patch plt.show to prevent display attempt
        with patch.object(plt, "show"):
            plot_performance(results)
        # Verify a figure was actually created with subplots
        fig_nums = plt.get_fignums()
        assert len(fig_nums) > 0, "plot_performance should create at least one figure"
        fig = plt.figure(fig_nums[-1])
        axes = fig.get_axes()
        assert len(axes) >= 2, f"Expected at least 2 subplots, got {len(axes)}"
        plt.close("all")

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

    def test_schema_mismatch_falls_back_to_csv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DB query raising ProgrammingError (missing column) should fall back to CSV."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake:5432/testdb")

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        from cuic_quant.backtest.backtester_backend import DUMMY_CSV

        # Simulate ProgrammingError from missing closing_home_odds column
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with (
                patch("cuic_quant.backtest.data_loader.pd.read_sql",
                      side_effect=Exception('column "closing_home_odds" does not exist')),
                patch("sqlalchemy.create_engine", return_value=mock_engine),
                patch("sqlalchemy.text"),
            ):
                df = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)

        assert len(df) > 0  # Fell back to CSV
        runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(runtime_warnings) >= 1
        assert "falling back" in str(runtime_warnings[0].message).lower()


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
        # The first bet has bankroll=10000. Set bet_size to 20000 to trigger check 9.
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

    def test_check5_invalid_odds_detected(self) -> None:
        """Manually corrupt odds to <= 1.0 to trigger Check 5 (valid odds)."""
        data = _make_input_data(n=3, home_wins=[1, 1, 1])
        results = backtest(data, always_bet_home, initial_bankroll=10000.0)

        corrupted = results.copy()
        corrupted.loc[corrupted.index[0], "odds"] = 0.9  # invalid: <= 1.0

        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any(
            "odds" in f.lower() for f in report["failures"]
        ), f"Expected odds failure, got: {report['failures']}"


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

    def test_inf_size_skipped_with_warning(self) -> None:
        """Strategy returning size=inf should be skipped with a UserWarning (strict policy)."""
        def inf_strategy(row: Any, ctx: Any = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 0.5, "size": float("inf")}
        data = _make_input_data(n=1, home_wins=[1])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = backtest(data, inf_strategy, initial_bankroll=10000.0)
        assert len(results) == 0
        user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert any("size" in str(uw.message).lower() for uw in user_warnings)


# ============================================================================
# M1 — Kelly growth rate metric
# ============================================================================


class TestKellyGrowthRate:
    """Tests for calculate_kelly_growth_rate (M1 fix)."""

    def test_positive_growth_on_wins(self) -> None:
        """All-win backtest should have positive Kelly growth rate."""
        from cuic_quant.metrics import calculate_kelly_growth_rate

        results = _make_results(n=5, home_wins=[1, 1, 1, 1, 1], odds=2.00)
        rate = calculate_kelly_growth_rate(results)
        assert rate > 0, f"Expected positive growth rate, got {rate}"

    def test_negative_growth_on_losses(self) -> None:
        """All-loss backtest should have negative Kelly growth rate."""
        from cuic_quant.metrics import calculate_kelly_growth_rate

        results = _make_results(n=5, home_wins=[0, 0, 0, 0, 0], odds=2.00)
        rate = calculate_kelly_growth_rate(results)
        assert rate < 0, f"Expected negative growth rate, got {rate}"

    def test_zero_on_empty(self) -> None:
        """Empty results should return 0."""
        from cuic_quant.metrics import calculate_kelly_growth_rate

        empty = pd.DataFrame(columns=OUTPUT_COLUMNS)
        assert calculate_kelly_growth_rate(empty) == 0.0

    def test_included_in_calculate_all_metrics(self) -> None:
        """kelly_growth_rate should appear in calculate_all_metrics output."""
        from cuic_quant.metrics import calculate_all_metrics

        results = _make_results(n=5, home_wins=[1, 0, 1, 1, 0])
        metrics = calculate_all_metrics(results)
        assert "kelly_growth_rate" in metrics
        assert isinstance(metrics["kelly_growth_rate"], float)


# ============================================================================
# M2 — CLV (Closing Line Value) metric
# ============================================================================


class TestCLV:
    """Tests for CLV infrastructure and calculate_clv (M2 fix)."""

    def test_closing_odds_in_output_with_input(self) -> None:
        """Output should have closing_odds when input has closing odds columns."""
        data = _make_input_data(n=3, home_wins=[1, 0, 1])
        data["closing_home_odds"] = [1.85, 2.10, 1.90]
        data["closing_away_odds"] = [2.10, 1.85, 2.10]

        results = backtest(data, always_bet_home, initial_bankroll=10000.0)
        assert "closing_odds" in results.columns
        # Since we bet BUY_HOME, closing_odds = closing_home_odds
        assert results.iloc[0]["closing_odds"] == 1.85
        assert results.iloc[1]["closing_odds"] == 2.10

    def test_closing_odds_nan_without_input(self) -> None:
        """Output should have closing_odds=NaN when input lacks closing odds."""
        data = _make_input_data(n=2, home_wins=[1, 0])
        results = backtest(data, always_bet_home, initial_bankroll=10000.0)
        assert "closing_odds" in results.columns
        assert results["closing_odds"].isna().all()

    def test_clv_positive_when_better_price(self) -> None:
        """CLV should be positive when bet odds > closing odds (got better price)."""
        from cuic_quant.metrics import calculate_clv

        results = pd.DataFrame({
            "odds": [2.00, 1.90, 2.10],
            "closing_odds": [1.85, 1.80, 2.00],  # closing < opening
        })
        clv = calculate_clv(results)
        assert clv > 0, f"Expected positive CLV, got {clv}"

    def test_clv_negative_when_worse_price(self) -> None:
        """CLV should be negative when bet odds < closing odds (got worse price)."""
        from cuic_quant.metrics import calculate_clv

        results = pd.DataFrame({
            "odds": [1.80, 1.85, 1.90],
            "closing_odds": [1.95, 2.00, 2.05],  # closing > opening
        })
        clv = calculate_clv(results)
        assert clv < 0, f"Expected negative CLV, got {clv}"

    def test_clv_nan_without_column(self) -> None:
        """CLV should be NaN when closing_odds column is missing."""
        from cuic_quant.metrics import calculate_clv
        import math

        results = pd.DataFrame({"odds": [2.0], "pnl": [100.0]})
        assert math.isnan(calculate_clv(results))

    def test_clv_in_calculate_all_metrics(self) -> None:
        """CLV should appear in calculate_all_metrics when closing_odds present."""
        from cuic_quant.metrics import calculate_all_metrics
        from cuic_quant.backtest.backtester_backend import load_backtest_data, DUMMY_CSV

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)
        metrics = calculate_all_metrics(results)
        assert "clv" in metrics


# ============================================================================
# M4 — Confidence in DataFrame + Brier Score / Log Loss
# ============================================================================


class TestConfidenceInOutput:
    """Tests for confidence column in output DataFrame (M4 fix)."""

    def test_confidence_stored_in_dataframe(self) -> None:
        """Confidence should be a proper column, not just in attrs."""
        results = _make_results(n=3, home_wins=[1, 0, 1])
        assert "confidence" in results.columns
        # always_bet_home returns confidence=0.5
        assert (results["confidence"] == 0.5).all()

    def test_confidence_nan_when_not_provided(self) -> None:
        """Strategies that don't return confidence should have NaN."""
        def no_conf_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            return {"action": "BUY_HOME", "size": 100.0}

        data = _make_input_data(n=2, home_wins=[1, 1])
        results = backtest(data, no_conf_strategy, initial_bankroll=10000.0)
        assert "confidence" in results.columns
        assert results["confidence"].isna().all()

    def test_mixed_confidence_values(self) -> None:
        """Some trades with confidence, some without."""
        call_count = {"n": 0}

        def mixed_strategy(row: pd.Series, context: dict[str, Any] | None = None) -> dict[str, Any]:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"action": "BUY_HOME", "confidence": 0.7, "size": 100.0}
            return {"action": "BUY_HOME", "size": 100.0}  # no confidence

        data = _make_input_data(n=2, home_wins=[1, 1])
        results = backtest(data, mixed_strategy, initial_bankroll=10000.0)
        assert results.iloc[0]["confidence"] == 0.7
        assert pd.isna(results.iloc[1]["confidence"])


class TestBrierScore:
    """Tests for calculate_brier_score (M4 fix)."""

    def test_perfect_predictions(self) -> None:
        """Perfect confidence = perfect predictions -> Brier = 0."""
        from cuic_quant.metrics import calculate_brier_score

        results = pd.DataFrame({
            "confidence": [1.0, 0.0, 1.0],
            "outcome": ["WIN", "LOSS", "WIN"],
        })
        brier = calculate_brier_score(results)
        assert abs(brier) < 1e-10

    def test_worst_predictions(self) -> None:
        """Completely wrong predictions -> Brier = 1.0."""
        from cuic_quant.metrics import calculate_brier_score

        results = pd.DataFrame({
            "confidence": [0.0, 1.0, 0.0],
            "outcome": ["WIN", "LOSS", "WIN"],
        })
        brier = calculate_brier_score(results)
        assert abs(brier - 1.0) < 1e-10

    def test_random_predictions(self) -> None:
        """p=0.5 for all -> Brier = 0.25."""
        from cuic_quant.metrics import calculate_brier_score

        results = pd.DataFrame({
            "confidence": [0.5, 0.5, 0.5, 0.5],
            "outcome": ["WIN", "LOSS", "WIN", "LOSS"],
        })
        brier = calculate_brier_score(results)
        assert abs(brier - 0.25) < 1e-10

    def test_nan_without_confidence(self) -> None:
        """Should return NaN when confidence column missing."""
        from cuic_quant.metrics import calculate_brier_score
        import math

        results = pd.DataFrame({"outcome": ["WIN", "LOSS"]})
        assert math.isnan(calculate_brier_score(results))

    def test_in_calculate_all_metrics(self) -> None:
        """brier_score should appear in calculate_all_metrics output."""
        from cuic_quant.metrics import calculate_all_metrics

        results = _make_results(n=5, home_wins=[1, 0, 1, 1, 0])
        metrics = calculate_all_metrics(results)
        assert "brier_score" in metrics


class TestLogLoss:
    """Tests for calculate_log_loss (M4 fix)."""

    def test_random_predictions(self) -> None:
        """p=0.5 for all -> Log Loss ≈ 0.693 (ln(2))."""
        from cuic_quant.metrics import calculate_log_loss
        import math

        results = pd.DataFrame({
            "confidence": [0.5, 0.5, 0.5, 0.5],
            "outcome": ["WIN", "LOSS", "WIN", "LOSS"],
        })
        ll = calculate_log_loss(results)
        assert abs(ll - math.log(2)) < 1e-10

    def test_good_predictions_lower_than_random(self) -> None:
        """Good predictions should have lower log loss than random."""
        from cuic_quant.metrics import calculate_log_loss

        good = pd.DataFrame({
            "confidence": [0.8, 0.2, 0.9, 0.1],
            "outcome": ["WIN", "LOSS", "WIN", "LOSS"],
        })
        random_pred = pd.DataFrame({
            "confidence": [0.5, 0.5, 0.5, 0.5],
            "outcome": ["WIN", "LOSS", "WIN", "LOSS"],
        })
        assert calculate_log_loss(good) < calculate_log_loss(random_pred)

    def test_nan_without_confidence(self) -> None:
        """Should return NaN when confidence column missing."""
        from cuic_quant.metrics import calculate_log_loss
        import math

        results = pd.DataFrame({"outcome": ["WIN", "LOSS"]})
        assert math.isnan(calculate_log_loss(results))

    def test_in_calculate_all_metrics(self) -> None:
        """log_loss should appear in calculate_all_metrics output."""
        from cuic_quant.metrics import calculate_all_metrics

        results = _make_results(n=5, home_wins=[1, 0, 1, 1, 0])
        metrics = calculate_all_metrics(results)
        assert "log_loss" in metrics
