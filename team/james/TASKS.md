# James's Tasks

## Week 2: Backtester Refactor (Feb 13+)

### To Do
- [ ] Give Ismaeel access to new backtester module for testing

### In Progress
| Task | Started | Notes |
|------|---------|-------|
| | | |

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Extract backtester into importable Python module | Feb 13 | `src/cuic_quant/backtest/backtester_backend.py` — 4 functions |
| Add validation suite (schema + math + leakage) | Feb 13 | `validate_backtest_results()` — 11 checks across 3 categories |
| Rewrite notebook as thin caller | Feb 13 | `tools/backtester.ipynb` — 16 cells, zero function definitions |
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
