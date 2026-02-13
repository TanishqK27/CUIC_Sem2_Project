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


class TestBacktest:
    """Tests for the backtest function."""

    def test_returns_nine_columns(self) -> None:
        """Backtest output must have exactly 9 required columns."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            DUMMY_CSV, OUTPUT_COLUMNS,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)
        assert results.columns.tolist() == OUTPUT_COLUMNS

    def test_matches_expected_output(self) -> None:
        """Results must match the known-good dummy_backtest_output.csv exactly."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            DUMMY_CSV, DATA_DIR,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)

        expected_path = DATA_DIR / "dummy_backtest_output.csv"
        expected = pd.read_csv(expected_path, parse_dates=["timestamp"])

        pd.testing.assert_frame_equal(
            results.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )

    def test_skip_strategy_returns_empty_with_columns(self) -> None:
        """A strategy that skips everything should return empty DF with 9 columns."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, load_backtest_data, DUMMY_CSV, OUTPUT_COLUMNS,
        )

        def skip_all(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "SKIP", "confidence": 0, "size": 0}

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, skip_all)

        assert len(results) == 0
        assert results.columns.tolist() == OUTPUT_COLUMNS

    def test_nan_odds_skipped(self) -> None:
        """Rows with NaN odds should be silently skipped."""
        import numpy as np
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        data.loc[2, "home_odds"] = np.nan
        data.loc[5, "away_odds"] = np.nan

        results = backtest(data, always_bet_home)
        assert len(results) == 25 - 2  # 2 rows skipped

    def test_bankroll_stops_at_zero(self) -> None:
        """Backtester should stop when bankroll reaches zero."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, load_backtest_data, DUMMY_CSV,
        )

        def bet_everything(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 1.0, "size": 999999.0}

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, bet_everything, initial_bankroll=100.0)

        # Should stop after first loss at the latest
        assert len(results) <= 25
        assert results["bankroll"].iloc[-1] >= 0

    def test_strategy_does_not_see_home_win(self) -> None:
        """Strategy row must NOT contain home_win (data leakage prevention)."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, load_backtest_data, DUMMY_CSV,
        )

        seen_columns: list[list[str]] = []

        def spy_strategy(row: pd.Series, context: dict | None = None) -> dict:
            seen_columns.append(row.index.tolist())
            return {"action": "SKIP", "confidence": 0, "size": 0}

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        backtest(data, spy_strategy)

        for cols in seen_columns:
            assert "home_win" not in cols, "Strategy received home_win — data leakage!"

    def test_bet_size_capped_at_bankroll(self) -> None:
        """Bet size should never exceed current bankroll."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, load_backtest_data, DUMMY_CSV,
        )

        def big_bet(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "BUY_HOME", "confidence": 1.0, "size": 50000.0}

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, big_bet, initial_bankroll=1000.0)

        # First bet should be capped at 1000
        if len(results) > 0:
            assert results.iloc[0]["bet_size"] <= 1000.0


class TestValidateBacktestResults:
    """Tests for the validate_backtest_results function."""

    def test_valid_results_pass(self) -> None:
        """Known-good results should pass all checks."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)
        report = validate_backtest_results(results, data)

        assert report["passed"] is True
        assert report["checks_passed"] == report["checks_run"]
        assert report["failures"] == []

    def test_wrong_columns_fail(self) -> None:
        """Results with missing columns should fail schema validation."""
        from cuic_quant.backtest.backtester_backend import (
            validate_backtest_results, load_backtest_data, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        bad_results = pd.DataFrame({"wrong": [1, 2, 3]})
        report = validate_backtest_results(bad_results, data)

        assert report["passed"] is False
        assert any("column" in f.lower() for f in report["failures"])

    def test_bad_pnl_math_fails(self) -> None:
        """Results with incorrect PnL calculations should fail."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)

        # Corrupt a PnL value
        corrupted = results.copy()
        corrupted.loc[0, "pnl"] = 999.99
        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any("pnl" in f.lower() for f in report["failures"])

    def test_corrupted_cumulative_pnl_fails(self) -> None:
        """Results with wrong cumulative_pnl should fail."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)

        corrupted = results.copy()
        corrupted.loc[3, "cumulative_pnl"] = 0.0
        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any("cumulative" in f.lower() for f in report["failures"])

    def test_outcome_mismatch_detected(self) -> None:
        """Mismatched outcomes (data leakage indicator) should fail."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)

        # Flip an outcome — this shouldn't match input data
        corrupted = results.copy()
        corrupted.loc[0, "outcome"] = "LOSS"  # Was WIN
        report = validate_backtest_results(corrupted, data)

        assert report["passed"] is False
        assert any("outcome" in f.lower() or "leakage" in f.lower()
                    for f in report["failures"])

    def test_empty_results_pass(self) -> None:
        """Empty results (from a skip-all strategy) should pass validation."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        def skip_all(row: pd.Series, context: dict | None = None) -> dict:
            return {"action": "SKIP", "confidence": 0, "size": 0}

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, skip_all)
        report = validate_backtest_results(results, data)

        assert report["passed"] is True

    def test_report_structure(self) -> None:
        """Report must have exactly the 4 required keys."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data,
            validate_backtest_results, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home)
        report = validate_backtest_results(results, data)

        assert set(report.keys()) == {"passed", "checks_run", "checks_passed", "failures"}
        assert isinstance(report["passed"], bool)
        assert isinstance(report["checks_run"], int)
        assert isinstance(report["checks_passed"], int)
        assert isinstance(report["failures"], list)


class TestPackageExports:
    """Test that the backtest package exports all required functions."""

    def test_all_functions_importable_from_package(self) -> None:
        """All 4 functions should be importable from cuic_quant.backtest."""
        from cuic_quant.backtest import (
            load_backtest_data,
            backtest,
            always_bet_home,
            validate_backtest_results,
        )

        assert callable(load_backtest_data)
        assert callable(backtest)
        assert callable(always_bet_home)
        assert callable(validate_backtest_results)
