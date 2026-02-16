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

### 2026-02-16

- **[tan]** Completed Polymarket NBA microstructure analysis: 67.9M orderbook events, 114+ games, 180K+ price snapshots. Key findings: 2.3% median spread, $142K depth, extreme fat tails (kurtosis=214), weak mean reversion (~3 min half-life), whale dominance (1.3% trades = 57.5% volume). Created 12-chapter LaTeX report with methodology tutorial boxes.

### 2026-02-15

- **[tan]** Completed NBA EDA Part 2: bivariate correlations with FDR correction, stratified analysis by player tier (Star/Rotation/Bench), cross-season R² analysis, home advantage trends (54-56% win rate). Generated 9 publication-quality figures. Started Polymarket microstructure framework.

### 2026-02-14

- **[tan]** Created rigorous NBA player statistics EDA: 136,965 rows × 428 columns, 5 seasons (2021-26). Implemented data quality assessment (MCAR/MAR/MNAR classification), outlier detection (IQR), univariate distributions with bootstrap CIs. Set up publication-quality figure pipeline.

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
