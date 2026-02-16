# Backtester Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract all backtester logic from the Jupyter notebook into an importable Python module with full validation, then rewrite the notebook as a thin caller.

**Architecture:** Functional approach — four standalone functions in one file (`backtester_backend.py`). The notebook imports and calls them. No classes, no state objects. Same function signatures as the current notebook so downstream consumers (Ben's metrics, Ismaeel's tests) are unaffected.

**Tech Stack:** Python 3.10+, pandas, SQLAlchemy (for DB loading), pytest

---

## Task 1: Create `backtester_backend.py` with `always_bet_home`

Start with the simplest function to establish the file and verify imports work.

**Files:**
- Create: `src/cuic_quant/backtest/backtester_backend.py`
- Test: `tests/test_backtester_backend.py`

**Step 1: Write the failing test**

Create `tests/test_backtester_backend.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtester_backend.py::TestAlwaysBetHome -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cuic_quant.backtest.backtester_backend'`

**Step 3: Write minimal implementation**

Create `src/cuic_quant/backtest/backtester_backend.py`:

```python
"""Backtester backend module for the CUIC Quant Fund sports betting backtester.

This module contains all core backtesting functions extracted from the
tools/backtester.ipynb notebook. It provides:

- Data loading from Railway PostgreSQL or local CSV fallback
- Core backtesting loop that evaluates strategy functions against historical data
- Example strategy implementation for testing
- Validation suite to verify backtest results are correct and leak-free

Why this exists:
    The backtester logic was originally defined inline in a Jupyter notebook,
    making it impossible to import from other modules (e.g., Ben's metrics,
    Ismaeel's tests). This module makes the backtester importable and testable.

How to use:
    from cuic_quant.backtest.backtester_backend import (
        load_backtest_data, backtest, always_bet_home, validate_backtest_results,
    )

    data = load_backtest_data("2026-01-01", "2026-01-31")
    results = backtest(data, always_bet_home)
    report = validate_backtest_results(results, data)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_COLUMNS = [
    "timestamp", "game", "action", "bet_size",
    "odds", "outcome", "pnl", "cumulative_pnl", "bankroll",
]
"""The 9 required columns in backtester output. This is the contract that
downstream consumers (Ben's metrics module, Ismaeel's tests) depend on.
Do NOT remove or rename columns without coordinating per
docs/SOPs/modularity-upgrades.md."""

VALID_ACTIONS = {"BUY_HOME", "BUY_AWAY", "SKIP"}
"""Actions a strategy function may return."""

VALID_OUTCOMES = {"WIN", "LOSS"}
"""Possible trade outcomes."""

# Project root detection: works whether imported from src/ or tools/
_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent.parent.parent  # src/cuic_quant/backtest -> project root
DATA_DIR = PROJECT_ROOT / "data"
DUMMY_CSV = DATA_DIR / "dummy_backtest_input.csv"
TEST_CSV = DATA_DIR / "test_games.csv"


# ---------------------------------------------------------------------------
# Example strategy
# ---------------------------------------------------------------------------


def always_bet_home(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Example strategy that always bets $100 on the home team.

    What: A naive strategy that unconditionally backs the home team
    for every game, regardless of odds or context.

    Why: This exists as a reference implementation of the strategy interface
    (see docs/reference/strategy-interface.md). It is used to validate
    that the backtester produces correct output — since the strategy is
    deterministic, we can verify results against a known-good CSV.

    How: Ignores all inputs and returns a fixed signal dict with
    action='BUY_HOME', confidence=0.5, and size=100.

    Args:
        row: Game data row with home_odds, away_odds, etc.
            Must NOT contain home_win (the backtester strips it).
        context: Optional dict from the backtester with current state
            (bankroll, trade_count, cumulative_pnl). Ignored by this strategy.

    Returns:
        Signal dict conforming to the strategy interface:
        - action: 'BUY_HOME'
        - confidence: 0.5
        - size: 100.0
        - reason: Human-readable explanation
    """
    return {
        "action": "BUY_HOME",
        "confidence": 0.5,
        "size": 100.0,
        "reason": "Always bet home (test strategy)",
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_backtester_backend.py::TestAlwaysBetHome -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py tests/test_backtester_backend.py
git commit -m "feat(backtest): create backtester_backend.py with always_bet_home strategy"
```

---

## Task 2: Add `load_backtest_data` function

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py`
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write the failing tests**

Append to `tests/test_backtester_backend.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_backtester_backend.py::TestLoadBacktestData -v`
Expected: FAIL — `ImportError: cannot import name 'load_backtest_data'`

**Step 3: Write the implementation**

Add to `backtester_backend.py` (after the constants, before `always_bet_home`):

```python
def load_backtest_data(
    start_date: str,
    end_date: str,
    csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load historical game data for backtesting.

    What: Loads a DataFrame of completed games with odds and outcomes,
    filtered to a date range and sorted chronologically.

    Why: The backtester needs historical game data to simulate strategy
    performance. This function abstracts the data source — it tries the
    Railway PostgreSQL database first (production), then falls back to a
    local CSV file (development/testing).

    How:
        1. Check if DATABASE_URL environment variable is set.
        2. If yes, query the sportsbook_matches + sportsbook_odds tables
           via SQLAlchemy, filter by date range, return sorted DataFrame.
        3. If no (or if the DB query fails), load from a local CSV file.
        4. Filter the CSV by date range, sort by timestamp, return.

    Args:
        start_date: Start of date range, inclusive. Format: "YYYY-MM-DD".
        end_date: End of date range, inclusive. Format: "YYYY-MM-DD".
        csv_path: Path to fallback CSV file. If None, defaults to
            data/dummy_backtest_input.csv.

    Returns:
        DataFrame with columns: timestamp (datetime), game (str),
        home_team (str), away_team (str), home_odds (float),
        away_odds (float), home_win (int: 1 or 0).
        Sorted by timestamp ascending.

    Raises:
        FileNotFoundError: If no database is available and no CSV exists
            at the specified path.
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(database_url)
            query = text("""
                SELECT
                    m.commence_time AS timestamp,
                    m.home_team || ' vs ' || m.away_team AS game,
                    m.home_team,
                    m.away_team,
                    o.home_odds,
                    o.away_odds,
                    m.home_win
                FROM sportsbook_matches m
                JOIN sportsbook_odds o ON m.id = o.match_id
                WHERE m.commence_time >= :start_date
                  AND m.commence_time <= :end_date
                ORDER BY m.commence_time ASC
            """)

            with engine.connect() as conn:
                df = pd.read_sql(
                    query, conn,
                    params={"start_date": start_date, "end_date": end_date},
                )

            df["timestamp"] = pd.to_datetime(df["timestamp"])
            print(f"Loaded {len(df)} rows from Railway database.")
            return df

        except Exception as e:
            print(f"Database connection failed ({e}), falling back to CSV.")

    # Fallback to CSV
    if csv_path is None:
        csv_path = DUMMY_CSV
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"No CSV found at {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # Filter by date range
    mask = (df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)
    df = df.loc[mask].sort_values("timestamp").reset_index(drop=True)

    print(f"Loaded {len(df)} rows from {csv_path.name}.")
    return df
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_backtester_backend.py::TestLoadBacktestData -v`
Expected: 5 passed (or 4 passed + 1 skipped if test_games.csv missing)

**Step 5: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py tests/test_backtester_backend.py
git commit -m "feat(backtest): add load_backtest_data function with DB and CSV support"
```

---

## Task 3: Add `backtest` function

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py`
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write the failing tests**

Append to `tests/test_backtester_backend.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_backtester_backend.py::TestBacktest -v`
Expected: FAIL — `ImportError: cannot import name 'backtest'`

**Step 3: Write the implementation**

Add to `backtester_backend.py` (after `load_backtest_data`, before `always_bet_home`):

```python
def backtest(
    data: pd.DataFrame,
    strategy_fn: Callable[[pd.Series, dict[str, Any] | None], dict[str, Any]],
    initial_bankroll: float = 10000.0,
) -> pd.DataFrame:
    """Run a backtest over historical game data using a strategy function.

    What: Simulates betting on historical games by iterating through each row,
    calling the strategy function for a signal, and tracking the bankroll,
    profit/loss, and trade history.

    Why: This is the core engine that every strategy in the CUIC Quant Fund
    is evaluated through. It provides a standardized way to measure strategy
    performance on historical data before risking real money.

    How:
        1. Initialize bankroll and empty trade list.
        2. For each game row (sorted by timestamp):
           a. Skip rows with NaN odds (data quality guard).
           b. Strip home_win from the row before passing to strategy
              (prevents data leakage — the strategy must not know outcomes).
           c. Call strategy_fn(row, context) to get a signal.
           d. If signal is SKIP or size <= 0, skip to next row.
           e. Cap bet_size at current bankroll.
           f. Determine outcome: compare action vs home_win.
           g. Calculate PnL: WIN = bet_size * (odds - 1), LOSS = -bet_size.
           h. Update cumulative_pnl and bankroll.
           i. Append trade to list.
        3. Return trades as a DataFrame with exactly 9 columns.

    Args:
        data: DataFrame from load_backtest_data() with columns: timestamp,
            game, home_team, away_team, home_odds, away_odds, home_win.
        strategy_fn: Callable matching the strategy interface
            (see docs/reference/strategy-interface.md). Takes
            (row: pd.Series, context: dict | None) and returns a dict with
            keys: action, confidence, size, reason (optional).
        initial_bankroll: Starting bankroll in dollars. Defaults to 10000.

    Returns:
        DataFrame with 9 columns: timestamp, game, action, bet_size, odds,
        outcome, pnl, cumulative_pnl, bankroll. Returns empty DataFrame with
        correct columns if no trades are executed.
    """
    bankroll = initial_bankroll
    cumulative_pnl = 0.0
    trades: list[dict[str, Any]] = []

    context: dict[str, Any] = {
        "initial_bankroll": initial_bankroll,
        "bankroll": bankroll,
        "trade_count": 0,
        "cumulative_pnl": 0.0,
    }

    for _, row in data.iterrows():
        if bankroll <= 0:
            break

        # Skip rows with NaN odds (prevents corruption of subsequent rows)
        if pd.isna(row["home_odds"]) or pd.isna(row["away_odds"]):
            continue

        # Update context for strategy
        context["bankroll"] = bankroll
        context["trade_count"] = len(trades)
        context["cumulative_pnl"] = cumulative_pnl

        # Remove outcome column to prevent data leakage
        strategy_row = row.drop(labels=["home_win"])
        signal = strategy_fn(strategy_row, context)
        action = signal.get("action", "SKIP")

        if action == "SKIP":
            continue

        # Determine bet size (cap at current bankroll)
        bet_size = min(signal.get("size", 0.0), bankroll)
        if bet_size <= 0:
            continue

        # Determine odds based on action
        if action == "BUY_HOME":
            odds = row["home_odds"]
            won = row["home_win"] == 1
        elif action == "BUY_AWAY":
            odds = row["away_odds"]
            won = row["home_win"] == 0
        else:
            continue  # Invalid action, skip

        # Calculate P&L
        if won:
            pnl = bet_size * (odds - 1)
            outcome = "WIN"
        else:
            pnl = -bet_size
            outcome = "LOSS"

        cumulative_pnl += pnl
        bankroll += pnl

        trades.append({
            "timestamp": row["timestamp"],
            "game": row["game"],
            "action": action,
            "bet_size": round(bet_size, 2),
            "odds": odds,
            "outcome": outcome,
            "pnl": round(pnl, 2),
            "cumulative_pnl": round(cumulative_pnl, 2),
            "bankroll": round(bankroll, 2),
        })

    # Return DataFrame with correct columns even if empty
    if not trades:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return pd.DataFrame(trades)[OUTPUT_COLUMNS]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_backtester_backend.py::TestBacktest -v`
Expected: 7 passed

**Step 5: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py tests/test_backtester_backend.py
git commit -m "feat(backtest): add backtest function with leakage prevention and edge case handling"
```

---

## Task 4: Add `validate_backtest_results` function

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py`
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write the failing tests**

Append to `tests/test_backtester_backend.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_backtester_backend.py::TestValidateBacktestResults -v`
Expected: FAIL — `ImportError: cannot import name 'validate_backtest_results'`

**Step 3: Write the implementation**

Add to `backtester_backend.py` (after `always_bet_home`):

```python
def validate_backtest_results(
    results: pd.DataFrame,
    input_data: pd.DataFrame,
    initial_bankroll: float = 10000.0,
) -> dict[str, Any]:
    """Validate backtest results for correctness and data leakage.

    What: Runs a comprehensive suite of checks on backtest output to
    verify schema compliance, mathematical correctness, and absence
    of data leakage.

    Why: Backtester bugs can silently produce wrong results — inflated
    win rates, incorrect PnL, or outcomes that could only be known
    through future data leakage. This function catches those errors
    before anyone draws conclusions from bad data.

    How: Runs three categories of checks:
        1. Schema validation — correct columns, types, and value domains.
        2. Math correctness — PnL formulas, running sums, bankroll tracking.
        3. Data leakage detection — outcome consistency with input data,
           chronological ordering, game existence verification.
        Returns a report dict summarizing pass/fail status.

    Args:
        results: DataFrame output from backtest() with 9 columns.
        input_data: The original DataFrame passed to backtest(), used to
            cross-reference outcomes and verify game existence.
        initial_bankroll: The initial_bankroll value used in the backtest.
            Needed to verify bankroll column calculations.

    Returns:
        Dict with keys:
        - passed (bool): True if ALL checks pass.
        - checks_run (int): Total number of checks executed.
        - checks_passed (int): Number of checks that passed.
        - failures (list[str]): Descriptions of each failed check.
    """
    failures: list[str] = []
    checks_run = 0

    # --- Handle empty results ---
    if len(results) == 0:
        checks_run += 1
        if results.columns.tolist() == OUTPUT_COLUMNS:
            return {
                "passed": True,
                "checks_run": checks_run,
                "checks_passed": checks_run,
                "failures": [],
            }
        else:
            failures.append(
                f"Schema: empty results have wrong columns. "
                f"Expected {OUTPUT_COLUMNS}, got {results.columns.tolist()}"
            )
            return {
                "passed": False,
                "checks_run": checks_run,
                "checks_passed": 0,
                "failures": failures,
            }

    # ===================================================================
    # Category 1: Schema Validation
    # ===================================================================

    # Check 1: Column names
    checks_run += 1
    if results.columns.tolist() != OUTPUT_COLUMNS:
        failures.append(
            f"Schema: column mismatch. "
            f"Expected {OUTPUT_COLUMNS}, got {results.columns.tolist()}"
        )

    # Check 2: Actions are valid
    checks_run += 1
    invalid_actions = set(results["action"].unique()) - {"BUY_HOME", "BUY_AWAY"}
    if invalid_actions:
        failures.append(f"Schema: invalid actions found: {invalid_actions}")

    # Check 3: Outcomes are valid
    checks_run += 1
    invalid_outcomes = set(results["outcome"].unique()) - VALID_OUTCOMES
    if invalid_outcomes:
        failures.append(f"Schema: invalid outcomes found: {invalid_outcomes}")

    # Check 4: Bet sizes positive
    checks_run += 1
    if (results["bet_size"] <= 0).any():
        failures.append("Schema: found non-positive bet_size values")

    # ===================================================================
    # Category 2: Math Correctness
    # ===================================================================

    # Check 5: PnL calculations
    checks_run += 1
    pnl_errors = []
    for idx, row in results.iterrows():
        if row["outcome"] == "WIN":
            expected_pnl = round(row["bet_size"] * (row["odds"] - 1), 2)
        else:
            expected_pnl = round(-row["bet_size"], 2)

        if abs(row["pnl"] - expected_pnl) > 0.01:
            pnl_errors.append(
                f"Row {idx}: pnl={row['pnl']}, expected={expected_pnl}"
            )

    if pnl_errors:
        failures.append(
            f"Math: incorrect pnl calculations in {len(pnl_errors)} rows. "
            f"First: {pnl_errors[0]}"
        )

    # Check 6: Cumulative PnL is running sum
    checks_run += 1
    running_sum = 0.0
    cum_pnl_errors = []
    for idx, row in results.iterrows():
        running_sum = round(running_sum + row["pnl"], 2)
        if abs(row["cumulative_pnl"] - running_sum) > 0.01:
            cum_pnl_errors.append(
                f"Row {idx}: cumulative_pnl={row['cumulative_pnl']}, "
                f"expected={running_sum}"
            )

    if cum_pnl_errors:
        failures.append(
            f"Math: incorrect cumulative_pnl in {len(cum_pnl_errors)} rows. "
            f"First: {cum_pnl_errors[0]}"
        )

    # Check 7: Bankroll = initial + cumulative_pnl
    checks_run += 1
    bankroll_errors = []
    for idx, row in results.iterrows():
        expected_bankroll = round(initial_bankroll + row["cumulative_pnl"], 2)
        if abs(row["bankroll"] - expected_bankroll) > 0.01:
            bankroll_errors.append(
                f"Row {idx}: bankroll={row['bankroll']}, "
                f"expected={expected_bankroll}"
            )

    if bankroll_errors:
        failures.append(
            f"Math: incorrect bankroll in {len(bankroll_errors)} rows. "
            f"First: {bankroll_errors[0]}"
        )

    # Check 8: No bet exceeds bankroll at time of bet
    checks_run += 1
    prev_bankroll = initial_bankroll
    overbet_errors = []
    for idx, row in results.iterrows():
        if row["bet_size"] > prev_bankroll + 0.01:
            overbet_errors.append(
                f"Row {idx}: bet_size={row['bet_size']}, "
                f"bankroll_at_time={prev_bankroll}"
            )
        prev_bankroll = row["bankroll"]

    if overbet_errors:
        failures.append(
            f"Math: bet exceeds bankroll in {len(overbet_errors)} rows. "
            f"First: {overbet_errors[0]}"
        )

    # ===================================================================
    # Category 3: Data Leakage Detection
    # ===================================================================

    # Check 9: Every game in results exists in input data
    checks_run += 1
    result_games = set(results["game"].unique())
    input_games = set(input_data["game"].unique())
    missing_games = result_games - input_games
    if missing_games:
        failures.append(
            f"Leakage: {len(missing_games)} games in results not found in "
            f"input data: {list(missing_games)[:3]}"
        )

    # Check 10: Outcomes match input data
    checks_run += 1
    outcome_errors = []
    for idx, row in results.iterrows():
        matching_input = input_data[input_data["game"] == row["game"]]
        if len(matching_input) == 0:
            continue  # Already caught by check 9

        input_row = matching_input.iloc[0]
        if row["action"] == "BUY_HOME":
            expected_outcome = "WIN" if input_row["home_win"] == 1 else "LOSS"
        elif row["action"] == "BUY_AWAY":
            expected_outcome = "WIN" if input_row["home_win"] == 0 else "LOSS"
        else:
            continue

        if row["outcome"] != expected_outcome:
            outcome_errors.append(
                f"Row {idx} ({row['game']}): outcome={row['outcome']}, "
                f"expected={expected_outcome} based on home_win={input_row['home_win']}"
            )

    if outcome_errors:
        failures.append(
            f"Leakage: outcome mismatch in {len(outcome_errors)} rows. "
            f"First: {outcome_errors[0]}"
        )

    # Check 11: Trades in chronological order
    checks_run += 1
    timestamps = pd.to_datetime(results["timestamp"])
    if not timestamps.is_monotonic_increasing:
        failures.append(
            "Leakage: trades are not in chronological order "
            "(possible future data access)"
        )

    # --- Build report ---
    checks_passed = checks_run - len(failures)
    return {
        "passed": len(failures) == 0,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "failures": failures,
    }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_backtester_backend.py::TestValidateBacktestResults -v`
Expected: 7 passed

**Step 5: Run ALL tests together**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: 21 passed (2 + 5 + 7 + 7)

**Step 6: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py tests/test_backtester_backend.py
git commit -m "feat(backtest): add validate_backtest_results with schema, math, and leakage checks"
```

---

## Task 5: Update `__init__.py` exports

**Files:**
- Modify: `src/cuic_quant/backtest/__init__.py`

**Step 1: Write a failing test**

Append to `tests/test_backtester_backend.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtester_backend.py::TestPackageExports -v`
Expected: FAIL — `ImportError: cannot import name 'load_backtest_data' from 'cuic_quant.backtest'`

**Step 3: Update `__init__.py`**

Replace the contents of `src/cuic_quant/backtest/__init__.py` with:

```python
"""Backtesting framework for strategy validation.

This module provides tools for:
- Loading historical game data from database or CSV
- Running strategies against historical data
- Validating backtest results for correctness and data leakage

Usage:
    from cuic_quant.backtest import backtest, load_backtest_data, validate_backtest_results

    data = load_backtest_data("2026-01-01", "2026-01-31")
    results = backtest(data, my_strategy)
    report = validate_backtest_results(results, data)
"""

from cuic_quant.backtest.backtester_backend import (
    always_bet_home,
    backtest,
    load_backtest_data,
    validate_backtest_results,
)

__all__ = [
    "always_bet_home",
    "backtest",
    "load_backtest_data",
    "validate_backtest_results",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_backtester_backend.py::TestPackageExports -v`
Expected: PASS

**Step 5: Run full test suite to check nothing broke**

Run: `pytest tests/ -v`
Expected: All existing tests + new tests pass

**Step 6: Commit**

```bash
git add src/cuic_quant/backtest/__init__.py tests/test_backtester_backend.py
git commit -m "feat(backtest): export all functions from backtest package __init__"
```

---

## Task 6: Rewrite `tools/backtester.ipynb` as thin caller

**Files:**
- Overwrite: `tools/backtester.ipynb`

**Step 1: Rewrite the notebook**

The notebook should contain NO function definitions. All logic is imported from `backtester_backend`. Structure:

- **Cell 0** (markdown): Title, owner, version, description, output format table
- **Cell 1** (code): Imports + path setup
- **Cell 2** (markdown): "Configuration"
- **Cell 3** (code): Config variables (PROJECT_ROOT, DATA_DIR, csv paths)
- **Cell 4** (markdown): "Load Data"
- **Cell 5** (code): `data = load_backtest_data(...)`, preview
- **Cell 6** (markdown): "Strategy" — explain how to swap strategies
- **Cell 7** (code): Import `always_bet_home` (or define a custom one here)
- **Cell 8** (markdown): "Run Backtest"
- **Cell 9** (code): `results = backtest(data, always_bet_home)`, display
- **Cell 10** (markdown): "Summary Statistics"
- **Cell 11** (code): Win rate, PnL, ROI calculations
- **Cell 12** (markdown): "Validate Results"
- **Cell 13** (code): `report = validate_backtest_results(results, data)`, display
- **Cell 14** (markdown): "Test with Mya's Data"
- **Cell 15** (code): Load test_games.csv, run backtest, validate

**Key cell contents:**

Cell 1 (code):
```python
import sys
from pathlib import Path

# Ensure src/ is importable from the tools/ directory
PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "tools":
    PROJECT_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cuic_quant.backtest import (
    load_backtest_data,
    backtest,
    always_bet_home,
    validate_backtest_results,
)
```

Cell 3 (code):
```python
DATA_DIR = PROJECT_ROOT / "data"
DUMMY_CSV = DATA_DIR / "dummy_backtest_input.csv"
TEST_CSV = DATA_DIR / "test_games.csv"
```

Cell 5 (code):
```python
data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
print(f"Games loaded: {len(data)}")
data.head()
```

Cell 7 (code):
```python
# Using the built-in test strategy.
# To use your own strategy, define it here or import it:
#
#   def my_strategy(row, context=None):
#       return {"action": "BUY_HOME", "confidence": 0.8, "size": 50.0}
#
# See docs/reference/strategy-interface.md for the full contract.
strategy = always_bet_home
```

Cell 9 (code):
```python
results = backtest(data, strategy, initial_bankroll=10000.0)
print(f"Total trades: {len(results)}")
results
```

Cell 11 (code):
```python
if len(results) > 0:
    wins = (results["outcome"] == "WIN").sum()
    losses = (results["outcome"] == "LOSS").sum()
    win_rate = wins / len(results)
    final_pnl = results["cumulative_pnl"].iloc[-1]
    final_bankroll = results["bankroll"].iloc[-1]

    print(f"Win Rate:        {win_rate:.1%} ({wins}W / {losses}L)")
    print(f"Total P&L:       ${final_pnl:,.2f}")
    print(f"Final Bankroll:  ${final_bankroll:,.2f}")
    print(f"ROI:             {final_pnl / 10000:.1%}")
else:
    print("No trades executed.")
```

Cell 13 (code):
```python
report = validate_backtest_results(results, data)

if report["passed"]:
    print(f"PASSED: {report['checks_passed']}/{report['checks_run']} checks passed")
else:
    print(f"FAILED: {report['checks_passed']}/{report['checks_run']} checks passed")
    for f in report["failures"]:
        print(f"  - {f}")
```

Cell 15 (code):
```python
if TEST_CSV.exists():
    mya_data = load_backtest_data("2026-01-01", "2026-12-31", csv_path=TEST_CSV)
    mya_results = backtest(mya_data, strategy, initial_bankroll=10000.0)
    mya_report = validate_backtest_results(mya_results, mya_data)

    print(f"Mya's data: {len(mya_results)} trades")
    print(f"Validation: {'PASSED' if mya_report['passed'] else 'FAILED'}")
    print(f"Checks: {mya_report['checks_passed']}/{mya_report['checks_run']}")
else:
    print(f"test_games.csv not found at {TEST_CSV}")
```

**Step 2: Verify the notebook runs end-to-end**

Run from project root: `jupyter nbconvert --to notebook --execute tools/backtester.ipynb --output /dev/null`
Or manually open in Jupyter and Run All.

Expected: All cells execute, validation passes, no errors.

**Step 3: Commit**

```bash
git add tools/backtester.ipynb
git commit -m "refactor(backtest): rewrite notebook as thin caller importing from backtester_backend"
```

---

## Task 7: Final integration test — run everything

**Step 1: Run full pytest suite**

Run: `pytest tests/ -v`
Expected: All tests pass (existing strategy tests + new backtester tests)

**Step 2: Verify imports work from project root**

Run: `python -c "from cuic_quant.backtest import backtest, load_backtest_data, validate_backtest_results; print('All imports OK')"`
Expected: "All imports OK"

**Step 3: Verify notebook runs cleanly**

Open `tools/backtester.ipynb` in Jupyter and Run All. Verify:
- Data loads (25 rows from dummy CSV)
- Backtest runs (25 trades)
- Validation passes (all checks)
- Mya's data works too (100 rows)

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "test(backtest): verify full integration of backtester refactor"
```
