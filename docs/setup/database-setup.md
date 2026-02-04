# CockroachDB Database Setup Guide

This guide walks you through accessing the team's shared CockroachDB database. Follow each step carefully.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Your Credentials](#getting-your-credentials)
3. [Setting Up Your Environment](#setting-up-your-environment)
4. [Testing Your Connection](#testing-your-connection)
5. [Using the Database in Python](#using-the-database-in-python)
6. [Using the Database in Jupyter Notebooks](#using-the-database-in-jupyter-notebooks)
7. [Connecting via CLI Tools](#connecting-via-cli-tools)
8. [Database Schema Reference](#database-schema-reference)
9. [Common Queries](#common-queries)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What is CockroachDB?

CockroachDB is a distributed SQL database that's compatible with PostgreSQL. We use it because:

- **Team Sharing**: Everyone can read/write to the same database simultaneously
- **Cloud Hosted**: No need to run a database on your laptop
- **Free Tier**: 10GB storage, unlimited users
- **PostgreSQL Compatible**: Use familiar SQL and Python libraries

### What's in the Database?

| Table | Description |
|-------|-------------|
| `events` | Polymarket events (NBA games, championships, etc.) |
| `market_snapshots` | Individual markets within events (YES/NO outcomes) |
| `price_points` | Historical price data for each market |

---

## Getting Your Credentials

### Step 1: Request Access from Tan

Message Tan to get the database connection string. You'll receive something like:

```
postgresql://username:PASSWORD@hostname:26257/defaultdb?sslmode=require
```

**Important**: Keep this password secret! Never commit it to git.

### Step 2: Understand the Connection String

```
postgresql://Tan:YOUR_PASSWORD@bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require
         │    │              │                                                           │        │         │
         │    │              │                                                           │        │         └─ SSL required
         │    │              │                                                           │        └─ Database name
         │    │              │                                                           └─ Port
         │    │              └─ Hostname (AWS EU-West-2)
         │    └─ Password (keep secret!)
         └─ Username
```

---

## Setting Up Your Environment

### Step 1: Navigate to the Project

```bash
cd "/Users/tanishq/Desktop/VSCode Folders/CUIC Quant /CUIC_Sem2_Project"
```

Or wherever you've cloned the repository.

### Step 2: Create Your .env File

Copy the example environment file:

```bash
cp configs/example.env .env
```

### Step 3: Add Your Database URL

Open `.env` in your editor and add the connection string:

```bash
# Open in VS Code
code .env

# Or use nano
nano .env
```

Add this line (replace with your actual credentials):

```
DATABASE_URL=postgresql://Tan:YOUR_PASSWORD@bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require
```

### Step 4: Save and Close

The `.env` file is already in `.gitignore`, so it won't be committed.

### Step 5: Install Dependencies

Make sure you have the required Python packages:

```bash
# Activate your virtual environment first
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .[dev,research]

# Install CockroachDB dialect (if not already installed)
pip install sqlalchemy-cockroachdb psycopg2-binary python-dotenv
```

---

## Testing Your Connection

### Quick Test Script

Run this to verify your connection works:

```bash
cd "/Users/tanishq/Desktop/VSCode Folders/CUIC Quant /CUIC_Sem2_Project"
source .venv/bin/activate

python3 -c "
from dotenv import load_dotenv
load_dotenv()

from cuic_quant.database import get_engine, get_session

engine = get_engine()
print(f'Connected to: {engine.url.host}')

with get_session(engine) as session:
    from sqlalchemy import text
    result = session.execute(text('SELECT 1'))
    print(f'Query test: {result.scalar()}')

print('Connection successful!')
"
```

**Expected Output:**

```
Connected to: bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud
Query test: 1
Connection successful!
```

---

## Using the Database in Python

### Basic Pattern

```python
from dotenv import load_dotenv
load_dotenv()  # Load DATABASE_URL from .env

from cuic_quant.database import get_engine, get_session
from cuic_quant.database.models import Event, MarketSnapshot, PricePoint

# Create engine (connects to CockroachDB automatically)
engine = get_engine()

# Use session for queries
with get_session(engine) as session:
    # Your queries here
    events = session.query(Event).limit(10).all()
    for event in events:
        print(f"{event.title}: {event.volume}")
```

### Query Examples

```python
from dotenv import load_dotenv
load_dotenv()

from cuic_quant.database import get_engine, get_session
from cuic_quant.database.models import Event, MarketSnapshot, PricePoint
from sqlalchemy import func

engine = get_engine()

with get_session(engine) as session:
    # Count all events
    event_count = session.query(Event).count()
    print(f"Total events: {event_count}")

    # Get highest volume events
    top_events = session.query(Event)\
        .order_by(Event.volume.desc())\
        .limit(5)\
        .all()

    for e in top_events:
        print(f"  {e.title[:50]}: ${e.volume:,.0f}")

    # Get markets for a specific event
    event = session.query(Event).filter(Event.title.ilike('%nba%champion%')).first()
    if event:
        markets = session.query(MarketSnapshot)\
            .filter(MarketSnapshot.event_id == event.id)\
            .all()
        print(f"\nMarkets in '{event.title[:40]}':")
        for m in markets[:5]:
            print(f"  {m.question[:40]}: {m.yes_price:.2%}")
```

---

## Using the Database in Jupyter Notebooks

### Setup Cell (Run First)

```python
# Cell 1: Setup
import sys
sys.path.insert(0, '../src')  # Adjust path as needed

from dotenv import load_dotenv
load_dotenv('../.env')  # Adjust path to your .env file

from cuic_quant.database import get_engine, get_session
from cuic_quant.database.models import Event, MarketSnapshot, PricePoint
import pandas as pd

engine = get_engine()
print(f"Connected to: {engine.url.host}")
```

### Query to DataFrame

```python
# Cell 2: Load data into pandas
with get_session(engine) as session:
    # Get all NBA events as DataFrame
    events = session.query(Event).filter(Event.slug.ilike('%nba%')).all()

    df = pd.DataFrame([{
        'id': e.id,
        'title': e.title,
        'volume': e.volume,
        'active': e.active,
        'closed': e.closed,
    } for e in events])

df.head()
```

### Using Raw SQL with Pandas

```python
# Cell 3: Raw SQL query
from sqlalchemy import text

query = """
SELECT
    e.title as event,
    COUNT(m.id) as market_count,
    SUM(m.volume) as total_volume
FROM events e
JOIN market_snapshots m ON m.event_id = e.id
WHERE e.slug LIKE '%nba%'
GROUP BY e.id, e.title
ORDER BY total_volume DESC
LIMIT 10
"""

with engine.connect() as conn:
    df = pd.read_sql(text(query), conn)

df
```

---

## Connecting via CLI Tools

### Using psql (PostgreSQL CLI)

If you have `psql` installed:

```bash
# Install psql if needed (macOS)
brew install postgresql

# Connect to CockroachDB
psql "postgresql://Tan:YOUR_PASSWORD@bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require"
```

### Using CockroachDB CLI

```bash
# Install cockroach CLI (macOS)
brew install cockroachdb/tap/cockroach

# Connect
cockroach sql --url "postgresql://Tan:YOUR_PASSWORD@bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require"
```

### Using DBeaver (GUI)

1. Download [DBeaver](https://dbeaver.io/download/)
2. New Connection → PostgreSQL
3. Host: `bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud`
4. Port: `26257`
5. Database: `defaultdb`
6. Username: `Tan` (or your username)
7. Password: Your password
8. SSL → Use SSL: checked, SSL Mode: `require`

---

## Database Schema Reference

### events

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| polymarket_id | VARCHAR(255) | Polymarket's event ID |
| slug | VARCHAR(500) | URL-friendly identifier |
| title | VARCHAR(1000) | Event title |
| description | TEXT | Full description |
| category | VARCHAR(255) | Category (e.g., "Sports") |
| active | BOOLEAN | Is event active? |
| closed | BOOLEAN | Is event closed? |
| volume | FLOAT | Total volume traded (USD) |
| liquidity | FLOAT | Current liquidity |
| start_date | TIMESTAMP | Event start |
| end_date | TIMESTAMP | Event end |
| created_at | TIMESTAMP | Record creation |
| updated_at | TIMESTAMP | Last update |

### market_snapshots

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| polymarket_id | VARCHAR(255) | Polymarket's market ID |
| event_id | INTEGER | Foreign key to events |
| question | VARCHAR(1000) | Market question |
| description | TEXT | Full description |
| slug | VARCHAR(500) | URL-friendly identifier |
| yes_token_id | VARCHAR(255) | Token ID for YES outcome |
| no_token_id | VARCHAR(255) | Token ID for NO outcome |
| yes_price | FLOAT | Current YES price (0-1) |
| no_price | FLOAT | Current NO price (0-1) |
| volume | FLOAT | Total volume traded |
| volume_24h | FLOAT | 24-hour volume |
| liquidity | FLOAT | Current liquidity |
| status | VARCHAR(50) | "active" or "resolved" |
| active | BOOLEAN | Is market active? |
| end_date | TIMESTAMP | Market end date |
| snapshot_at | TIMESTAMP | When snapshot was taken |

### price_points

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| market_id | INTEGER | Foreign key to market_snapshots |
| token_id | VARCHAR(255) | Token ID |
| price | FLOAT | Price at timestamp (0-1) |
| timestamp | TIMESTAMP | Price timestamp |
| best_bid | FLOAT | Best bid (if captured) |
| best_ask | FLOAT | Best ask (if captured) |
| spread | FLOAT | Bid-ask spread |
| created_at | TIMESTAMP | Record creation |

---

## Common Queries

### Count Records

```sql
SELECT
    (SELECT COUNT(*) FROM events) as events,
    (SELECT COUNT(*) FROM market_snapshots) as markets,
    (SELECT COUNT(*) FROM price_points) as price_points;
```

### Top Events by Volume

```sql
SELECT title, volume, active, closed
FROM events
ORDER BY volume DESC
LIMIT 10;
```

### Markets with Price History

```sql
SELECT
    m.question,
    COUNT(p.id) as price_points,
    MIN(p.timestamp) as first_price,
    MAX(p.timestamp) as last_price
FROM market_snapshots m
JOIN price_points p ON p.market_id = m.id
GROUP BY m.id, m.question
ORDER BY price_points DESC
LIMIT 10;
```

### Price History for a Market

```sql
SELECT timestamp, price
FROM price_points
WHERE market_id = 123
ORDER BY timestamp;
```

---

## Troubleshooting

### "Connection refused" or timeout

**Cause**: Network issue or wrong hostname

**Fix**:
1. Check your internet connection
2. Verify the hostname in your DATABASE_URL
3. Try: `ping bull-canary-21388.j77.aws-eu-west-2.cockroachlabs.cloud`

### "Password authentication failed"

**Cause**: Wrong password in DATABASE_URL

**Fix**:
1. Double-check password in your `.env` file
2. Make sure there are no extra spaces
3. Request new credentials from Tan if needed

### "SSL SYSCALL error" or certificate errors

**Cause**: SSL configuration issue

**Fix**: Make sure your URL ends with `?sslmode=require` (not `verify-full`)

### "Could not determine version from string 'CockroachDB...'"

**Cause**: Missing CockroachDB SQLAlchemy dialect

**Fix**:
```bash
pip install sqlalchemy-cockroachdb
```

### "No module named 'dotenv'"

**Cause**: Missing python-dotenv package

**Fix**:
```bash
pip install python-dotenv
```

### "No module named 'psycopg2'"

**Cause**: Missing PostgreSQL driver

**Fix**:
```bash
pip install psycopg2-binary
```

### Database is empty

**Cause**: Data collection hasn't run yet

**Fix**: Data is collected nightly at midnight, or run manually:
```bash
python scripts/collect_historic_data.py
```

---

## Need Help?

- **Database access issues**: Message Tan
- **Query help**: Check `research/notebooks/polymarket/data_exploration.ipynb` for examples
- **Schema questions**: See `src/cuic_quant/database/models.py`

---

*Last updated: 2026-02-04*
