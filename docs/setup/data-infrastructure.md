# Data Infrastructure Guide

This guide covers accessing the team's shared Polymarket database for research and analysis.

---

## Overview

The CUIC Quant team uses a shared PostgreSQL database hosted on Railway for NBA betting data. Another team member runs continuous data collection - you just need to query it.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Team Data Collection Server                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  Polymarket API  │  │   Sportsbook API │                     │
│  │  (Prices)        │  │   (Odds)         │                     │
│  └────────┬─────────┘  └────────┬─────────┘                     │
│           │                     │                                │
│           └─────────┬───────────┘                                │
│                     ▼                                            │
│           ┌──────────────────┐                                   │
│           │ Data Collector   │  (runs continuously)              │
│           └────────┬─────────┘                                   │
│                    │                                             │
│                    ▼                                             │
│           ┌──────────────────┐                                   │
│           │ Railway PostgreSQL│                                  │
│           │ (24M+ rows)      │                                   │
│           └────────┬─────────┘                                   │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼ (IP-restricted)
┌─────────────────────────────────────────────────────────────────┐
│                       Your Access Options                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Google Colab    │  │  Local + VPN     │  │  Direct psql   │ │
│  │  (Recommended)   │  │  (If available)  │  │  (Advanced)    │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### What's in the Database?

| Table | Rows | Description |
|-------|------|-------------|
| `price_snapshots` | 90K+ | PM vs Sportsbook probabilities |
| `trade_decisions` | 316K+ | Strategy decision logs |
| `paper_trades` | 258 | Simulated trade results |
| `orderbook_snapshots` | 116K+ | Liquidity and depth data |
| `ws_book_events` | 24M+ | High-frequency WebSocket data |
| `latency_events` | 57K+ | Who moves first analysis |

📖 **Full schema details:** See [`docs/DATABASE_GUIDE.md`](../DATABASE_GUIDE.md)

---

## Quick Start

### Option 1: Google Colab (Recommended)

Best for most users - no IP restrictions, no setup required.

1. Open the getting started notebook: [`research/notebooks/polymarket/getting_started.ipynb`](../../research/notebooks/polymarket/getting_started.ipynb)
2. Click the "Open in Colab" badge
3. Run the first cell to connect

```python
# This works in Colab without any setup
import sys
if 'google.colab' in sys.modules:
    !pip install -q psycopg2-binary

import psycopg2
import pandas as pd

DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def query(sql):
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

# Test it
query("SELECT COUNT(*) FROM price_snapshots")
```

### Option 2: Local with VPN

If you have VPN access:

```bash
# Install dependency
pip install psycopg2-binary

# Test connection
python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway')
print('Connected!')
conn.close()
"
```

### Option 3: Direct psql

```bash
psql 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'
```

---

## Available Notebooks

| Notebook | Purpose |
|----------|---------|
| [`getting_started.ipynb`](../../research/notebooks/polymarket/getting_started.ipynb) | Interactive tutorial with visualizations |
| [`price_dynamics.ipynb`](../../research/notebooks/polymarket/price_dynamics.ipynb) | Advanced price analysis |

Both notebooks have Colab badges for easy access.

---

## Example Queries

### Latest Prices

```sql
SELECT DISTINCT ON (game)
    game, timestamp, pm_home_prob, sb_home_prob,
    (sb_home_prob - pm_home_prob) * 100 as gap_pp
FROM price_snapshots
WHERE pm_home_prob IS NOT NULL
ORDER BY game, timestamp DESC
```

### Strategy Performance

```sql
SELECT strategy, COUNT(*) as trades,
       ROUND(100.0 * SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate,
       ROUND(SUM(pnl)::numeric, 2) as total_pnl
FROM paper_trades
GROUP BY strategy
ORDER BY total_pnl DESC
```

### Find Large Gaps

```sql
SELECT game, timestamp, pm_home_prob, sb_home_prob,
       (sb_home_prob - pm_home_prob) * 100 as gap
FROM price_snapshots
WHERE ABS(sb_home_prob - pm_home_prob) > 0.05
ORDER BY timestamp DESC
LIMIT 20
```

📖 **More queries:** See [`docs/DATABASE_GUIDE.md`](../DATABASE_GUIDE.md)

---

## Troubleshooting

### Connection Timeout

**Cause:** IP not whitelisted

**Fix:** Use Google Colab (recommended) or connect via VPN

### Empty Results

**Cause:** Query syntax issue or no matching data

**Fix:** Check column names in DATABASE_GUIDE.md

### psycopg2 Import Error

```bash
pip install psycopg2-binary
```

---

## Data Platforms

The project integrates with multiple data sources:

| Platform | Status | Purpose |
|----------|--------|---------|
| **Polymarket** | ✅ Team server | NBA betting data (via shared DB) |
| **Kalshi** | 🔧 Framework ready | CFTC-regulated event contracts |
| **The Odds API** | 🔧 Framework ready | Aggregated sportsbook odds |

### Kalshi Client

```python
from cuic_quant.data import KalshiClient

client = KalshiClient(api_key="your-key")
markets = client.get_markets(category="sports")
```

### Odds API Client

```python
from cuic_quant.data import OddsAPIClient

client = OddsAPIClient(api_key="your-key")
odds = client.get_nba_odds()
```

📖 **API key setup:** See [`docs/setup/api-keys.md`](api-keys.md)

---

## Next Steps

1. Start with [`getting_started.ipynb`](../../research/notebooks/polymarket/getting_started.ipynb) in Colab
2. Review [`DATABASE_GUIDE.md`](../DATABASE_GUIDE.md) for full schema
3. Explore strategy code in `src/cuic_quant/strategies/`
4. Check research tasks in `team/PROJECT_TASKS.md`
