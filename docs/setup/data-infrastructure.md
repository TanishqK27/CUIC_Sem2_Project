# Data Infrastructure Guide

This guide covers the Polymarket data collection and storage system for the CUIC Quant project.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Quick Start](#quick-start)
3. [CLI Commands](#cli-commands)
4. [API Server](#api-server)
5. [Notebook Interface](#notebook-interface)
6. [Database Schema](#database-schema)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Architecture

The data infrastructure follows a layered architecture for collecting, storing, and accessing Polymarket prediction market data.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Sources                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Polymarket API  │  │   CLOB API       │  │  Future APIs   │ │
│  │  (Markets)       │  │   (Orderbooks)   │  │  (Kalshi, etc) │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────────┘ │
└───────────┼──────────────────────┼──────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Collection Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ PolymarketClient │  │PolymarketCollector│                    │
│  │ (API wrapper)    │──│ (orchestration)   │                    │
│  └──────────────────┘  └────────┬─────────┘                     │
│                                 │                                │
│                        ┌────────┴─────────┐                     │
│                        │CollectionScheduler│                    │
│                        │ (background jobs) │                    │
│                        └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  SQLite Database │  │ MarketRepository │                     │
│  │  (polymarket.db) │◄─│ (data access)    │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Access Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   FastAPI        │  │ Notebook Helper  │  │   Direct SQL   │ │
│  │   REST API       │  │ (pm module)      │  │   Queries      │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Initialize Database

Create the SQLite database and tables:

```bash
cuic-quant init-db
```

This creates `data/polymarket.db` with all required tables.

### 2. Collect Data

Run a one-time collection:

```bash
# Collect up to 500 markets (default)
cuic-quant collect

# Collect a specific number of markets
cuic-quant collect --limit 100

# Full collection including orderbook data
cuic-quant collect --full
```

### 3. Start Background Scheduler (Optional)

For continuous data collection:

```bash
# Default intervals: markets every 15min, orderbooks every 5min
cuic-quant scheduler

# Custom intervals
cuic-quant scheduler --market-interval 10 --orderbook-interval 3
```

### 4. Start API Server (Optional)

Launch the REST API:

```bash
# Start on default port 8000
cuic-quant serve

# Custom host and port
cuic-quant serve --host 0.0.0.0 --port 8080

# Development mode with auto-reload
cuic-quant serve --reload
```

### 5. Use in Notebook

```python
from cuic_quant.notebook import pm

# Load markets from database
df = pm.load_markets()

# Or fetch live from API
df = pm.fetch_markets()

# Search for specific markets
election = pm.search("election")

# View collection statistics
stats = pm.stats()
```

---

## CLI Commands

The `cuic-quant` CLI provides commands for managing the data infrastructure.

### Command Reference

| Command | Description | Options |
|---------|-------------|---------|
| `init-db` | Create database tables | `--db-path` |
| `collect` | Run data collection | `--limit`, `--full` |
| `scheduler` | Start background scheduler | `--market-interval`, `--orderbook-interval` |
| `serve` | Start API server | `--host`, `--port`, `--reload` |
| `stats` | Show collection statistics | - |

### Detailed Usage

#### `cuic-quant init-db`

Initialize the database schema. Safe to run multiple times - existing tables are not modified.

```bash
# Use default location (data/polymarket.db)
cuic-quant init-db

# Use custom database path
cuic-quant init-db --db-path /path/to/custom.db
```

#### `cuic-quant collect`

Fetch market data from Polymarket API and store in database.

```bash
# Default: collect up to 500 markets
cuic-quant collect

# Collect specific number
cuic-quant collect --limit 100

# Full collection with orderbook data (takes longer)
cuic-quant collect --full

# Verbose output
cuic-quant -v collect --limit 50
```

#### `cuic-quant scheduler`

Run continuous background collection at specified intervals.

```bash
# Default intervals
cuic-quant scheduler

# Custom intervals (in minutes)
cuic-quant scheduler --market-interval 10 --orderbook-interval 3

# Stop with Ctrl+C
```

#### `cuic-quant serve`

Start the FastAPI REST server.

```bash
# Default: localhost:8000
cuic-quant serve

# Custom binding
cuic-quant serve --host 0.0.0.0 --port 8080

# Development mode with auto-reload
cuic-quant serve --reload
```

#### `cuic-quant stats`

Display statistics about collected data.

```bash
cuic-quant stats
```

Example output:
```
Collection Statistics
========================================
  Unique markets:     1,234
  Market snapshots:   5,678
  Active markets:     892
  Price points:       45,230

Date Range
----------------------------------------
  Oldest snapshot:    2024-01-15 10:30:00
  Newest snapshot:    2024-01-20 14:45:00
  Oldest price:       2024-01-15 10:30:00
  Newest price:       2024-01-20 14:45:00
```

---

## API Server

The FastAPI server provides REST endpoints for accessing collected data.

### Starting the Server

```bash
cuic-quant serve --port 8000
```

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/markets` | GET | List latest market snapshots |
| `/api/v1/markets/top` | GET | Top markets by volume |
| `/api/v1/markets/search` | GET | Search markets by question |
| `/api/v1/markets/{id}` | GET | Get specific market by ID |
| `/api/v1/prices/{token_id}` | GET | Price history for a token |
| `/api/v1/stats` | GET | Collection statistics |
| `/api/v1/collect` | POST | Trigger data collection |

### Example Requests

**List Markets:**
```bash
# Get 10 active markets
curl "http://localhost:8000/api/v1/markets?limit=10&active_only=true"
```

**Search Markets:**
```bash
# Search for election-related markets
curl "http://localhost:8000/api/v1/markets/search?q=election&limit=20"
```

**Top Markets by Volume:**
```bash
curl "http://localhost:8000/api/v1/markets/top?limit=10"
```

**Price History:**
```bash
# Get price history for a token
curl "http://localhost:8000/api/v1/prices/TOKEN_ID"

# With date range
curl "http://localhost:8000/api/v1/prices/TOKEN_ID?start_date=2024-01-01T00:00:00"
```

**Trigger Collection:**
```bash
curl -X POST "http://localhost:8000/api/v1/collect"
```

### Response Models

**MarketResponse:**
```json
{
  "id": 123,
  "question": "Will X happen by Y date?",
  "yes_price": 0.65,
  "no_price": 0.35,
  "volume": 1500000.0,
  "volume_24h": 50000.0,
  "liquidity": 200000.0,
  "status": "active",
  "active": true,
  "end_date": "2024-12-31T23:59:59",
  "snapshot_at": "2024-01-20T14:30:00"
}
```

**PricePointResponse:**
```json
{
  "timestamp": "2024-01-20T14:30:00",
  "price": 0.65,
  "best_bid": 0.64,
  "best_ask": 0.66,
  "spread": 0.02
}
```

---

## Notebook Interface

The `pm` module provides a convenient interface for Jupyter notebooks.

### Import

```python
from cuic_quant.notebook import pm
```

### Live API Methods

Fetch data directly from Polymarket API:

```python
# Fetch active markets
df = pm.fetch_markets(limit=100, active=True)

# Fetch orderbook for a token
orderbook = pm.fetch_orderbook("TOKEN_ID")
bids = orderbook[orderbook['side'] == 'bid']
asks = orderbook[orderbook['side'] == 'ask']
```

### Database Methods

Load data from local database (faster, no API limits):

```python
# Load markets from database
df = pm.load_markets(limit=1000, active_only=True)

# Load price history
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=7)
prices = pm.load_prices("TOKEN_ID", start_date=start, end_date=end)

# Plot price history
prices['price'].plot(title="7-Day Price History")

# Get top markets by volume
top = pm.load_top_markets(limit=20)

# Search markets by keyword
results = pm.search("bitcoin", limit=50)
```

### Collection Methods

Trigger data collection from notebook:

```python
# Collect data immediately
result = pm.collect_now(limit=100)

if result['status'] == 'success':
    print(f"Collected {result['markets_saved']} markets")
else:
    print(f"Error: {result.get('error')}")
```

### Statistics

```python
stats = pm.stats()
print(f"Total markets: {stats['total_markets']}")
print(f"Active markets: {stats['active_markets']}")
print(f"Price points: {stats['total_price_points']}")
print(f"Date range: {stats['oldest_snapshot']} to {stats['newest_snapshot']}")
```

### Complete Example

```python
from cuic_quant.notebook import pm
import matplotlib.pyplot as plt

# Check what data we have
stats = pm.stats()
print(f"Database contains {stats['total_markets']} markets")

# Load top markets by volume
top_markets = pm.load_top_markets(limit=10)
print(top_markets[['question', 'volume', 'yes_price']])

# Search for specific markets
crypto_markets = pm.search("bitcoin")
print(f"Found {len(crypto_markets)} bitcoin-related markets")

# Analyze a specific market's price history
if len(crypto_markets) > 0:
    # Get token ID from a market
    market_id = crypto_markets.iloc[0]['id']

    # Load full market data
    markets = pm.load_markets()
    market = markets[markets['polymarket_id'] == market_id].iloc[0]

    # If we have the token ID, get price history
    if market.get('yes_token_id'):
        prices = pm.load_prices(market['yes_token_id'])
        prices['price'].plot(title=f"Price History: {market['question'][:50]}...")
        plt.show()
```

---

## Database Schema

The SQLite database contains four main tables:

### Entity Relationship

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   events    │───────│ market_snapshots │───────│price_points │
│             │  1:N  │                  │  1:N  │             │
└─────────────┘       └──────────────────┘       └─────────────┘

┌─────────────────┐
│ collection_runs │  (standalone - tracks collection jobs)
└─────────────────┘
```

### Table: `events`

Polymarket events (groups of related markets).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| polymarket_id | VARCHAR(255) | Unique Polymarket event ID |
| slug | VARCHAR(500) | URL-friendly identifier |
| title | VARCHAR(1000) | Event display title |
| description | TEXT | Detailed description |
| category | VARCHAR(255) | Category (e.g., "politics") |
| active | BOOLEAN | Is event active |
| closed | BOOLEAN | Is event resolved |
| volume | FLOAT | Total trading volume (USDC) |
| liquidity | FLOAT | Current liquidity (USDC) |
| start_date | DATETIME | Event start date |
| end_date | DATETIME | Event resolution date |
| created_at | DATETIME | Record creation time |
| updated_at | DATETIME | Last update time |

### Table: `market_snapshots`

Point-in-time market state snapshots.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| polymarket_id | VARCHAR(255) | Polymarket market ID |
| event_id | INTEGER | Foreign key to events |
| question | VARCHAR(1000) | The prediction question |
| description | TEXT | Market description |
| slug | VARCHAR(500) | URL slug |
| yes_token_id | VARCHAR(255) | YES token identifier |
| no_token_id | VARCHAR(255) | NO token identifier |
| yes_price | FLOAT | YES token price (0-1) |
| no_price | FLOAT | NO token price (0-1) |
| volume | FLOAT | Total volume (USDC) |
| volume_24h | FLOAT | 24-hour volume |
| liquidity | FLOAT | Market liquidity |
| status | VARCHAR(50) | Market status |
| active | BOOLEAN | Is trading enabled |
| end_date | DATETIME | Resolution date |
| snapshot_at | DATETIME | When snapshot was taken |

### Table: `price_points`

Time series price data for tokens.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| market_id | INTEGER | Foreign key to market_snapshots |
| token_id | VARCHAR(255) | Token identifier |
| price | FLOAT | Token price (0-1) |
| timestamp | DATETIME | Observation time |
| best_bid | FLOAT | Best bid from orderbook |
| best_ask | FLOAT | Best ask from orderbook |
| spread | FLOAT | Bid-ask spread |
| created_at | DATETIME | Record creation time |

### Table: `collection_runs`

Metadata for collection job tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| started_at | DATETIME | Job start time |
| completed_at | DATETIME | Job completion time |
| status | VARCHAR(50) | Job status |
| markets_collected | INTEGER | Markets collected count |
| events_collected | INTEGER | Events collected count |
| price_points_collected | INTEGER | Price points collected |
| error_message | TEXT | Error details if failed |

---

## Advanced Usage

### Custom Database Location

```python
from cuic_quant.notebook import PolymarketNotebook

# Use custom database path
pm = PolymarketNotebook(db_path="/custom/path/data.db")
```

### Direct Repository Access

For advanced queries:

```python
from cuic_quant.database import MarketRepository

repo = MarketRepository()

# Get raw market snapshots
markets = repo.get_latest_markets(limit=100)

# Get statistics
stats = repo.get_collection_stats()

# Search with custom parameters
results = repo.search_markets(query="bitcoin", limit=50)
```

### Direct Database Access

For custom SQL queries:

```python
from cuic_quant.database import get_engine
from sqlalchemy import text
import pandas as pd

engine = get_engine()

# Custom SQL query
query = text("""
    SELECT question, yes_price, volume
    FROM market_snapshots
    WHERE volume > 100000
    ORDER BY volume DESC
    LIMIT 20
""")

df = pd.read_sql(query, engine)
```

### Running Collector Programmatically

```python
from cuic_quant.collector import PolymarketCollector, CollectionScheduler

# One-time collection
collector = PolymarketCollector()
result = collector.collect_markets(limit=100)

# Full collection with orderbooks
result = collector.run_full_collection()

# Background scheduler
scheduler = CollectionScheduler(
    market_interval_minutes=15,
    orderbook_interval_minutes=5,
)
scheduler.start()

# ... later ...
scheduler.stop()
```

---

## Troubleshooting

### Database Not Found

```bash
# Initialize the database first
cuic-quant init-db

# Check database location
ls -la data/polymarket.db
```

### Empty Results

```bash
# Run data collection
cuic-quant collect --limit 100

# Check statistics
cuic-quant stats
```

### API Server Won't Start

```bash
# Check if uvicorn is installed
pip install uvicorn

# Or install server extras
pip install -e ".[server]"

# Check if port is in use
lsof -i :8000
```

### Import Errors

```bash
# Ensure package is installed
pip install -e ".[all]"

# Verify installation
python -c "from cuic_quant.notebook import pm; print('OK')"
```

### Collection Errors

```python
# Check API connectivity
from cuic_quant.data import PolymarketClient
client = PolymarketClient()
markets = client.get_markets(limit=1)
print(f"API working: {len(markets)} markets fetched")
```

### Performance Tips

1. **Use database methods** (`load_*`) instead of API methods (`fetch_*`) for analysis
2. **Set appropriate limits** to avoid loading too much data into memory
3. **Use date filters** when loading price history
4. **Run scheduler** in background for continuous data collection

---

## Next Steps

1. Review the [example notebook](../../research/notebooks/examples/polymarket_data_exploration.ipynb)
2. Explore [strategy modules](../../src/cuic_quant/strategies/)
3. Check [API keys setup](api-keys.md) for additional platforms
