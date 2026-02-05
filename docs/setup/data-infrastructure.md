# Data Infrastructure Setup

How to connect to the team's shared Polymarket database.

📖 **What's in the database?** See [DATABASE_GUIDE.md](../../research/notebooks/polymarket/polymarket_data_collection/DATABASE_GUIDE.md)

---

## Quick Start (Google Colab)

**Recommended for most users** - no IP restrictions, no local setup.

1. Open a notebook: [getting_started.ipynb](../../research/notebooks/polymarket/polymarket_data_collection/getting_started.ipynb)
2. Click the "Open in Colab" badge
3. Run the first cell

```python
# Works in Colab without any setup
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

---

## Local Setup (Requires VPN)

The database has IP restrictions. If you have VPN access:

### 1. Install dependency

```bash
pip install psycopg2-binary
```

### 2. Test connection

```bash
python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway')
print('Connected!')
conn.close()
"
```

### 3. Use in Python

```python
import psycopg2
import pandas as pd

DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def query(sql):
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

# Example
df = query("SELECT * FROM price_snapshots LIMIT 10")
```

---

## Direct SQL Access

```bash
# Using psql (install: brew install postgresql)
psql 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'
```

---

## Available Notebooks

| Notebook | Purpose |
|----------|---------|
| [getting_started.ipynb](../../research/notebooks/polymarket/polymarket_data_collection/getting_started.ipynb) | Interactive tutorial with visualizations |
| [price_dynamics.ipynb](../../research/notebooks/polymarket/polymarket_data_collection/price_dynamics.ipynb) | Advanced price analysis |

---

## Troubleshooting

### Connection Timeout
**Cause:** Your IP isn't whitelisted
**Fix:** Use Google Colab (recommended) or connect via VPN

### "No module named psycopg2"
```bash
pip install psycopg2-binary
```

### Empty Results
Check your SQL syntax and column names in [DATABASE_GUIDE.md](../../research/notebooks/polymarket/polymarket_data_collection/DATABASE_GUIDE.md)

---

## Other Data Sources

| Platform | Status | Client |
|----------|--------|--------|
| **Polymarket** | ✅ Via shared DB | See above |
| **Kalshi** | 🔧 Framework ready | `from cuic_quant.data import KalshiClient` |
| **The Odds API** | 🔧 Framework ready | `from cuic_quant.data import OddsAPIClient` |

📖 **API key setup:** See [api-keys.md](api-keys.md)
