# Polymarket API Guide

Quick reference for accessing Polymarket data directly via API.

**No database or special setup required** - just `pip install -e .` and go.

---

## Quick Start

```python
from cuic_quant.notebook import pm

# Fetch live markets
df = pm.fetch_markets(limit=100, active=True)

# Fetch order book for a market
orderbook = pm.fetch_orderbook("token_id_here")
```

---

## Available Methods

### `pm.fetch_markets(limit, active)`

Fetch markets directly from Polymarket API.

```python
df = pm.fetch_markets(limit=50, active=True)

# Returns DataFrame with columns:
# - id, question, yes_price, no_price, volume, liquidity, status, end_date
```

### `pm.fetch_orderbook(token_id)`

Fetch the order book (bids/asks) for a specific token.

```python
orderbook = pm.fetch_orderbook("your_token_id")

# Returns DataFrame with columns:
# - price, size, side (bid/ask)

# Example usage:
bids = orderbook[orderbook['side'] == 'bid']
asks = orderbook[orderbook['side'] == 'ask']
spread = asks['price'].min() - bids['price'].max()
```

---

## Direct API Access

For more control, use the Polymarket APIs directly with `requests`.

### Gamma API (Markets & Events)

```python
import requests

# Get markets
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={
        "limit": 100,
        "active": "true",
        "closed": "false"
    }
)
markets = response.json()

# Get events (for sports like NBA)
response = requests.get(
    "https://gamma-api.polymarket.com/events",
    params={"limit": 100, "closed": "false"}
)
events = response.json()

# Filter for NBA
nba = [e for e in events if "nba" in e.get("slug", "").lower()]
```

### CLOB API (Order Books)

```python
import requests

token_id = "your_token_id"
response = requests.get(
    f"https://clob.polymarket.com/book",
    params={"token_id": token_id}
)
orderbook = response.json()

# Structure: {"bids": [...], "asks": [...]}
```

---

## API Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| Markets | `https://gamma-api.polymarket.com/markets` | List all markets |
| Events | `https://gamma-api.polymarket.com/events` | Events (sports, etc.) |
| Single Market | `https://gamma-api.polymarket.com/markets/{id}` | Get one market |
| Order Book | `https://clob.polymarket.com/book?token_id=X` | Bids & asks |

---

## Common Parameters

### Markets Endpoint

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (default 100) |
| `offset` | int | Pagination offset |
| `active` | bool | Only active markets |
| `closed` | bool | Include closed markets |

### Events Endpoint

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results |
| `closed` | bool | Include closed events |
| `slug` | string | Filter by event slug |

---

## Example: Find NBA Markets

```python
import requests
import json

# 1. Fetch events
response = requests.get(
    "https://gamma-api.polymarket.com/events",
    params={"limit": 200, "closed": "false"}
)
events = response.json()

# 2. Filter for NBA
nba_events = [e for e in events if "nba" in e.get("slug", "").lower()]

# 3. Extract markets
for event in nba_events:
    print(f"Event: {event.get('title')}")
    for market in event.get("markets", []):
        question = market.get("question")
        volume = float(market.get("volume", 0))
        print(f"  ${volume:,.0f} - {question}")
```

---

## Example: Get Best Bid/Ask

```python
from cuic_quant.notebook import pm

# Get orderbook
orderbook = pm.fetch_orderbook("token_id")

if len(orderbook) > 0:
    bids = orderbook[orderbook['side'] == 'bid']
    asks = orderbook[orderbook['side'] == 'ask']

    best_bid = bids['price'].max() if len(bids) > 0 else 0
    best_ask = asks['price'].min() if len(asks) > 0 else 1
    spread = best_ask - best_bid

    print(f"Best Bid: {best_bid:.4f}")
    print(f"Best Ask: {best_ask:.4f}")
    print(f"Spread: {spread:.4f} ({spread*100:.2f}%)")
```

---

## Rate Limits

Polymarket's public API is generally permissive, but:
- No official rate limit documentation
- Recommend: < 10 requests/second
- Use delays between bulk requests

---

## Notes

- **No authentication required** for read-only access
- Markets use USDC on Polygon network
- `clobTokenIds` contains YES/NO token addresses
- Prices are 0-1 (probability)
- Volume is in USD

---

## See Also

- [Polymarket Docs](https://docs.polymarket.com/)
- [data_exploration.ipynb](./data_exploration.ipynb) - Example notebook
- [docs/platforms/polymarket.md](../../../docs/platforms/polymarket.md) - Platform overview
