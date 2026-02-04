# Polymarket API Guide

A beginner-friendly guide to fetching prediction market data from Polymarket.

**No database, no API keys, no special setup** - just install the package and start exploring.

---

## Table of Contents

1. [What is Polymarket?](#what-is-polymarket)
2. [Getting Started](#getting-started)
3. [Fetching Markets](#fetching-markets)
4. [Understanding Market Data](#understanding-market-data)
5. [Fetching Order Books](#fetching-order-books)
6. [Understanding Order Books](#understanding-order-books)
7. [Finding Sports Markets](#finding-sports-markets)
8. [Direct API Access](#direct-api-access)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)
11. [Glossary](#glossary)

---

## What is Polymarket?

Polymarket is a **prediction market** - a platform where people trade on the outcomes of real-world events. Instead of betting with a bookmaker, users buy and sell shares that pay out based on what actually happens.

**Example:** A market asking "Will Team X win the championship?" might have:
- **YES shares** trading at $0.60 (60 cents)
- **NO shares** trading at $0.40 (40 cents)

The price represents the market's collective estimate of the probability. If you think the true probability is higher than 60%, you'd buy YES shares. If the event happens, each YES share pays out $1.00.

**Why this matters for quant research:**
- Prices = real-time probability estimates from thousands of traders
- Can be compared against sports betting odds
- Potential arbitrage opportunities
- Data on how predictions change over time

---

## Getting Started

### Step 1: Make sure the package is installed

Open a terminal in the project folder and run:

```bash
pip install -e .
```

This installs the `cuic_quant` package so you can import it in Python.

### Step 2: Open a Jupyter notebook

```bash
jupyter lab
```

Or open the existing notebook at `research/notebooks/polymarket/data_exploration.ipynb`.

### Step 3: Import the helper

```python
from cuic_quant.notebook import pm
```

That's it! The `pm` object gives you easy access to Polymarket data.

---

## Fetching Markets

### Basic Usage

```python
from cuic_quant.notebook import pm

# Fetch 50 active markets
df = pm.fetch_markets(limit=50, active=True)

# See what we got
print(f"Fetched {len(df)} markets")
df.head()
```

### What the parameters mean

| Parameter | What it does | Default |
|-----------|--------------|---------|
| `limit` | How many markets to fetch (max ~100) | 100 |
| `active` | Only get markets that are still open for trading | True |

### Example output

```
   id          question                                    yes_price  volume      status
0  abc123...   Will Bitcoin reach $100K by end of 2024?   0.45       2500000.0   active
1  def456...   Will it rain in London tomorrow?           0.72       15000.0     active
2  ghi789...   Will Team X win the Super Bowl?            0.08       890000.0    active
```

---

## Understanding Market Data

When you fetch markets, you get a DataFrame with these columns:

### Column Definitions

| Column | What it means | Example |
|--------|---------------|---------|
| `id` | Unique identifier for the market | `"0x1234..."` |
| `question` | What the market is asking | `"Will X happen?"` |
| `yes_price` | Current price of YES shares (0 to 1) | `0.65` |
| `no_price` | Current price of NO shares (0 to 1) | `0.35` |
| `volume` | Total money traded (in USD) | `1500000.0` |
| `liquidity` | Money available in the order book | `50000.0` |
| `status` | Market state | `"active"` or `"resolved"` |
| `end_date` | When the market closes | `"2024-12-31"` |

### Understanding Prices

**Key concept:** `yes_price` is the market's probability estimate.

- `yes_price = 0.75` means the market thinks there's a **75% chance** of YES
- `yes_price = 0.20` means the market thinks there's a **20% chance** of YES
- `yes_price + no_price` should roughly equal 1.00 (slight differences are normal)

**Example interpretation:**

```python
# A market with yes_price = 0.65
# Interpretation: "The market thinks there's a 65% chance this happens"
# If you disagree and think it's actually 80%, you might buy YES shares
```

### Understanding Volume

Volume tells you how much money has been traded on this market.

- **High volume** (>$1M) = Many people trading, prices likely accurate
- **Low volume** (<$10K) = Few traders, prices might be unreliable

```python
# Find high-volume markets (more reliable prices)
high_volume = df[df['volume'] > 100000]
print(f"Found {len(high_volume)} markets with >$100K volume")
```

### Understanding Liquidity

Liquidity is how much money is sitting in the order book right now.

- **High liquidity** = You can trade large amounts without moving the price
- **Low liquidity** = Even small trades will move the price significantly

---

## Fetching Order Books

An **order book** shows all the buy orders (bids) and sell orders (asks) for a market.

### Why order books matter

- See the **best prices** you can buy/sell at
- Understand the **spread** (gap between buy and sell prices)
- Gauge **market depth** (how much you can trade)

### Getting an order book

```python
# First, you need a token ID
# Token IDs are found in market data from the raw API

import requests
import json

# Fetch markets with token IDs
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={"limit": 10, "active": "true", "closed": "false"}
)
markets = response.json()

# Find the first market with tokens
for market in markets:
    tokens = market.get("clobTokenIds")
    if tokens:
        # Parse the JSON string
        if isinstance(tokens, str):
            tokens = json.loads(tokens)

        if tokens and len(tokens) > 0:
            token_id = tokens[0]  # First token is usually YES
            question = market.get("question", "Unknown")

            print(f"Market: {question}")
            print(f"Token ID: {token_id}")
            break
```

### Fetching the order book

```python
# Now fetch the order book for that token
orderbook = pm.fetch_orderbook(token_id)

print(f"Order book has {len(orderbook)} entries")
orderbook.head(10)
```

### Example output

```
   price    size    side
0  0.6500   150.0   bid
1  0.6400   200.0   bid
2  0.6300   500.0   bid
3  0.6600    75.0   ask
4  0.6700   100.0   ask
5  0.6800   300.0   ask
```

---

## Understanding Order Books

### What is a bid?

A **bid** is someone wanting to BUY shares.
- They're willing to pay the `price` shown
- They want to buy `size` number of shares

```
Bid: price=0.65, size=150
Translation: "Someone wants to buy 150 shares at $0.65 each"
```

### What is an ask?

An **ask** is someone wanting to SELL shares.
- They're willing to sell at the `price` shown
- They have `size` shares to sell

```
Ask: price=0.67, size=100
Translation: "Someone wants to sell 100 shares at $0.67 each"
```

### The spread

The **spread** is the gap between the best bid and best ask.

```python
# Calculate the spread
bids = orderbook[orderbook['side'] == 'bid']
asks = orderbook[orderbook['side'] == 'ask']

best_bid = bids['price'].max()  # Highest price someone will pay
best_ask = asks['price'].min()  # Lowest price someone will sell

spread = best_ask - best_bid

print(f"Best Bid: ${best_bid:.4f}")
print(f"Best Ask: ${best_ask:.4f}")
print(f"Spread: ${spread:.4f} ({spread*100:.2f}%)")
```

**Interpreting the spread:**
- **Tight spread** (< 1%): Liquid market, easy to trade
- **Wide spread** (> 5%): Illiquid market, harder to trade profitably

### Visualizing an order book

```
        BIDS (Buyers)          |          ASKS (Sellers)
        ----------------------+------------------------
        $0.65  ████████ 150   |   $0.67  ████ 100
        $0.64  ██████████ 200 |   $0.68  ████████ 200
        $0.63  ██████████████ 500 |   $0.69  ██████████ 300
                              |
              ← Buyers        |        Sellers →
```

The gap in the middle is the spread. If you want to buy immediately, you pay the ask price. If you want to sell immediately, you receive the bid price.

---

## Finding Sports Markets

Sports markets on Polymarket are organized under **events**, not individual markets.

### Why events?

An event like "NBA Finals 2024" contains multiple markets:
- "Will Team A win?"
- "Will it go to 7 games?"
- "Will Player X score 30+ points?"

### Fetching events

```python
import requests

# Get all open events
response = requests.get(
    "https://gamma-api.polymarket.com/events",
    params={"limit": 100, "closed": "false"}
)
events = response.json()

print(f"Found {len(events)} open events")
```

### Filtering for sports

```python
# Filter for NBA events
nba_events = [e for e in events if "nba" in e.get("slug", "").lower()]

print(f"Found {len(nba_events)} NBA events")

# Show them
for event in nba_events[:5]:
    title = event.get("title", "N/A")
    markets = event.get("markets", [])
    print(f"\n{title}")
    print(f"  Contains {len(markets)} markets")
```

### Getting markets from an event

```python
# Pick an NBA event
if nba_events:
    event = nba_events[0]

    print(f"Event: {event.get('title')}")
    print(f"\nMarkets in this event:")

    for market in event.get("markets", [])[:5]:
        question = market.get("question", "N/A")
        volume = float(market.get("volume", 0))
        print(f"  ${volume:>10,.0f}  {question[:60]}")
```

### Other sports to search for

```python
# Common sports slugs
sports_keywords = ["nba", "nfl", "mlb", "nhl", "soccer", "ufc", "tennis"]

for sport in sports_keywords:
    matching = [e for e in events if sport in e.get("slug", "").lower()]
    if matching:
        print(f"{sport.upper()}: {len(matching)} events")
```

---

## Direct API Access

For full control, you can call the Polymarket APIs directly.

### The two main APIs

| API | Base URL | Purpose |
|-----|----------|---------|
| **Gamma API** | `https://gamma-api.polymarket.com` | Markets, events, metadata |
| **CLOB API** | `https://clob.polymarket.com` | Order books, trading |

### Gamma API: Fetching markets

```python
import requests

response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={
        "limit": 20,
        "active": "true",
        "closed": "false"
    }
)

# Check if request succeeded
if response.status_code == 200:
    markets = response.json()
    print(f"Got {len(markets)} markets")
else:
    print(f"Error: {response.status_code}")
```

### Gamma API: Query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default 100) |
| `offset` | integer | Skip this many results (for pagination) |
| `active` | string | `"true"` or `"false"` |
| `closed` | string | `"true"` or `"false"` |
| `order` | string | `"volume"`, `"createdAt"`, etc. |
| `ascending` | string | `"true"` or `"false"` |

### Gamma API: Fetching events

```python
response = requests.get(
    "https://gamma-api.polymarket.com/events",
    params={
        "limit": 50,
        "closed": "false"
    }
)

events = response.json()
```

### Gamma API: Single market by ID

```python
market_id = "your_market_id_here"
response = requests.get(f"https://gamma-api.polymarket.com/markets/{market_id}")
market = response.json()
```

### CLOB API: Order book

```python
token_id = "your_token_id_here"
response = requests.get(
    "https://clob.polymarket.com/book",
    params={"token_id": token_id}
)

orderbook = response.json()
# Returns: {"bids": [...], "asks": [...]}
```

### Putting it all together

```python
import requests
import json
import pandas as pd

def get_markets_with_orderbooks(limit=10):
    """Fetch markets and their order books."""

    # Step 1: Get markets
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": limit, "active": "true", "closed": "false"}
    )
    markets = response.json()

    results = []

    for market in markets:
        # Step 2: Get token ID
        tokens = market.get("clobTokenIds")
        if not tokens:
            continue

        if isinstance(tokens, str):
            tokens = json.loads(tokens)

        if not tokens:
            continue

        token_id = tokens[0]

        # Step 3: Get order book
        try:
            ob_response = requests.get(
                "https://clob.polymarket.com/book",
                params={"token_id": token_id}
            )
            orderbook = ob_response.json()

            # Calculate spread
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])

            if bids and asks:
                best_bid = float(bids[0]["price"])
                best_ask = float(asks[0]["price"])
                spread = best_ask - best_bid
            else:
                spread = None

            results.append({
                "question": market.get("question"),
                "volume": float(market.get("volume", 0)),
                "spread": spread,
                "bid_levels": len(bids),
                "ask_levels": len(asks)
            })

        except Exception as e:
            continue

    return pd.DataFrame(results)

# Use it
df = get_markets_with_orderbooks(limit=20)
print(df)
```

---

## Common Tasks

### Task 1: Find the most active markets

```python
df = pm.fetch_markets(limit=100, active=True)
top_markets = df.sort_values('volume', ascending=False).head(10)

print("TOP 10 MARKETS BY VOLUME")
for _, row in top_markets.iterrows():
    print(f"${row['volume']:>12,.0f}  {row['question'][:50]}...")
```

### Task 2: Find markets near 50/50

Markets near 50% are the most uncertain - potentially interesting for trading.

```python
df = pm.fetch_markets(limit=100, active=True)

# Find markets between 40% and 60%
uncertain = df[(df['yes_price'] > 0.4) & (df['yes_price'] < 0.6)]
uncertain = uncertain.sort_values('volume', ascending=False)

print(f"Found {len(uncertain)} uncertain markets (40-60%)")
for _, row in uncertain.head(10).iterrows():
    print(f"{row['yes_price']:.0%}  {row['question'][:50]}...")
```

### Task 3: Find markets with tight spreads

Tight spreads = more liquid = easier to trade.

```python
import requests
import json

# Get markets
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={"limit": 30, "active": "true", "closed": "false"}
)
markets = response.json()

# Check spreads
for market in markets[:10]:
    tokens = market.get("clobTokenIds")
    if not tokens:
        continue
    if isinstance(tokens, str):
        tokens = json.loads(tokens)
    if not tokens:
        continue

    try:
        ob = requests.get(
            "https://clob.polymarket.com/book",
            params={"token_id": tokens[0]}
        ).json()

        bids = ob.get("bids", [])
        asks = ob.get("asks", [])

        if bids and asks:
            spread = float(asks[0]["price"]) - float(bids[0]["price"])
            if spread < 0.02:  # Less than 2%
                print(f"Spread: {spread:.2%}  {market.get('question', '')[:50]}...")
    except:
        continue
```

### Task 4: Export data to CSV

```python
df = pm.fetch_markets(limit=100, active=True)
df.to_csv("polymarket_markets.csv", index=False)
print("Saved to polymarket_markets.csv")
```

### Task 5: Compare Polymarket to sports odds

```python
# This is a preview - full implementation coming with OddsHarvester integration

# Polymarket says Lakers have 65% chance to win
polymarket_prob = 0.65

# Bookmaker has Lakers at +150 (American odds)
# Convert to implied probability: 100 / (150 + 100) = 0.40 = 40%
bookmaker_prob = 100 / (150 + 100)

print(f"Polymarket: {polymarket_prob:.0%}")
print(f"Bookmaker:  {bookmaker_prob:.0%}")
print(f"Difference: {abs(polymarket_prob - bookmaker_prob):.0%}")

# If there's a big difference, there might be an opportunity!
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'cuic_quant'"

**Problem:** The package isn't installed.

**Solution:** Run this in your terminal:
```bash
pip install -e .
```

Make sure you're in the project directory (CUIC_Sem2_Project).

### "Connection refused" or timeout errors

**Problem:** Can't reach the Polymarket API.

**Solutions:**
1. Check your internet connection
2. Try again in a few seconds (temporary server issue)
3. Check if Polymarket is down: https://status.polymarket.com/

### Empty DataFrame returned

**Problem:** `pm.fetch_markets()` returns no data.

**Solutions:**
1. Try with `active=False` to include resolved markets
2. Increase the `limit` parameter
3. Check if the API is responding:
   ```python
   import requests
   r = requests.get("https://gamma-api.polymarket.com/markets?limit=1")
   print(r.status_code, r.text[:200])
   ```

### "No markets with active orderbooks found"

**Problem:** Can't find order books for any market.

**Why this happens:**
- Market might be resolved (no more trading)
- Market might have no liquidity
- Token IDs might be missing

**Solution:** Try more markets:
```python
# Increase the search range
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={"limit": 50, "active": "true", "closed": "false"}  # More markets
)
```

### Prices don't add up to 1.0

**Problem:** `yes_price + no_price` doesn't equal 1.0 exactly.

**Why this happens:** This is normal! The difference is the market maker's spread/fee.

```python
# Example:
yes_price = 0.52
no_price = 0.49
total = yes_price + no_price  # = 1.01

# The 0.01 (1%) difference is the "vig" or spread
```

### Rate limiting

**Problem:** Getting 429 errors or requests failing.

**Solution:** Add delays between requests:
```python
import time

for market in markets:
    # ... do something ...
    time.sleep(0.5)  # Wait 0.5 seconds between requests
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Ask** | An order to sell shares at a specified price |
| **Bid** | An order to buy shares at a specified price |
| **CLOB** | Central Limit Order Book - where buy/sell orders are matched |
| **Liquidity** | How easily you can buy/sell without affecting the price |
| **Market** | A single prediction question that can be traded |
| **Order Book** | List of all current buy and sell orders |
| **Prediction Market** | Platform where people trade on event outcomes |
| **Probability** | Chance of an event happening (0% to 100%) |
| **Resolved** | A market that has ended and paid out |
| **Spread** | Difference between best bid and best ask prices |
| **Token** | Digital asset representing YES or NO shares |
| **Volume** | Total amount of money traded on a market |
| **Yes Price** | Current trading price of YES shares (equals probability) |

---

## Next Steps

1. **Run the example notebook:** `research/notebooks/polymarket/data_exploration.ipynb`
2. **Explore different markets:** Try filtering for topics you're interested in
3. **Compare to other data sources:** Once OddsHarvester is set up, compare predictions
4. **Build your own analysis:** Use the API directly to answer research questions

---

## Quick Reference Card

```python
# === SETUP ===
from cuic_quant.notebook import pm
import requests
import json

# === FETCH MARKETS ===
df = pm.fetch_markets(limit=100, active=True)

# === FETCH ORDER BOOK ===
orderbook = pm.fetch_orderbook("token_id_here")
bids = orderbook[orderbook['side'] == 'bid']
asks = orderbook[orderbook['side'] == 'ask']

# === DIRECT API ===
# Markets
requests.get("https://gamma-api.polymarket.com/markets", params={"limit": 50})

# Events (for sports)
requests.get("https://gamma-api.polymarket.com/events", params={"limit": 50})

# Order book
requests.get("https://clob.polymarket.com/book", params={"token_id": "..."})
```

---

## See Also

- [data_exploration.ipynb](./data_exploration.ipynb) - Interactive example notebook
- [Polymarket Docs](https://docs.polymarket.com/) - Official documentation
- [docs/platforms/polymarket.md](../../../docs/platforms/polymarket.md) - Platform overview
