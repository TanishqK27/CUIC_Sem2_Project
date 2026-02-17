# Backtester Missing Criteria Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add transaction cost modeling, Kelly criterion integration, notebook documentation, and edge case tests to the backtester.

**Architecture:** Extend the existing `backtest()` function with optional parameters (`cost_pct`, `cost_flat`, `position_sizing`, `kelly_fraction`) that default to current behavior. Add a Kelly-aware example strategy. Update the validator to support cost parameters. Improve notebook documentation and test coverage.

**Tech Stack:** Python 3.10+, pandas, matplotlib, pytest

---

### Task 1: Transaction Costs — Failing Tests

**Files:**
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write failing tests for transaction costs**

Add these tests to `tests/test_backtester_backend.py` inside a new test class:

```python
class TestTransactionCosts:
    """Tests for transaction cost modeling."""

    def test_cost_pct_reduces_win_pnl(self) -> None:
        """A 5% cost_pct should reduce winning PnL by 5%."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(data, always_bet_home, cost_pct=0.05)
        # WIN pnl = 100 * (2.0 - 1) * (1 - 0.05) - 0 = 95.0
        assert results.iloc[0]["pnl"] == 95.0

    def test_cost_flat_deducted_from_every_trade(self) -> None:
        """A $2 flat fee should be deducted from every trade."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "game": ["A vs B", "C vs D"],
            "home_team": ["A", "C"],
            "away_team": ["B", "D"],
            "home_odds": [2.00, 2.00],
            "away_odds": [2.00, 2.00],
            "home_win": [1, 0],
        })

        results = backtest(data, always_bet_home, cost_flat=2.0)
        # WIN: 100 * (2.0 - 1) * 1.0 - 2.0 = 98.0
        assert results.iloc[0]["pnl"] == 98.0
        # LOSS: -100 - 2.0 = -102.0
        assert results.iloc[1]["pnl"] == -102.0

    def test_both_costs_combined(self) -> None:
        """Both cost_pct and cost_flat should apply together."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [3.00],
            "away_odds": [1.50],
            "home_win": [1],
        })

        results = backtest(data, always_bet_home, cost_pct=0.10, cost_flat=1.0)
        # WIN: 100 * (3.0 - 1) * (1 - 0.10) - 1.0 = 200 * 0.9 - 1 = 179.0
        assert results.iloc[0]["pnl"] == 179.0

    def test_zero_costs_match_original_behavior(self) -> None:
        """Default costs (0, 0) should produce identical results to no-cost backtest."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data, DUMMY_CSV,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results_default = backtest(data, always_bet_home)
        results_zero = backtest(data, always_bet_home, cost_pct=0.0, cost_flat=0.0)

        pd.testing.assert_frame_equal(results_default, results_zero)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_backtester_backend.py::TestTransactionCosts -v`
Expected: FAIL — `backtest()` does not accept `cost_pct` or `cost_flat`

**Step 3: Commit failing tests**

```bash
git add tests/test_backtester_backend.py
git commit -m "test: add failing tests for transaction cost modeling"
```

---

### Task 2: Transaction Costs — Implementation

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py` (lines 166-285)

**Step 1: Add cost parameters to `backtest()` signature**

Change the function signature at line 166:

```python
def backtest(
    data: pd.DataFrame,
    strategy_fn: Callable[[pd.Series, dict[str, Any] | None], dict[str, Any]],
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
) -> pd.DataFrame:
```

**Step 2: Update the PnL calculation block**

Replace the PnL calculation block (lines 259-265) with:

```python
        # Calculate P&L (round immediately so stored and accumulated values match)
        if won:
            pnl = round(bet_size * (odds - 1) * (1 - cost_pct) - cost_flat, 2)
            outcome = "WIN"
        else:
            pnl = round(-bet_size - cost_flat, 2)
            outcome = "LOSS"
```

**Step 3: Update the docstring**

Add to the Args section of `backtest()`:

```
        cost_pct: Percentage deducted from winning payouts (e.g. 0.02 for 2%).
            Models bookmaker vig/margin. Default 0.0 (no cost).
        cost_flat: Flat dollar fee deducted per trade regardless of outcome.
            Default 0.0 (no fee).
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_backtester_backend.py::TestTransactionCosts -v`
Expected: 4 PASSED

**Step 5: Run ALL existing tests to verify no regressions**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: All tests PASS (defaults preserve original behavior)

**Step 6: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py
git commit -m "feat: add transaction cost modeling to backtest()"
```

---

### Task 3: Update Validator for Costs

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py` (lines 345-622)
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write failing test for validator with costs**

Add to `TestValidateBacktestResults`:

```python
    def test_validates_results_with_costs(self) -> None:
        """Validator should pass when cost params match the backtest."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, validate_backtest_results,
        )

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "game": ["A vs B", "C vs D"],
            "home_team": ["A", "C"],
            "away_team": ["B", "D"],
            "home_odds": [2.00, 2.00],
            "away_odds": [2.00, 2.00],
            "home_win": [1, 0],
        })

        results = backtest(data, always_bet_home, cost_pct=0.05, cost_flat=1.0)
        report = validate_backtest_results(results, data, cost_pct=0.05, cost_flat=1.0)
        assert report["passed"] is True, f"Failures: {report['failures']}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtester_backend.py::TestValidateBacktestResults::test_validates_results_with_costs -v`
Expected: FAIL — `validate_backtest_results()` does not accept cost params

**Step 3: Add cost params to validator**

Update `validate_backtest_results` signature (line 345):

```python
def validate_backtest_results(
    results: pd.DataFrame,
    input_data: pd.DataFrame,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
) -> dict[str, Any]:
```

Update the PnL check (around line 486-491) to use costs:

```python
    for idx, row in results.iterrows():
        if row["outcome"] == "WIN":
            expected_pnl = round(row["bet_size"] * (row["odds"] - 1) * (1 - cost_pct) - cost_flat, 2)
        else:
            expected_pnl = round(-row["bet_size"] - cost_flat, 2)
```

**Step 4: Run tests**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py tests/test_backtester_backend.py
git commit -m "feat: update validator to support transaction cost params"
```

---

### Task 4: Kelly Criterion — Failing Tests

**Files:**
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write failing tests for Kelly sizing**

Add a new test class:

```python
class TestKellySizing:
    """Tests for Kelly criterion position sizing."""

    def test_kelly_sizing_uses_confidence(self) -> None:
        """When position_sizing='kelly', bet size should use strategy confidence."""
        from cuic_quant.backtest.backtester_backend import backtest

        def confident_strategy(row, context=None):
            return {"action": "BUY_HOME", "confidence": 0.6, "size": 100.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(
            data, confident_strategy,
            initial_bankroll=10000.0,
            position_sizing="kelly",
            kelly_fraction=1.0,
        )

        # Kelly fraction for p=0.6, odds=2.0: (0.6*2 - 0.4)/2 = 0.8/2 = 0.2 (but capped at 0.25 by default max)
        # But calculate_kelly_fraction(0.6, 2.0, 1.0, 0.25) = min(0.2, 0.25) = 0.2
        # Bet size = 0.2 * 10000 = 2000
        assert results.iloc[0]["bet_size"] == 2000.0

    def test_kelly_no_confidence_falls_back_to_size(self) -> None:
        """Without confidence field, should fall back to strategy's size."""
        from cuic_quant.backtest.backtester_backend import backtest

        def no_confidence_strategy(row, context=None):
            return {"action": "BUY_HOME", "size": 50.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(
            data, no_confidence_strategy,
            position_sizing="kelly",
        )

        assert results.iloc[0]["bet_size"] == 50.0

    def test_kelly_half_kelly_fraction(self) -> None:
        """Half-Kelly should halve the bet size."""
        from cuic_quant.backtest.backtester_backend import backtest

        def confident_strategy(row, context=None):
            return {"action": "BUY_HOME", "confidence": 0.6, "size": 100.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        full = backtest(data, confident_strategy, position_sizing="kelly", kelly_fraction=1.0)
        half = backtest(data, confident_strategy, position_sizing="kelly", kelly_fraction=0.5)

        assert half.iloc[0]["bet_size"] == full.iloc[0]["bet_size"] / 2

    def test_kelly_negative_edge_skips(self) -> None:
        """Kelly should return 0 for negative edge (confidence too low), skipping the bet."""
        from cuic_quant.backtest.backtester_backend import backtest

        def low_confidence(row, context=None):
            return {"action": "BUY_HOME", "confidence": 0.3, "size": 100.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(data, low_confidence, position_sizing="kelly")
        # Kelly for p=0.3, odds=2.0: (0.3*2 - 0.7)/2 = -0.1/2 = -0.05 -> clamped to 0
        assert len(results) == 0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_backtester_backend.py::TestKellySizing -v`
Expected: FAIL — `backtest()` does not accept `position_sizing`

**Step 3: Commit**

```bash
git add tests/test_backtester_backend.py
git commit -m "test: add failing tests for Kelly criterion sizing"
```

---

### Task 5: Kelly Criterion — Implementation

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py`

**Step 1: Add Kelly params to `backtest()` signature**

```python
def backtest(
    data: pd.DataFrame,
    strategy_fn: Callable[[pd.Series, dict[str, Any] | None], dict[str, Any]],
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    position_sizing: str | None = None,
    kelly_fraction: float = 0.5,
) -> pd.DataFrame:
```

**Step 2: Add Kelly sizing logic**

After the bet_size determination block (after line 245), add Kelly logic:

```python
        # Apply Kelly position sizing if enabled
        if position_sizing == "kelly":
            confidence = signal.get("confidence")
            if confidence is not None and 0 < confidence < 1:
                from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction
                kelly_size = calculate_kelly_fraction(
                    win_probability=confidence,
                    decimal_odds=odds,
                    kelly_fraction=kelly_fraction,
                )
                bet_size = round(kelly_size * bankroll, 2)
                if bet_size <= 0:
                    continue
```

Note: This block must go AFTER we know the `odds` value (after the action/odds determination block), but BEFORE the PnL calculation. The bet_size cap at bankroll already happens earlier, but Kelly already accounts for this since it's a fraction of bankroll. Still cap it:

```python
        bet_size = min(bet_size, bankroll)
        if bet_size <= 0:
            continue
```

**Step 3: Update docstring**

Add to Args:

```
        position_sizing: Position sizing method. None = use strategy's size field,
            "kelly" = Kelly Criterion sizing using strategy's confidence as
            win probability. Default None.
        kelly_fraction: Fraction of Kelly to use when position_sizing="kelly".
            0.5 = half-Kelly (safer), 1.0 = full Kelly. Default 0.5.
```

**Step 4: Run tests**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: All PASS including new Kelly tests

**Step 5: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py
git commit -m "feat: add Kelly criterion position sizing to backtest()"
```

---

### Task 6: Kelly Example Strategy

**Files:**
- Modify: `src/cuic_quant/backtest/backtester_backend.py`
- Modify: `src/cuic_quant/backtest/__init__.py`
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write failing test**

Add to `TestAlwaysBetHome` or create new class:

```python
class TestKellyBetHome:
    """Tests for the kelly_bet_home example strategy."""

    def test_returns_buy_home_action(self) -> None:
        from cuic_quant.backtest import kelly_bet_home

        row = pd.Series({"home_odds": 1.95, "away_odds": 2.05})
        signal = kelly_bet_home(row)
        assert signal["action"] == "BUY_HOME"

    def test_confidence_based_on_odds(self) -> None:
        from cuic_quant.backtest import kelly_bet_home

        row = pd.Series({"home_odds": 1.50, "away_odds": 2.80})
        signal = kelly_bet_home(row)
        # Implied prob = 1/1.50 = 0.667, with 5% edge = 0.717 capped at 0.95
        assert 0 < signal["confidence"] < 1

    def test_works_with_kelly_sizing(self) -> None:
        from cuic_quant.backtest import kelly_bet_home, backtest

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(data, kelly_bet_home, position_sizing="kelly")
        assert len(results) == 1
        assert results.iloc[0]["bet_size"] > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtester_backend.py::TestKellyBetHome -v`
Expected: FAIL — `kelly_bet_home` not found

**Step 3: Implement `kelly_bet_home`**

Add to `backtester_backend.py` after `always_bet_away`:

```python
def kelly_bet_home(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Example strategy that bets on home team with confidence based on odds.

    Uses implied probability from odds plus a small edge (5%) as the
    confidence value. Designed to work with position_sizing="kelly" in
    backtest() for Kelly Criterion bet sizing.

    Args:
        row: Game data row with home_odds, away_odds, etc.
        context: Optional dict from backtester with current state.

    Returns:
        Signal dict with action, confidence, size, and reason.
    """
    implied_prob = 1.0 / row["home_odds"]
    confidence = min(implied_prob + 0.05, 0.95)
    return {
        "action": "BUY_HOME",
        "confidence": confidence,
        "size": 100.0,
        "reason": f"Kelly home bet (implied={implied_prob:.2f}, conf={confidence:.2f})",
    }
```

**Step 4: Export from `__init__.py`**

Add `kelly_bet_home` to imports and `__all__` in `src/cuic_quant/backtest/__init__.py`.

**Step 5: Run tests**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/cuic_quant/backtest/backtester_backend.py src/cuic_quant/backtest/__init__.py tests/test_backtester_backend.py
git commit -m "feat: add kelly_bet_home example strategy"
```

---

### Task 7: Edge Case Tests

**Files:**
- Modify: `tests/test_backtester_backend.py`

**Step 1: Write all edge case tests**

Add a new test class:

```python
class TestEdgeCases:
    """Edge case tests for financial extremes."""

    def test_extreme_high_odds(self) -> None:
        """Odds of 100.0 should produce correct large PnL."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [100.0],
            "away_odds": [1.01],
            "home_win": [1],
        })

        results = backtest(data, always_bet_home)
        assert results.iloc[0]["pnl"] == round(100.0 * (100.0 - 1), 2)  # 9900.0

    def test_extreme_low_odds(self) -> None:
        """Odds of 1.001 should produce tiny payout that rounds correctly."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [1.001],
            "away_odds": [100.0],
            "home_win": [1],
        })

        results = backtest(data, always_bet_home)
        assert results.iloc[0]["pnl"] == round(100.0 * (1.001 - 1), 2)  # 0.1

    def test_zero_initial_bankroll(self) -> None:
        """Zero bankroll should produce no trades."""
        from cuic_quant.backtest.backtester_backend import (
            backtest, always_bet_home, load_backtest_data, DUMMY_CSV, OUTPUT_COLUMNS,
        )

        data = load_backtest_data("2026-01-01", "2026-01-31", csv_path=DUMMY_CSV)
        results = backtest(data, always_bet_home, initial_bankroll=0.0)
        assert len(results) == 0
        assert results.columns.tolist() == OUTPUT_COLUMNS

    def test_invalid_action_string_skipped(self) -> None:
        """Strategy returning an invalid action should be skipped."""
        from cuic_quant.backtest.backtester_backend import backtest

        def bad_strategy(row, context=None):
            return {"action": "INVALID_ACTION", "confidence": 0.5, "size": 100.0}

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "game": ["A vs B"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_odds": [2.00],
            "away_odds": [2.00],
            "home_win": [1],
        })

        results = backtest(data, bad_strategy)
        assert len(results) == 0

    def test_all_wins_bankroll_grows(self) -> None:
        """All-win sequence should grow bankroll correctly."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "game": ["A vs B", "C vs D", "E vs F"],
            "home_team": ["A", "C", "E"],
            "away_team": ["B", "D", "F"],
            "home_odds": [2.00, 2.00, 2.00],
            "away_odds": [2.00, 2.00, 2.00],
            "home_win": [1, 1, 1],
        })

        results = backtest(data, always_bet_home, initial_bankroll=1000.0)
        assert len(results) == 3
        assert all(results["outcome"] == "WIN")
        # Each bet wins $100: bankroll = 1000 + 100 + 100 + 100 = 1300
        assert results.iloc[-1]["bankroll"] == 1300.0

    def test_all_losses_bankroll_shrinks(self) -> None:
        """All-loss sequence should reduce bankroll correctly."""
        from cuic_quant.backtest.backtester_backend import backtest, always_bet_home

        data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "game": ["A vs B", "C vs D", "E vs F"],
            "home_team": ["A", "C", "E"],
            "away_team": ["B", "D", "F"],
            "home_odds": [2.00, 2.00, 2.00],
            "away_odds": [2.00, 2.00, 2.00],
            "home_win": [0, 0, 0],
        })

        results = backtest(data, always_bet_home, initial_bankroll=1000.0)
        assert len(results) == 3
        assert all(results["outcome"] == "LOSS")
        # Each bet loses $100: bankroll = 1000 - 100 - 100 - 100 = 700
        assert results.iloc[-1]["bankroll"] == 700.0
```

**Step 2: Run tests**

Run: `pytest tests/test_backtester_backend.py::TestEdgeCases -v`
Expected: All PASS (these test existing behavior, no code changes needed)

**Step 3: Commit**

```bash
git add tests/test_backtester_backend.py
git commit -m "test: add edge case tests for financial extremes"
```

---

### Task 8: Notebook Documentation Fixes

**Files:**
- Modify: `tools/backtester.ipynb`

**Step 1: Fix strategy inconsistency**

Update cell-6 markdown — change "always_bet_home" reference to match code, OR change cell-7 code to `strategy = always_bet_home`. Per design doc: switch to `always_bet_home` since it has the known-good CSV.

Cell-6 markdown stays as-is (it already says "always_bet_home").
Cell-7 code: change to `strategy = always_bet_home`

Also update the import in cell-1 to import `always_bet_home` instead of `always_bet_away` (and also import `kelly_bet_home`):

```python
from cuic_quant.backtest import (
    load_backtest_data,
    backtest,
    always_bet_home,
    kelly_bet_home,
    validate_backtest_results,
    display_extended_metrics,
    plot_performance,
)
```

**Step 2: Add assumptions/limitations markdown cell**

Insert a new markdown cell after cell-0 (the title cell):

```markdown
## Assumptions & Limitations

- **Odds at face value** — no slippage, liquidity constraints, or market impact modeling. Bets are assumed to be filled at the quoted odds.
- **Synthetic data** — the default dataset (`dummy_backtest_input.csv`) is generated test data, not real market data.
- **Single bet per game** — no parlays, accumulators, or multi-leg bets.
- **No CLV (Closing Line Value)** — our data has a single odds snapshot per game. CLV calculation requires closing odds data (future enhancement).
- **Transaction costs optional** — costs default to 0. Use `cost_pct` and `cost_flat` parameters in `backtest()` to model bookmaker vig and fees.
- **Kelly sizing optional** — use `position_sizing="kelly"` to enable Kelly Criterion bet sizing based on strategy confidence values.
```

**Step 3: Add conclusion cell**

Add a new markdown cell at the end of the notebook:

```markdown
## Conclusion

This notebook demonstrates the full backtesting pipeline:

1. **Data loading** from CSV (or Railway database when available)
2. **Strategy evaluation** using a pluggable strategy interface
3. **Validation** across 11 checks (schema, math, data leakage)
4. **Performance metrics** (Sharpe, Sortino, drawdown, profit factor, streaks)
5. **Visualizations** (equity curve, drawdown, PnL distribution, outcomes)

To build your own strategy, implement a function matching the interface in `docs/reference/strategy-interface.md` and pass it to `backtest()`.

For Kelly Criterion position sizing, set `position_sizing="kelly"` and return a `confidence` value (0-1) from your strategy.

For transaction cost modeling, use `cost_pct` (percentage on wins) and `cost_flat` (flat fee per trade).
```

**Step 4: Commit**

```bash
git add tools/backtester.ipynb
git commit -m "docs: fix strategy inconsistency, add assumptions and conclusion to notebook"
```

---

### Task 9: Final Integration Test & Push

**Files:** None (verification only)

**Step 1: Run full test suite**

Run: `pytest tests/test_backtester_backend.py -v`
Expected: All tests PASS (should be ~35+ tests now)

**Step 2: Verify backwards compatibility**

Run: `pytest tests/ -v`
Expected: All project tests PASS

**Step 3: Update logs and tasks**

Update `team/james/LOG.md` and `team/james/TASKS.md` with the new work.

**Step 4: Final commit and push**

```bash
git add team/james/LOG.md team/james/TASKS.md team/PROJECT_LOG.md
git commit -m "docs: update James's logs for missing criteria implementation"
git push origin james_branch
```
