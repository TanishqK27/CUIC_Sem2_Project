# Polymarket Sports Betting Database Guide

> **Team Database:** PostgreSQL on Railway (IP-restricted)
> **Data:** NBA game prices from Polymarket vs Sportsbooks
> **Updated:** Live data collection running continuously

---

## Quick Start

### Connection Setup

```python
import psycopg2
import pandas as pd

# Database URL (requires VPN or whitelisted IP)
DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def run_query(query):
    """Run SQL query and return pandas DataFrame."""
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Test connection
df = run_query("SELECT COUNT(*) FROM price_snapshots")
print(f"Connected! {df.iloc[0,0]:,} price snapshots available")
```

### Google Colab Setup

If you can't connect locally (IP restrictions), use Google Colab:

```python
# Run this first in Colab
!pip install -q psycopg2-binary

import psycopg2
import pandas as pd

DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def run_query(query):
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    df = pd.read_sql(query, conn)
    conn.close()
    return df
```

---

## Database Overview

| Table | Rows | Description |
|-------|------|-------------|
| `price_snapshots` | 90,456 | Core price data: PM vs SB probabilities |
| `trade_decisions` | 316,397 | Why trades were made/skipped |
| `ws_book_events` | 24,099,429 | WebSocket orderbook events (high-frequency) |
| `orderbook_snapshots` | 116,710 | Aggregated orderbook state |
| `orderbook_levels` | 2,324,513 | Individual bid/ask levels |
| `latency_events` | 57,811 | Who moved first: PM or SB? |
| `paper_trades` | 258 | Simulated trade results |
| `paper_stats` | 3,799 | Strategy performance over time |
| `paper_positions` | 0 | Currently open paper positions |
| `paper_cooldowns` | 59 | Post-trade cooldown periods |
| `real_orders` | 710 | Actual orders placed |
| `real_positions` | 3 | Currently open real positions |
| `real_trades` | 4 | Completed real trades |

**Data Range:** January 26, 2026 - Present (live collection)
**Games Tracked:** 81 unique NBA games

---

## Table Schemas

### price_snapshots (Core Data)

The main table for price analysis. Each row is a point-in-time snapshot comparing Polymarket and sportsbook prices.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `timestamp` | timestamptz | When snapshot was taken |
| `game` | text | Game name (e.g., "Lakers @ Celtics") |
| `game_date` | date | Date of the game |
| `home` | text | Home team name |
| `away` | text | Away team name |
| `pm_home_prob` | float | Polymarket home win probability (0-1) |
| `pm_away_prob` | float | Polymarket away win probability (0-1) |
| `sb_home_prob` | float | Sportsbook home win probability (0-1) |
| `sb_away_prob` | float | Sportsbook away win probability (0-1) |
| `sb_home_ml` | float | Sportsbook moneyline (American odds) |
| `sb_away_ml` | float | Sportsbook moneyline (American odds) |
| `diff` | float | Gap: sb_home_prob - pm_home_prob |
| `has_arb` | boolean | Arbitrage opportunity detected |
| `arb_profit_pct` | float | Potential arbitrage profit % |

**Example Query:**
```sql
-- Get latest prices for all active games
SELECT DISTINCT ON (game)
    game,
    timestamp,
    pm_home_prob,
    sb_home_prob,
    (sb_home_prob - pm_home_prob) * 100 as gap_pp
FROM price_snapshots
WHERE pm_home_prob IS NOT NULL
ORDER BY game, timestamp DESC
```

---

### trade_decisions (Strategy Logic)

Logs every decision point for the trading strategies. Essential for understanding why trades happen or don't.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `timestamp` | timestamptz | Decision time |
| `strategy` | text | Strategy name |
| `game` | text | Game being evaluated |
| `gap` | float | Price gap at decision time |
| `abs_gap` | float | Absolute gap value |
| `min_gap_threshold` | float | Required gap to trade |
| `gap_exceeded` | boolean | Was threshold met? |
| `has_position` | boolean | Already in a position? |
| `on_cooldown` | boolean | In post-trade cooldown? |
| `game_decided` | boolean | Game outcome clear? |
| `decision` | text | Final decision made |
| `decision_detail` | text | Explanation of decision |
| `liquidity_tier` | text | Market liquidity level |

**Decision Types:**
| Decision | Count | Meaning |
|----------|-------|---------|
| `SKIP_LOW_GAP` | 240,198 | Gap too small to trade |
| `SKIP_NO_LIQUIDITY` | 24,990 | Insufficient orderbook depth |
| `SKIP_DECIDED` | 24,364 | Game outcome already clear |
| `HOLD` | 15,943 | Keep existing position |
| `EXIT_BLOCKED` | 6,337 | Can't exit (no liquidity) |
| `SKIP_COOLDOWN` | 4,263 | Recently traded, waiting |
| `EXIT_TP` | 92 | Take profit exit |
| `ENTER_BUY` | 92 | Open long position |
| `ENTER_SELL` | 86 | Open short position |
| `EXIT_SL` | 57 | Stop loss exit |

**Strategies:**
- `aggressive` - Lower thresholds, more trades
- `safe` - Higher thresholds, fewer trades
- `liq_aggressive` - Aggressive + liquidity checks
- `liq_balanced` - Balanced approach
- `liq_deep_only` - Only trade deep liquidity

---

### paper_trades (Simulated Results)

Completed paper trades with full P&L tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `strategy` | text | Strategy that made the trade |
| `game` | text | Game traded |
| `side` | text | BUY or SELL |
| `entry_price` | float | Entry probability |
| `exit_price` | float | Exit probability |
| `entry_gap` | float | Gap when entering |
| `exit_gap` | float | Gap when exiting |
| `entry_time` | timestamptz | When position opened |
| `exit_time` | timestamptz | When position closed |
| `hold_snapshots` | integer | How long held (in snapshots) |
| `pnl` | float | Profit/loss |
| `fees` | float | Trading fees |
| `exit_reason` | text | Why position was closed |
| `clv` | float | Closing line value |

**Strategy Performance:**
| Strategy | Trades | Win Rate | Total PnL |
|----------|--------|----------|-----------|
| aggressive | 88 | 73.9% | $1,807.20 |
| liq_deep_only | 28 | 71.4% | $654.58 |
| liq_aggressive | 52 | 50.0% | $83.93 |
| liq_balanced | 44 | 56.8% | $51.01 |
| safe | 46 | 54.3% | -$3.91 |

---

### latency_events (Who Moves First?)

Tracks which market (PM or SB) moves first when prices change.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `timestamp` | timestamptz | Event time |
| `game` | text | Game name |
| `pm_home_prev` | float | PM price before move |
| `pm_home_now` | float | PM price after move |
| `pm_delta` | float | PM price change |
| `sb_home_prev` | float | SB price before move |
| `sb_home_now` | float | SB price after move |
| `sb_delta` | float | SB price change |
| `leader` | text | Who moved first |
| `gap_closing` | boolean | Did gap narrow? |

**Leader Breakdown:**
| Leader | Count | Percentage |
|--------|-------|------------|
| none | 50,168 | 86.8% |
| sb | 4,013 | 6.9% |
| pm | 2,947 | 5.1% |
| both | 692 | 1.2% |

---

### orderbook_snapshots (Liquidity Data)

Aggregated orderbook state with depth and slippage metrics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `timestamp` | timestamptz | Snapshot time |
| `game` | text | Game name |
| `outcome` | text | HOME or AWAY |
| `best_bid` | float | Highest buy price |
| `best_ask` | float | Lowest sell price |
| `bid_ask_spread` | float | Spread (avg: 1.16%) |
| `mid_price` | float | Midpoint price |
| `bid_depth_total` | float | Total bid liquidity |
| `ask_depth_total` | float | Total ask liquidity |
| `cost_to_buy_100` | float | Cost to buy $100 |
| `slippage_buy_100` | float | Slippage on $100 buy |
| `slip_buy_25/50/250/500/1000` | float | Slippage at various sizes |

---

### ws_book_events (High-Frequency Data)

Raw WebSocket orderbook events - very high volume (24M+ rows).

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key |
| `timestamp` | timestamptz | Event time |
| `event_type` | text | Type of orderbook event |
| `asset_id` | text | Polymarket token ID |
| `game` | text | Game name |
| `outcome` | text | HOME or AWAY |
| `best_bid` | float | Best bid at event time |
| `best_ask` | float | Best ask at event time |
| `buy_levels` | jsonb | Full bid ladder (JSON) |
| `sell_levels` | jsonb | Full ask ladder (JSON) |

---

## Common Queries

### 1. Latest Prices for All Games
```sql
SELECT DISTINCT ON (game)
    game,
    timestamp,
    pm_home_prob,
    sb_home_prob,
    (sb_home_prob - pm_home_prob) * 100 as gap_pp
FROM price_snapshots
WHERE pm_home_prob IS NOT NULL
ORDER BY game, timestamp DESC
```

### 2. Price History for a Specific Game
```sql
SELECT timestamp, pm_home_prob, sb_home_prob,
       (sb_home_prob - pm_home_prob) * 100 as gap
FROM price_snapshots
WHERE game LIKE '%Lakers%'
ORDER BY timestamp
```

### 3. Find Large Gaps in Competitive Games
```sql
SELECT game, timestamp, pm_home_prob, sb_home_prob,
       (sb_home_prob - pm_home_prob) * 100 as gap
FROM price_snapshots
WHERE ABS(sb_home_prob - pm_home_prob) > 0.05
  AND sb_home_prob BETWEEN 0.25 AND 0.75
ORDER BY timestamp DESC
LIMIT 50
```

### 4. Strategy Performance Summary
```sql
SELECT
    strategy,
    COUNT(*) as trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
    ROUND(SUM(pnl)::numeric, 2) as total_pnl,
    ROUND(AVG(pnl)::numeric, 4) as avg_pnl
FROM paper_trades
GROUP BY strategy
ORDER BY total_pnl DESC
```

### 5. Why Were Trades Skipped?
```sql
SELECT decision, COUNT(*) as cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM trade_decisions
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY decision
ORDER BY cnt DESC
```

### 6. Who Moves First Analysis
```sql
SELECT
    leader,
    COUNT(*) as events,
    ROUND(AVG(ABS(gap_delta))::numeric, 4) as avg_gap_change
FROM latency_events
WHERE leader IS NOT NULL
GROUP BY leader
ORDER BY events DESC
```

### 7. Orderbook Depth by Game
```sql
SELECT
    game,
    COUNT(*) as snapshots,
    ROUND(AVG(bid_depth_total)::numeric, 0) as avg_bid_depth,
    ROUND(AVG(ask_depth_total)::numeric, 0) as avg_ask_depth,
    ROUND(AVG(bid_ask_spread)::numeric, 4) as avg_spread
FROM orderbook_snapshots
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY game
ORDER BY avg_bid_depth DESC
```

### 8. Daily Gap Statistics
```sql
SELECT
    DATE(timestamp) as date,
    COUNT(*) as snapshots,
    COUNT(DISTINCT game) as games,
    ROUND(AVG(ABS(diff) * 100)::numeric, 2) as avg_gap_pp,
    ROUND(MAX(ABS(diff) * 100)::numeric, 1) as max_gap_pp
FROM price_snapshots
WHERE pm_home_prob IS NOT NULL
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 14
```

---

## SQL Patterns Cheat Sheet

### Time Filtering
```sql
-- Last 24 hours
WHERE timestamp > NOW() - INTERVAL '24 hours'

-- Specific date range
WHERE timestamp BETWEEN '2026-02-01' AND '2026-02-05'

-- Today only
WHERE DATE(timestamp) = CURRENT_DATE
```

### Text Matching
```sql
-- Contains (case-sensitive)
WHERE game LIKE '%Lakers%'

-- Contains (case-insensitive)
WHERE game ILIKE '%lakers%'

-- Starts with
WHERE game LIKE 'Los Angeles%'
```

### Latest Row Per Group
```sql
-- PostgreSQL-specific: DISTINCT ON
SELECT DISTINCT ON (game) *
FROM price_snapshots
ORDER BY game, timestamp DESC
```

### Window Functions
```sql
-- Previous and next values
SELECT *,
    LAG(pm_home_prob) OVER (PARTITION BY game ORDER BY timestamp) as pm_prev,
    LEAD(pm_home_prob) OVER (PARTITION BY game ORDER BY timestamp) as pm_next
FROM price_snapshots
```

### Conditional Aggregation
```sql
SELECT
    COUNT(*) FILTER (WHERE ABS(diff) > 0.05) as large_gaps,
    COUNT(*) FILTER (WHERE ABS(diff) <= 0.05) as small_gaps
FROM price_snapshots
```

---

## Key Concepts

### Gap (diff)
The difference between sportsbook and Polymarket probability:
- **Positive gap:** SB thinks home team more likely to win than PM
- **Negative gap:** PM thinks home team more likely to win than SB
- **Trading signal:** Large gaps may indicate mispricing

### Liquidity Tiers
- **deep** - High liquidity, low slippage
- **medium** - Moderate liquidity
- **shallow** - Low liquidity, high slippage
- **none** - No orderbook depth

### Exit Reasons
- **Take profit** - Gap converged, profit target hit
- **Stop loss** - Gap widened, loss limit hit
- **Game ended** - Game finished, position closed
- **Timeout** - Held too long without resolution

---

## Notebooks

| Notebook | Description |
|----------|-------------|
| `research/notebooks/polymarket/price_dynamics.ipynb` | Correlation, lead/lag, mean reversion analysis |
| `research/notebooks/polymarket/data_exploration.ipynb` | Polymarket public API exploration |

---

## Tips

1. **Start with `price_snapshots`** - It's the core table for most analysis
2. **Use `trade_decisions` to understand strategy logic** - See why trades happen
3. **Careful with `ws_book_events`** - 24M+ rows, always use LIMIT and filters
4. **Check `paper_trades` for backtest results** - Real performance data
5. **Use Colab if IP-restricted** - Colab IPs usually aren't blocked
