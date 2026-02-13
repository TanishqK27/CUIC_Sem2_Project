# James's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:
```
/update-log james <description of work>
```

---

## Log Entries

### Feb 13, 2026

**Backtester Refactor — Extracted to Importable Module**

Redesigned the backtester architecture: all logic extracted from `tools/backtester.ipynb` into `src/cuic_quant/backtest/backtester_backend.py` as an importable Python module. The notebook is now a thin caller with zero function definitions.

**New file:** `src/cuic_quant/backtest/backtester_backend.py` with 4 functions:
- `load_backtest_data()` — loads game data from Railway DB or CSV fallback
- `backtest()` — core backtest loop with data leakage prevention, NaN handling, bankroll capping
- `always_bet_home()` — deterministic test strategy for validation
- `validate_backtest_results()` — **NEW** 11-check validation suite covering schema, math correctness, and data leakage detection

**Validator checks (3 categories):**
1. Schema: 9 columns present, valid actions/outcomes, positive bet sizes
2. Math: PnL formulas correct, cumulative_pnl is running sum, bankroll = initial + cumulative_pnl, no overbet
3. Leakage: games exist in input, outcomes match input data, chronological order

**Updated:** `src/cuic_quant/backtest/__init__.py` — exports all 4 functions
**Rewritten:** `tools/backtester.ipynb` — from 27 cells (inline functions) to 16 cells (imports only)

**Tests:** 22 new tests in `tests/test_backtester_backend.py` covering all functions + edge cases. All pass.

**Verification results:**
- Dummy data (25 rows): 25 trades, 60% win rate, $305 PnL, validation 11/11 passed
- Output matches `dummy_backtest_output.csv` exactly
- Mya's test_games.csv (100 rows): 100 trades, validation 10/11 (1 false positive due to duplicate game names in test data)
- Edge cases: empty results, NaN odds, bankrupt bankroll all handled correctly

**Interface unchanged** — same function signatures, same 9-column output. Ben's metrics and Ismaeel's tests are unaffected.

---

### Feb 11, 2026

**Feedback Fixes Implemented**

Addressed all 3 feedback items from `task_briefs_feedback/week1-backtester-core.md`:

1. **Empty results column fix:** `backtest()` now returns empty DataFrame with correct 9 columns when strategy skips all games. Prevents Ben's metrics from blowing up on empty input.

2. **NaN odds handling:** Added check to skip rows where `home_odds` or `away_odds` are NaN. Prevents corruption of subsequent calculations.

3. **Data leakage prevention:** Already implemented (confirmed) — `row.drop(labels=["home_win"])` before passing to strategy.

**Edge Case Tests Added**
- Added test cells to `tools/backtester.ipynb` for:
  - Skip-all strategy returning empty DataFrame with correct columns
  - NaN odds being skipped without errors
- All tests pass

**Branch Updates**
- Merged `origin/ben` into `james_branch` (resolved backtester.ipynb conflict — kept data leakage fix)
- Merged `origin/main` into `james_branch` (no conflicts)
- Fixed `tools/test_metrics.ipynb` import path issue

---

### Feb 6, 2026

**Data Leakage Fix + Mya CSV Test**

- Fixed data leakage bug in `backtest()`: strategy functions were receiving the full row including `home_win`, allowing a cheating strategy to always win. Now drops `home_win` before calling `strategy_fn()`.
- Added test cells running backtester against Mya's `test_games.csv` (100 rows) with `always_bet_home` strategy
- Validated 9-column output format passes for both dummy and Mya datasets

**Backtester Core — Initial Build Complete**

- Created `data/dummy_backtest_input.csv` with 25 rows of NBA game data (7 columns: timestamp, game, home_team, away_team, home_odds, away_odds, home_win)
- Built `tools/backtester.ipynb` with two core functions:
  - `load_backtest_data(start_date, end_date)` — loads from Railway DB (DATABASE_URL) with CSV fallback
  - `backtest(data, strategy_fn, initial_bankroll)` — runs strategy over data, returns 9-column DataFrame
- Created example "always bet home" strategy and ran end-to-end test
- Documented strategy interface at `docs/reference/strategy-interface.md` (v1.0)
- Output format validated: timestamp, game, action, bet_size, odds, outcome, pnl, cumulative_pnl, bankroll

**Next:** Get test_games.csv from Mya, give Ismaeel access Tuesday.

**Mya's Test Data — Received and Verified**

- Received Mya's test data bundle: `test_games.csv` (100 rows) + `test_data_generator.py`
- Placed files per SOP: `data/test_games.csv`, `tools/test_data_generator.py`
- Verified compatibility: columns match backtester input spec exactly (timestamp, game, home_team, away_team, home_odds, away_odds, home_win)
- Generator includes edge case generators for Ismaeel's testing
- CSV is gitignored (`*.csv` rule); generator script is tracked

**Next:** Give Ismaeel access for testing on Tuesday.

<!-- New entries will be added above this line -->
