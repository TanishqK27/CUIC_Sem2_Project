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

### 2025-02-01

- Joined CUIC Quant Fund project

---

<!-- New entries will be added above this line -->
