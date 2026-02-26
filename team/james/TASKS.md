# James's Tasks

## Week 4: 10-Agent Audit Fixes + Documentation (Feb 26)

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Fix engine.py crash vectors (14 fixes) | Feb 26 | Input validation, NaN guards, deep copies, leakage prevention |
| Fix metrics/__init__.py (5 fixes) | Feb 26 | yield_per_bet, calmar_ratio, return_on_capital, Brier clamping |
| Fix statistics.py (3 fixes) | Feb 26 | One-sided p-value, DSR skew/kurtosis, PBO docs |
| Fix walk_forward.py (4 fixes) | Feb 26 | Fold-0 skip, OOS Sharpe concat, chrono sort check |
| Fix comparison.py (4 fixes) | Feb 26 | NaN columns, dense ranking, odds guard, point-biserial |
| Fix validator.py (3 fixes) | Feb 26 | cost_flat overbetting, attrs auto-read, Optional params |
| Create test_audit_fixes.py (42+ tests) | Feb 26 | Comprehensive coverage for all audit findings |
| Fix existing tests (3 files) | Feb 26 | Extended, comparison, walk-forward test updates |
| Verify all 30 PR items still fixed | Feb 26 | B1-B5, S1-S5, M1-M4, U1-U5, T1-T6, D1-D5 |
| Write 35-page LaTeX documentation | Feb 26 | Complete backtester reference document |

---

## Week 3: PR Review Fixes (Feb 25)

### To Do
- [ ] Give Ismaeel access to new backtester module for testing

### In Progress
| Task | Started | Notes |
|------|---------|-------|
| | | |

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Fix C1: except Exception to except ImportError | Feb 25 | Added logging.debug for visibility |
| Fix C2: Rename kelly_bet_home to kelly_bet_home_demo | Feb 25 | Prominent warning docstring about tautological edge |
| Fix C3: Correct Sharpe/Sortino ratios | Feb 25 | Percentage returns, 365 annualization, new Sortino formula |
| Fix C4: Bankroll negative with cost_flat | Feb 25 | bet_size capped at bankroll - cost_flat |
| Fix C5: DB fallback warning + strict mode | Feb 25 | warnings.warn(RuntimeWarning), strict=True param |
| Fix I1: Kelly import out of for-loop | Feb 25 | Moved to top of function |
| Fix I2: Warn on Kelly to flat fallback | Feb 25 | warnings.warn when confidence outside (0,1) |
| Fix I3: Input validation on backtest() | Feb 25 | ValueError for missing columns |
| Fix I4: display_extended_metrics error handling | Feb 25 | try/except ImportError fallback |
| Fix I5: Warn on unrecognized actions | Feb 25 | warnings.warn for invalid actions |
| Fix I6: always_bet_away docstring | Feb 25 | Google-style, matches always_bet_home |
| Fix I7: Store cost params in metadata | Feb 25 | DataFrame.attrs for cost_pct, cost_flat, initial_bankroll |
| Fix I8: Move matplotlib import | Feb 25 | Lazy import inside plot_performance() |
| Add missing tests from PR review | Feb 25 | 10 new tests: bankroll, PnL math, always_bet_away, Kelly bounds, empty DF |

---

## Week 2: Backtester Refactor + Cleanup (Feb 13+)

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Add Kelly Criterion math annotation to notebook | Feb 17 | Formula, worked example, tweaking guide with file locations |
| Add transaction cost modeling (`cost_pct`, `cost_flat`) | Feb 17 | New params in `backtest()` + validator, 4 tests |
| Add Kelly criterion position sizing | Feb 17 | `position_sizing="kelly"` + `kelly_fraction` params, 4 tests |
| Add `kelly_bet_home()` example strategy | Feb 17 | Uses implied prob + 5% edge as confidence, exported from package |
| Add edge case tests (financial extremes) | Feb 17 | Extreme odds, zero bankroll, invalid action, all-wins/losses — 6 tests |
| Fix notebook strategy inconsistency | Feb 17 | Changed to `always_bet_home`, updated imports |
| Add assumptions/limitations + conclusion to notebook | Feb 17 | Two new markdown cells documenting scope and summarizing pipeline |
| Fix `always_bet_away` import error | Feb 17 | Was missing from `__init__.py` exports — notebook couldn't run |
| Move `display_extended_metrics()` to backend | Feb 17 | ~50 lines extracted from notebook into `backtester_backend.py` |
| Move `plot_performance()` to backend | Feb 17 | ~60 lines extracted from notebook into `backtester_backend.py` |
| Remove Mya's test section from notebook | Feb 17 | Deleted test_games.csv cells + TEST_CSV config |
| Add detailed validation check documentation | Feb 17 | Expanded docstring in backend + markdown cell in notebook listing all 11 checks |
| Update `__init__.py` with all 7 exports | Feb 17 | Now exports: `always_bet_away`, `always_bet_home`, `backtest`, `display_extended_metrics`, `load_backtest_data`, `plot_performance`, `validate_backtest_results` |
| Extract backtester into importable Python module | Feb 13 | `src/cuic_quant/backtest/backtester_backend.py` — 4 functions |
| Add validation suite (schema + math + leakage) | Feb 13 | `validate_backtest_results()` — 11 checks across 3 categories |
| Rewrite notebook as thin caller | Feb 13 | `tools/backtester.ipynb` — 18 cells, zero function definitions |
| Write 22 unit tests for backtester backend | Feb 13 | `tests/test_backtester_backend.py` — all passing |
| Update `__init__.py` package exports | Feb 13 | `from cuic_quant.backtest import backtest, ...` now works |
| Verify output matches expected CSV exactly | Feb 13 | `dummy_backtest_output.csv` matches perfectly |

---

## Week 1: Backtester Core (Feb 6-12)

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Create dummy input CSV with 20+ rows | Feb 6 | `data/dummy_backtest_input.csv` — 25 rows of NBA game data |
| Build `load_backtest_data()` function | Feb 6 | In `tools/backtester.ipynb` — supports Railway DB + CSV fallback |
| Build `backtest()` function with 9-column output | Feb 6 | In `tools/backtester.ipynb` — returns exact 9-column spec |
| Document strategy interface | Feb 6 | `docs/reference/strategy-interface.md` — v1.0 |
| Test with simple "always bet home" strategy | Feb 6 | End-to-end run in notebook with validation checks |
| Get test data from Mya and verify compatibility | Feb 6 | `data/test_games.csv` (100 rows) + `tools/test_data_generator.py` — matches backtester input spec |
| **Feedback fix:** Prevent home_win data leakage | Feb 11 | Already implemented — `row.drop(labels=["home_win"])` before passing to strategy |
| **Feedback fix:** Empty results return correct columns | Feb 11 | Returns `pd.DataFrame(columns=OUTPUT_COLUMNS)` when no trades |
| **Feedback fix:** Skip rows with NaN odds | Feb 11 | Added `pd.isna()` check before processing each row |
| Add edge case tests to backtester notebook | Feb 11 | Tests for skip-all strategy and NaN odds handling |

---

## Notes
- Output format: 9 columns (timestamp, game, action, bet_size, odds, outcome, pnl, cumulative_pnl, bankroll)
- Ben depends on your output format
- See `team/james/work/task_briefs/week1-backtester-core.md` for full spec
