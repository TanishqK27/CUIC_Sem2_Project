# Backtester Module — Presentation

**Presenter:** James
**Date:** Feb 25, 2026
**Branch:** `james_branch` → `main` (PR #53)

---

## What I Built

A complete backtesting engine for evaluating sports betting strategies against historical data.

**Core module:** `src/cuic_quant/backtest/backtester_backend.py`

### Four Core Functions

| Function | Purpose |
|----------|---------|
| `load_backtest_data()` | Loads historical games from Railway DB or local CSV |
| `backtest()` | Runs a strategy over historical data, tracks PnL and bankroll |
| `validate_backtest_results()` | 11-check validation suite (schema, math, data leakage) |
| `display_extended_metrics()` | 12-metric performance table (Sharpe, Sortino, drawdown, etc.) |

### Three Example Strategies

| Strategy | Behaviour |
|----------|-----------|
| `always_bet_home()` | Fixed $100 on home team every game — deterministic test strategy |
| `always_bet_away()` | Fixed $100 on away team — tests BUY_AWAY logic path |
| `kelly_bet_home_demo()` | Kelly-sized home bets — **demo only**, shows how to wire confidence into Kelly sizing |

---

## The Pipeline

```
CSV / Database  →  load_backtest_data()  →  DataFrame (25 games)
                                                  ↓
                                           backtest(data, strategy)
                                                  ↓
                                           Results DataFrame (9 columns)
                                                  ↓
                            ┌─────────────────────┼─────────────────────┐
                            ↓                     ↓                     ↓
                   validate_backtest_results()  display_extended_metrics()  plot_performance()
                   (11 checks)                 (12 metrics)               (2x2 dashboard)
```

### 9-Column Output Format

Every strategy produces the same output — this is the contract that Ben's metrics and Ismaeel's tests depend on:

| Column | Type | Example |
|--------|------|---------|
| timestamp | datetime | 2026-01-01 |
| game | str | Lakers vs Celtics |
| action | str | BUY_HOME |
| bet_size | float | 256.58 |
| odds | float | 1.95 |
| outcome | str | WIN |
| pnl | float | 243.75 |
| cumulative_pnl | float | 243.75 |
| bankroll | float | 10243.75 |

---

## Key Features

### 1. Data Leakage Prevention

The backtester **strips `home_win` from the row** before passing it to the strategy function. This means strategies cannot cheat by looking at the outcome. We have a dedicated "spy strategy" test that verifies no strategy ever receives `home_win`.

### 2. Transaction Cost Modeling

Two cost parameters model real-world betting friction:

- **`cost_pct`** — Percentage deducted from winning payouts (models bookmaker vig)
- **`cost_flat`** — Flat dollar fee per trade regardless of outcome

```python
# Example: 5% vig + $1 flat fee
results = backtest(data, strategy, cost_pct=0.05, cost_flat=1.0)
```

PnL formulas:
- **WIN:** `bet_size * (odds - 1) * (1 - cost_pct) - cost_flat`
- **LOSS:** `-bet_size - cost_flat`

### 3. Kelly Criterion Position Sizing

Instead of flat $100 bets, Kelly sizes each bet as a fraction of your bankroll based on your estimated edge:

$$f^* = \frac{bp - q}{b}$$

Where `b` = net odds, `p` = estimated win probability (from strategy's `confidence`), `q` = 1 - p.

```python
# Enable Kelly with half-Kelly for safety
results = backtest(data, strategy, position_sizing="kelly", kelly_fraction=0.5)
```

| Kelly Fraction | Risk Profile |
|----------------|-------------|
| 0.25 | Very conservative |
| 0.50 | Moderate (default) |
| 0.75 | Aggressive |
| 1.00 | Maximum growth (unrealistic in practice) |

### 4. Validation Suite (11 Checks)

**Schema (5 checks):** Correct columns, valid actions/outcomes, positive bets, valid odds

**Math (4 checks):** PnL formula correctness, cumulative PnL is running sum, bankroll tracking, no overbetting

**Data Leakage (2 checks):** Outcomes match input data, chronological order

---

## Demo Results

Running `kelly_bet_home_demo` with quarter-Kelly on 25 NBA games:

| Metric | Value |
|--------|-------|
| Win Rate | 60.0% (15W / 10L) |
| Total PnL | $1,123.02 |
| Final Bankroll | $11,123.02 |
| ROI | 11.2% |
| Sharpe Ratio | 2.808 |
| Max Drawdown | 4.8% |
| Profit Factor | 1.434 |
| Validation | 12/12 checks passed |

---

## PR Review Fixes

The first PR was reviewed by Tan and returned with feedback across three categories. All items have been addressed.

### Critical Fixes (C1–C5)

**C1. `except Exception:` silently swallowed ALL errors**
- **Problem:** `__init__.py` caught SyntaxError, AttributeError, RecursionError — not just ImportError. A typo in any module would be invisible.
- **Fix:** Changed to `except ImportError:` with `logging.debug()` for visibility.

**C2. `kelly_bet_home` had circular edge logic**
- **Problem:** Confidence = implied_prob + 5%. Since Kelly is positive whenever p > 1/odds, and here p = 1/odds + 0.05, the strategy always bets by construction. It's tautological.
- **Fix:** Renamed to `kelly_bet_home_demo` with a prominent WARNING docstring explaining this is a plumbing demonstration, not a real edge model.

**C3. Sharpe/Sortino ratios were mathematically meaningless**
- **Problem:** Three compounding errors:
  1. Used raw dollar PnL instead of percentage returns
  2. Annualized with sqrt(252) (trading days) — wrong for sports bets
  3. Sortino used std(losses_only) instead of full-sample downside deviation
- **Fix:**
  1. Now computes `pnl / bankroll_before_bet` (percentage returns)
  2. Annualizes with sqrt(365)
  3. New `calculate_sortino_ratio()` with correct formula: `sqrt(mean(min(0, r_i)^2))` over ALL observations

**C4. Bankroll could go negative with `cost_flat`**
- **Problem:** `bet_size` was capped at `bankroll`, but loss = `-(bet_size + cost_flat)` could exceed bankroll. Example: bankroll=$50, bet=$50, cost=$2, loss=-$52, bankroll=-$2.
- **Fix:** `bet_size = min(bet_size, max(0.0, bankroll - cost_flat))`

**C5. Database fallback silently loaded dummy CSV**
- **Problem:** When DATABASE_URL was set but the query failed, the code `print()`ed a message and loaded 25 rows of synthetic data. User might unknowingly backtest on fake data.
- **Fix:** `warnings.warn(..., RuntimeWarning)` instead of `print()`. Added `strict=True` parameter that raises instead of falling back.

### Important Fixes (I1–I8)

| Fix | What Changed |
|-----|-------------|
| I1 | Kelly import moved from inside for-loop to top of function |
| I2 | Warning when Kelly falls back to flat sizing (confidence=None/0.0/1.0) |
| I3 | Input column validation — raises `ValueError` with clear message for missing columns |
| I4 | `display_extended_metrics()` handles missing metrics module gracefully |
| I5 | Warning on unrecognized strategy actions (e.g. "BUY_DRAW", "buy_home") |
| I6 | Google-style docstring added to `always_bet_away()` |
| I7 | Cost params stored in `DataFrame.attrs` metadata for downstream consumers |
| I8 | matplotlib import moved inside `plot_performance()` (lazy import) |

### Test Gaps Filled

| Test | What It Verifies |
|------|-----------------|
| Bankroll negative with cost_flat | Bankroll >= 0 at all times with flat fees (validates C4) |
| Multi-trade PnL with costs | Row-by-row PnL verification across 5 trades with both cost types |
| `always_bet_away` dedicated test | Action, context handling, docstring existence |
| Kelly confidence boundaries | 0.0 and 1.0 correctly fall back to flat sizing |
| Empty DataFrame input | Returns empty results with correct 9 columns |
| All-rows bankroll check | Every row has bankroll >= 0, not just the last |
| Missing columns | Raises ValueError (validates I3) |

**Test suite: 57 tests, all passing.**

---

## Files Changed

| File | Lines | What |
|------|-------|------|
| `src/cuic_quant/__init__.py` | 50 | Package init with narrowed exception handling |
| `src/cuic_quant/backtest/backtester_backend.py` | 934 | Core backtester module |
| `src/cuic_quant/backtest/__init__.py` | 37 | Package exports |
| `src/cuic_quant/metrics/__init__.py` | 185 | Performance metrics with Sortino fix |
| `tests/test_backtester_backend.py` | 999 | 57 tests |
| `team/james/LOG.md` | — | Work log updated |
| `team/james/TASKS.md` | — | Task tracker updated |

---

## What's Next (Roadmap)

These items were flagged in the review as "Domain Fitness" — not blocking merge but worth tracking:

- Walk-forward validation / train-test split for real strategy evaluation
- Closing Line Value (CLV) — the #1 metric for sports betting skill
- Polymarket/Kalshi compatibility (CLOB / YES-NO contracts)
- Multi-bookmaker odds (OddsAPIClient already supports this)
- Point spreads (currently moneyline only)
- Expose Kelly `max_fraction=0.25` cap in `backtest()` parameters

---

## How to Run

```bash
# Run the demo notebook
jupyter lab tools/backtester.ipynb

# Run tests
pytest tests/test_backtester_backend.py -v

# Use in your own code
from cuic_quant.backtest import backtest, load_backtest_data

data = load_backtest_data("2026-01-01", "2026-01-31")
results = backtest(data, your_strategy, position_sizing="kelly")
```
