# CUIC Quant Fund - Project Log

Aggregated log of all team member contributions. Entries are in reverse chronological order (newest first).

---

## How to Add Entries

Use the `/update-log` skill to automatically add entries:

```text
/update-log <your-name> <description of work>
```

This will update both your personal `team/<name>/LOG.md` and this PROJECT_LOG.md.

---

## Log Entries

### 2026-02-17

- **[james]** Missing criteria implementation: added transaction cost modeling (`cost_pct`, `cost_flat` params), Kelly Criterion position sizing (`position_sizing="kelly"`), `kelly_bet_home()` example strategy, 6 edge case tests (extreme odds, zero bankroll, invalid actions, all-wins/losses). Fixed notebook strategy inconsistency, added assumptions/limitations and conclusion cells. Test suite: 47 tests, all passing.
- **[james]** Backtester cleanup: fixed `always_bet_away` import error, moved `display_extended_metrics()` and `plot_performance()` from notebook to backend, removed Mya's test section from notebook, added detailed validation documentation (11 checks across schema/math/leakage). Notebook now 20 cells with zero function definitions. Updated `__init__.py` to export all 8 public functions.

### 2026-02-13

- **[james]** Backtester refactor complete: extracted all logic from `tools/backtester.ipynb` into importable module `src/cuic_quant/backtest/backtester_backend.py` (4 functions: load_backtest_data, backtest, always_bet_home, validate_backtest_results). Added 11-check validation suite (schema, math, leakage). Notebook rewritten as thin caller. 22 unit tests, all passing. Interface unchanged — Ben's metrics and Ismaeel's tests unaffected.

### 2026-02-12

- **[dietrich]** Historical Odds API + Raw Data Correlation Analysis: Built `fetch_historical_odds.py` (The Odds API v4, 7 NBA seasons), downloaded 4,152 games historical sportsbook dataset (28.5K odds rows). Built `backtest_realistic.py` with CLV tracking, Kelly sizing, gap momentum. DB now at 181K price snapshots, 68M websocket orderbook events, 148K latency events. Correlation analysis on 7 measures: Granger causality shows SB leads PM (64% of games at lag 1), wide PM spreads predict 1.8x more price movement. Takeaway: Two actionable signals — SB moves first, wide spreads predict big moves.
- **[james]** Helped Ben with metrics module
- **[ben]** Completed metrics module task
- **[ismaeel]** Tested James' backtester code
- **[mya]** Uploaded sportsbook analysis work to GitHub
- **[max]** Final modifications to CSVs, making data as granular as possible
- **[alfie]** Updated odds data work
- **[vansheeka]** Working through data inventory commits, started understanding data analysis approaches

### 2026-02-05

- **[dietrich]** NBA Polymarket vs Sportsbook Arbitrage Project - Analysis Complete: Built complete trading system comparing Polymarket prediction market prices to traditional sportsbook odds for NBA games. Deployed data collection on Railway (PostgreSQL): 89,664+ price snapshots across 81 games. Implemented 5 trading strategies. Paper trading: 258 closed trades, +$2,592.81 P&L. Real trading: 4 closed trades, -$0.50 realized. Key finding: Gap signal is NOT predictive (24-39% win rate). Deliverables: analysis_results.ipynb, price_dynamics.ipynb, run_analysis.py, full database documentation. Conclusion: Current gap-based strategy not viable, recommending pivot to market making or higher-frequency approaches.
- **[miran]** Reviewed platform docs (Kalshi, Polymarket, Sports Betting Basics)
- **[miran]** Finished environment setup checks and confirmed the git hooks are working

### 2026-02-02

- **[tan]** Updated personal TASKS.md with team coordination tasks (speak to members, assign research tasks) due 4th Feb
- **[tan]** Added 25 research tasks to PROJECT_TASKS.md covering data sources, strategies, platforms, and literature reviews
- **[tan]** Added James to the team - created team/james/ folder with LOG.md and TASKS.md, updated all config files

### 2026-02-01

- **[tan]** Initialized project repository with complete structure, documentation, and tooling
- **[tan]** Committed initial infrastructure to main branch (72 files, 11k+ lines)
- **[tan]** Created personal `/tan-update-log` skill for quick log updates

---

<!-- New entries will be added above this line -->
