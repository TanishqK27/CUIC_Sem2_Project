# Dietrich's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:
```
/update-log dietrich <description of work>
```

---

## Log Entries

### 2026-02-13

**Combined Player Stats Dataset + PostgreSQL Upload**

- Merged 8 individual CSV datasets (`Data/invidual_stats/`) into a single unified dataset: 136,965 rows x 428 columns, one row per player per game.
- Data sources combined: boxscores, advanced stats, hustle stats, tracking stats, pregame availability, pregame player rolling averages, team boxscores, pregame team stats.
- Pivoted per-period data (Q1-Q4, OT1-OT3) into flat columns (e.g. `q1_pts`, `q2_pts`, `adv_q1_off_rating`) — 259 additional columns alongside the full-game totals.
- Uploaded combined dataset to Railway PostgreSQL as `combined_player_stats` table with indexes on `game_id`, `player_id`, `team_id`, and a composite unique index on `(game_id, player_id)`.
- Created `query_examples.ipynb` — notebook with 8 example SQL queries (player lookup, season averages, quarter-by-quarter scoring, pregame vs actual, rest impact, hustle leaders, home/away splits, full DataFrame pull) plus a column reference guide.

**Scripts created:**
- `Data/invidual_stats/combine_all.py` — merges all 8 CSVs, pivots periods, outputs `combined_all_stats.csv` (224.8 MB)
- `Data/invidual_stats/upload_combined.py` — bulk uploads combined CSV to PostgreSQL via COPY
- `Data/invidual_stats/query_examples.ipynb` — query reference notebook

---

### 2026-02-12

**Historical Odds API + Raw Data Correlation Analysis**

- Built `fetch_historical_odds.py` — automated historical odds fetcher (The Odds API v4) covering 7 NBA seasons (2019-20 through 2025-26) with resume/credit management. Stores vig-adjusted probabilities + per-bookmaker JSONB in PostgreSQL.
- Downloaded historical sportsbook dataset: 4,152 games (Oct 2021 – Apr 2026), 15 bookmakers, 28.5K odds rows in `Data/`.
- Built `backtest_realistic.py` — full replay backtester with CLV tracking, Kelly sizing, live filter, gap momentum, and feature ablation (`--compare`).
- DB now at 181K price snapshots, 68M websocket orderbook events, 148K latency events across 129 games.
- Correlation analysis (`correlation_analysis.ipynb`) — 7 measures on raw data:
  - Orderbook imbalance, trade flow, gap half-life (128 min), conditional correlation — all either too weak, too slow, or inconclusive.
  - Granger causality: SB leads PM — significant in 64% of games at lag 1 (vs 45% for PM→SB). Sportsbooks move first, Polymarket follows within 5-10 min.
  - Spread predicts volatility — r = 0.23, p ≈ 0. Wide PM spreads predict 1.8x more price movement. Usable as a regime filter.

**Takeaway:** Two actionable signals — SB moves first (Granger), and wide PM spreads predict big moves. Combined: when SB moves while PM spread is wide, PM will likely follow within minutes.

---

### 2026-02-05

**NBA Polymarket vs Sportsbook Arbitrage Project - Analysis Complete**

- Built complete trading system comparing Polymarket prediction market prices to traditional sportsbook odds for NBA games
- Deployed data collection on Railway (PostgreSQL): 89,664+ price snapshots across 81 games
- Implemented 5 trading strategies: aggressive, safe, liq_aggressive, liq_balanced, liq_deep_only
- Paper trading results: 258 closed trades, +$2,592.81 P&L (though inflated by early unrealistic code)
- Real trading via Polymarket CLOB: 4 closed trades, -$0.50 realized; 3 stuck positions (~$11 loss)

**Key Findings:**
- Gap signal is NOT predictive: 24-39% win rate (worse than random 50%)
- Large gaps (30-50pp) only appear in decided games (SB >90%) — untradeable
- 614 real orders failed with "not enough balance" errors
- 5-minute polling too slow for mid-game opportunities

**Deliverables created:**
- `analysis_results.ipynb` — comprehensive trading analysis notebook
- `price_dynamics.ipynb` — correlation analysis, lead/lag relationships, database querying guide
- `run_analysis.py` — standalone Python script for all analysis
- Full database documentation with example queries

**Conclusion:** Current gap-based strategy is not viable. Recommended pivoting to market making, true arbitrage, or higher-frequency approaches.


---

<!-- New entries will be added above this line -->
