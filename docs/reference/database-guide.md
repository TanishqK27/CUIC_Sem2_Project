# Database Guide: What's in the Data

A plain-English guide to our NBA betting database.

🔧 **How to connect:** See [Connecting to Database](../guides/connecting-to-database.md)
🔬 **Explore interactively:** See [Polymarket Data Exploration](../../tools/polymarket_data_exploration.ipynb)

---

## The Big Picture

We collect data comparing **Polymarket** (a prediction market) prices to **Sportsbook** odds for NBA games. When these prices differ significantly, there may be trading opportunities.

**Data source:** Dietrich's strategy experimentation and testing generated the core trading data.

---

## Tables at a Glance

| Table | What It Contains | Use It For |
|-------|------------------|------------|
| `price_snapshots` | PM vs Sportsbook prices over time | Finding price gaps, trend analysis |
| `trade_decisions` | Why the strategy traded or skipped | Understanding strategy logic |
| `paper_trades` | Simulated trade results | Evaluating strategy performance |
| `latency_events` | Which market moves first | Timing analysis |
| `orderbook_snapshots` | Market depth and liquidity | Assessing trade feasibility |
| `ws_book_events` | Raw real-time orderbook updates | High-frequency analysis |

---

## Core Tables Explained

### price_snapshots — The Main Table

**What it is:** A snapshot every few seconds comparing Polymarket and Sportsbook prices for each NBA game.

**Key columns:**

| Column | What It Means |
|--------|---------------|
| `game` | The matchup, e.g., "Lakers @ Celtics" |
| `pm_home_prob` | Polymarket's implied probability the home team wins (0.0–1.0) |
| `sb_home_prob` | Sportsbook's implied probability (0.0–1.0) |
| `diff` | The gap: `sb_home_prob - pm_home_prob` |
| `has_arb` | True if there's a risk-free arbitrage opportunity |

**How to read it:**

- `pm_home_prob = 0.65` means Polymarket thinks home team has 65% chance to win
- `diff = 0.05` means Sportsbook thinks home is 5 percentage points more likely than PM does
- Large gaps (|diff| > 0.05) may indicate mispricing

**Example query:**

```sql
-- Latest prices for each game
SELECT DISTINCT ON (game) game, pm_home_prob, sb_home_prob, diff
FROM price_snapshots
ORDER BY game, timestamp DESC
```

---

### trade_decisions — Strategy Logic

**What it is:** Every time the strategy evaluates whether to trade, it logs the decision and why.

**Key columns:**

| Column | What It Means |
|--------|---------------|
| `strategy` | Which strategy variant (aggressive, safe, etc.) |
| `gap` | Price gap at decision time |
| `decision` | What the strategy decided to do |
| `decision_detail` | Human-readable explanation |
| `liquidity_tier` | Market depth level (deep/medium/shallow/none) |

**Common decisions:**

| Decision | Meaning |
|----------|---------|
| `SKIP_LOW_GAP` | Gap too small to be profitable |
| `SKIP_NO_LIQUIDITY` | Can't trade — not enough buyers/sellers |
| `ENTER_BUY` | Opening a long position |
| `EXIT_TP` | Closing for profit (take profit) |
| `EXIT_SL` | Closing at a loss (stop loss) |

**Strategy variants:**

- `aggressive` — Lower thresholds, trades more often
- `safe` — Higher thresholds, fewer but more confident trades
- `liq_deep_only` — Only trades when there's deep liquidity

---

### paper_trades — Simulated Results

**What it is:** Completed simulated trades with full profit/loss tracking. No real money involved.

**Key columns:**

| Column | What It Means |
|--------|---------------|
| `strategy` | Which strategy made the trade |
| `side` | BUY or SELL |
| `entry_price` / `exit_price` | Prices when opening and closing |
| `pnl` | Profit or loss in dollars |
| `exit_reason` | Why the trade was closed (take profit, stop loss, etc.) |

**Current performance:**

| Strategy | Trades | Win Rate | Total P&L |
|----------|--------|----------|-----------|
| aggressive | 88 | 73.9% | +$1,807 |
| liq_deep_only | 28 | 71.4% | +$655 |
| safe | 46 | 54.3% | -$4 |

---

### latency_events — Who Moves First?

**What it is:** Tracks when prices change and which market (PM or Sportsbook) moved first.

**Why it matters:** If sportsbooks consistently move before Polymarket, we might be able to trade on Polymarket before it catches up.

**Key columns:**

| Column | What It Means |
|--------|---------------|
| `leader` | Which market moved first: `pm`, `sb`, `both`, or `none` |
| `pm_delta` | How much Polymarket's price changed |
| `sb_delta` | How much Sportsbook's price changed |
| `gap_closing` | Did the gap get smaller? (convergence) |

**Current findings:**

- 86.8% of the time, neither moves significantly
- Sportsbooks lead 6.9% of the time
- Polymarket leads 5.1% of the time

---

## Orderbook Tables

### What's an Orderbook?

An orderbook shows all the buy orders (bids) and sell orders (asks) waiting to be filled. Think of it like a queue of people wanting to buy or sell at different prices.

- **Bid:** "I'll buy at this price"
- **Ask:** "I'll sell at this price"
- **Spread:** Gap between best bid and best ask
- **Depth:** How much money is available at each price level

### orderbook_snapshots — Aggregated Liquidity

**What it is:** A summary of the orderbook at regular intervals.

**Key columns:**

| Column | What It Means |
|--------|---------------|
| `best_bid` | Highest price someone will pay |
| `best_ask` | Lowest price someone will sell at |
| `bid_ask_spread` | Gap between bid and ask (lower = more liquid) |
| `bid_depth_total` | Total $ available on buy side |
| `slippage_buy_100` | Extra cost to buy $100 worth |

**How to read it:**

- `bid_ask_spread = 0.02` means 2% spread — you lose 2% just to enter and exit
- `bid_depth_total = 5000` means $5,000 available to sell into
- Higher depth = easier to trade large amounts

---

### ws_book_events — Real-Time Updates

**What it is:** Raw WebSocket feed of every orderbook change. Very high volume (24M+ rows).

**What's a WebSocket?** A live connection that streams data in real-time, like a stock ticker. Every time someone places or cancels an order, we get an update.

**⚠️ Warning:** This table is huge. Always use `LIMIT` and filters:

```sql
-- DON'T do this (will timeout)
SELECT * FROM ws_book_events

-- DO this instead
SELECT * FROM ws_book_events
WHERE game LIKE '%Lakers%'
  AND timestamp > NOW() - INTERVAL '1 hour'
LIMIT 1000
```

---

## Key Concepts

### The Gap (diff)

The difference between what sportsbooks and Polymarket think:

```
gap = sb_home_prob - pm_home_prob
```

- **Positive gap (+0.05):** Sportsbooks think home team is 5pp more likely than PM
- **Negative gap (-0.03):** Polymarket thinks home team is 3pp more likely than SB
- **Trading thesis:** Gaps tend to close over time → bet on convergence

### Liquidity Tiers

How easy it is to trade:

| Tier | Meaning | Can Trade? |
|------|---------|------------|
| `deep` | Lots of buyers and sellers | ✅ Yes, large amounts |
| `medium` | Moderate activity | ✅ Yes, smaller amounts |
| `shallow` | Few orders available | ⚠️ High slippage |
| `none` | No orderbook depth | ❌ Can't trade |

### Implied Probability

Converting betting odds to probabilities:

- **Polymarket:** Price IS the probability (0.65 = 65% chance)
- **Sportsbook:** Convert from American odds
  - +150 → 100/(100+150) = 40%
  - -200 → 200/(200+100) = 67%

---

## Common Queries

### Latest prices for all games

```sql
SELECT DISTINCT ON (game)
    game, timestamp, pm_home_prob, sb_home_prob,
    ROUND((sb_home_prob - pm_home_prob) * 100, 1) as gap_pct
FROM price_snapshots
WHERE pm_home_prob IS NOT NULL
ORDER BY game, timestamp DESC
```

### Find large gaps (potential opportunities)

```sql
SELECT game, timestamp, pm_home_prob, sb_home_prob, diff
FROM price_snapshots
WHERE ABS(diff) > 0.05
ORDER BY timestamp DESC
LIMIT 20
```

### Strategy performance

```sql
SELECT strategy,
       COUNT(*) as trades,
       ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
       ROUND(SUM(pnl)::numeric, 2) as total_pnl
FROM paper_trades
GROUP BY strategy
ORDER BY total_pnl DESC
```

### Why are trades being skipped?

```sql
SELECT decision, COUNT(*) as count
FROM trade_decisions
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY decision
ORDER BY count DESC
```

---

## SQL Tips

### Time filters

```sql
-- Last 24 hours
WHERE timestamp > NOW() - INTERVAL '24 hours'

-- Specific date range
WHERE timestamp BETWEEN '2026-02-01' AND '2026-02-05'
```

### Text search

```sql
-- Contains (case-insensitive)
WHERE game ILIKE '%lakers%'
```

### Latest row per group

```sql
-- PostgreSQL-specific
SELECT DISTINCT ON (game) *
FROM price_snapshots
ORDER BY game, timestamp DESC
```

---

## Data Stats

| Metric | Value |
|--------|-------|
| **Date range** | Jan 26, 2026 – Present |
| **Games tracked** | 81 NBA games |
| **Price snapshots** | 90,456 |
| **Trade decisions** | 316,397 |
| **Paper trades** | 258 |
| **WebSocket events** | 24,099,429 |
