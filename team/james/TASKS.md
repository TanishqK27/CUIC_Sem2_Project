# James's Tasks

## Week 1: Backtester Core (Feb 6-12)

### To Do
- [ ] Get test data from Mya and verify compatibility
- [ ] Give Ismaeel access for testing (Tuesday)

### In Progress
| Task | Started | Notes |
|------|---------|-------|
| | | |

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| Create dummy input CSV with 20+ rows | Feb 6 | `data/dummy_backtest_input.csv` — 25 rows of NBA game data |
| Build `load_backtest_data()` function | Feb 6 | In `tools/backtester.ipynb` — supports Railway DB + CSV fallback |
| Build `backtest()` function with 9-column output | Feb 6 | In `tools/backtester.ipynb` — returns exact 9-column spec |
| Document strategy interface | Feb 6 | `docs/reference/strategy-interface.md` — v1.0 |
| Test with simple "always bet home" strategy | Feb 6 | End-to-end run in notebook with validation checks |

---

## Notes
- Output format: 9 columns (timestamp, game, action, bet_size, odds, outcome, pnl, cumulative_pnl, bankroll)
- Ben depends on your output format
- See `team/james/work/task_briefs/week1-backtester-core.md` for full spec
