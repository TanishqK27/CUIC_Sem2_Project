# Strategy Notes

## Win Rate ≠ Profitability

**Observed:** `kelly_bet_home_demo` on 871 real NBA games → 55.1% WR but -89% ROI ($-8,913 on $10k).

**Why:** The strategy always bets home. Homes win more often (55%) but those wins are mostly on favorites with low odds. Losses are on underdogs with high odds.

| Metric | Wins | Losses |
|--------|------|--------|
| Avg odds | 1.75 | 2.67 |
| Avg payout | +$114 | -$162 |
| Breakeven WR needed | 57.2% | — |

**Key insight:** Breakeven win rate = `1 / avg_odds`. At avg winning odds of 1.75, you need 57.2% WR to break even — our 55.1% falls short. The market already prices in home advantage through lower odds, so blindly betting home captures no edge.

**Takeaway for strategy design:**
- Win rate alone is meaningless without considering the odds at which you win/lose
- A profitable strategy needs: `win_rate > 1 / avg_odds_on_wins`
- Or equivalently: `avg_win * win_rate + avg_loss * (1 - win_rate) > 0`
- The backtester correctly exposes this — it's working as intended
