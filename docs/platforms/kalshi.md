# Kalshi Guide

A comprehensive guide to Kalshi, the first CFTC-regulated prediction market exchange in the United States.

---

## Table of Contents

1. [What is Kalshi?](#what-is-kalshi)
2. [Regulatory Framework](#regulatory-framework)
3. [How It Works](#how-it-works)
4. [Market Types](#market-types)
5. [API Overview](#api-overview)
6. [Python Client Usage](#python-client-usage)
7. [Strategies](#strategies)
8. [Resources](#resources)

---

## What is Kalshi?

**Kalshi** is the first legal, regulated prediction market exchange in the United States. It operates as a Designated Contract Market (DCM) under the oversight of the Commodity Futures Trading Commission (CFTC).

### Key Facts

| Attribute | Value |
|-----------|-------|
| **Founded** | 2018 |
| **Launched** | July 2021 |
| **Regulator** | CFTC (Commodity Futures Trading Commission) |
| **Currency** | USD |
| **Headquarters** | New York, USA |
| **2024 Volume** | $1B+ in event contracts |
| **Available To** | US residents (most states) |

### Why Kalshi Matters for Quant Research

1. **Regulatory Legitimacy**: CFTC oversight provides legal certainty
2. **US Access**: Available to US traders (unlike Polymarket)
3. **Novel Asset Class**: Event contracts are a new financial instrument
4. **Clean Data**: Regulated exchange provides reliable price data
5. **Growing Liquidity**: Rapidly expanding market depth

---

## Regulatory Framework

### CFTC Oversight

Kalshi operates under CFTC regulations as a Designated Contract Market (DCM), similar to CME or CBOE. This means:

- **Capital Requirements**: Kalshi must maintain minimum capital
- **Customer Protection**: Segregated customer funds
- **Market Surveillance**: Continuous monitoring for manipulation
- **Reporting**: Regular regulatory filings

### Event Contracts

Kalshi trades **event contracts** - binary options on real-world events:

```
Contract: "Will US GDP growth exceed 2% in Q1 2025?"

- Pays $1.00 if YES
- Pays $0.00 if NO
- Current price: $0.72 (72% implied probability)
- Max loss: Purchase price
- Max gain: $1.00 - Purchase price
```

### Position Limits

| Category | Limit |
|----------|-------|
| Single Event | Varies by contract (typically $25,000-$250,000) |
| Daily Volume | No limit |
| Account Minimum | $0 (no minimum) |

---

## How It Works

### 1. Account Setup

1. Create account at [kalshi.com](https://kalshi.com)
2. Complete identity verification (KYC)
3. Link bank account or debit card
4. Deposit USD

### 2. Trading Mechanism

Kalshi uses a **central limit order book (CLOB)**:

```
Market: "Fed raises rates in January 2025"

BIDS (Buy YES)           ASKS (Sell YES)
$0.45 × 500 contracts    $0.47 × 300 contracts
$0.44 × 1,200 contracts  $0.48 × 800 contracts
$0.43 × 2,000 contracts  $0.49 × 1,500 contracts

Spread: $0.02 (2 cents)
```

### 3. Order Types

| Order Type | Description |
|------------|-------------|
| **Market** | Execute immediately at best available price |
| **Limit** | Execute only at specified price or better |
| **IOC** | Immediate-or-cancel: fill what's available, cancel rest |

### 4. Settlement

Events settle based on official sources specified in contract rules:

```python
# Example settlement sources
settlement_sources = {
    "inflation": "Bureau of Labor Statistics CPI release",
    "gdp": "Bureau of Economic Analysis GDP release",
    "weather": "National Weather Service official data",
    "elections": "Associated Press race calls",
}
```

---

## Market Types

### Economic Indicators

```
- "Will CPI inflation exceed 3.0% in December 2025?"
- "Will unemployment fall below 4.0% in January 2025?"
- "Will GDP growth exceed 2.5% in Q1 2025?"
- "Will the Fed cut rates by 25bp+ in March 2025?"
```

### Weather Events

```
- "Will NYC temperature exceed 90°F on July 15, 2025?"
- "Will a Category 3+ hurricane make US landfall in August 2025?"
- "Will total snowfall in Chicago exceed 5 inches in January 2025?"
```

### Finance & Markets

```
- "Will S&P 500 close above 5,500 on December 31, 2025?"
- "Will Bitcoin close above $100,000 on January 1, 2025?"
- "Will Apple earnings beat consensus estimates in Q4 2025?"
```

### Politics & Elections

```
- "Will [Candidate] win [State] in the 2024 election?"
- "Will Congress pass [Bill] by [Date]?"
- "Will the government shutdown last more than 7 days?"
```

### Technology & Science

```
- "Will GPT-5 be released before July 2025?"
- "Will SpaceX complete a successful Starship orbital flight by March 2025?"
```

---

## API Overview

### Base URL

```
Production: https://trading-api.kalshi.com/trade-api/v2
Demo: https://demo-api.kalshi.co/trade-api/v2
```

### Authentication

Kalshi uses email/password authentication to obtain a session token:

```python
import requests

# Login to get session token
response = requests.post(
    "https://trading-api.kalshi.com/trade-api/v2/login",
    json={
        "email": "your_email@example.com",
        "password": "your_password",
    },
)

token = response.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
```

### Key Endpoints

#### Get Markets

```http
GET /markets
Authorization: Bearer {token}

Query Parameters:
- status: active, closed, settled
- series_ticker: Filter by series (e.g., "INFL" for inflation)
- cursor: Pagination cursor
- limit: Results per page (max 200)
```

Response:
```json
{
  "markets": [
    {
      "ticker": "INFL-25JAN-T3.0",
      "title": "Inflation above 3.0% in January 2025?",
      "status": "active",
      "yes_bid": 0.72,
      "yes_ask": 0.74,
      "no_bid": 0.26,
      "no_ask": 0.28,
      "volume": 15000,
      "open_interest": 8500,
      "close_time": "2025-02-12T14:30:00Z"
    }
  ],
  "cursor": "next_page_cursor"
}
```

#### Get Order Book

```http
GET /markets/{ticker}/orderbook
Authorization: Bearer {token}

Query Parameters:
- depth: Number of levels (default 10)
```

Response:
```json
{
  "yes": {
    "bids": [
      {"price": 72, "quantity": 500},
      {"price": 71, "quantity": 1200}
    ],
    "asks": [
      {"price": 74, "quantity": 300},
      {"price": 75, "quantity": 800}
    ]
  },
  "no": {
    "bids": [...],
    "asks": [...]
  }
}
```

#### Place Order

```http
POST /portfolio/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "ticker": "INFL-25JAN-T3.0",
  "action": "buy",
  "side": "yes",
  "type": "limit",
  "count": 100,
  "price": 72
}
```

Response:
```json
{
  "order": {
    "order_id": "abc123",
    "ticker": "INFL-25JAN-T3.0",
    "status": "resting",
    "action": "buy",
    "side": "yes",
    "type": "limit",
    "count": 100,
    "remaining_count": 100,
    "price": 72,
    "created_time": "2025-01-15T10:30:00Z"
  }
}
```

#### Get Portfolio

```http
GET /portfolio/balance
Authorization: Bearer {token}
```

```http
GET /portfolio/positions
Authorization: Bearer {token}
```

---

## Python Client Usage

### Basic Setup

```python
"""Kalshi API client example."""

import os
from cuic_quant.data.kalshi_client import KalshiClient

# Initialize client
client = KalshiClient(
    email=os.getenv("KALSHI_EMAIL"),
    password=os.getenv("KALSHI_PASSWORD"),
    demo=True,  # Use demo environment for testing
)

# Login
client.login()

# Check balance
balance = client.get_balance()
print(f"Available balance: ${balance.available:,.2f}")
```

### Fetching Markets

```python
# Get all active markets
markets = client.get_markets(status="active")
print(f"Found {len(markets)} active markets")

# Filter by series
inflation_markets = client.get_markets(
    status="active",
    series_ticker="INFL",
)

for market in inflation_markets[:5]:
    print(f"{market.ticker}: {market.title}")
    print(f"  YES: ${market.yes_bid:.2f} / ${market.yes_ask:.2f}")
    print(f"  Volume: {market.volume:,} contracts")
```

### Getting Order Book

```python
# Fetch order book
orderbook = client.get_orderbook(ticker="INFL-25JAN-T3.0")

print("YES Side:")
print("  Bids:", orderbook.yes.bids[:3])
print("  Asks:", orderbook.yes.asks[:3])

# Calculate mid price
yes_mid = (orderbook.yes.bids[0].price + orderbook.yes.asks[0].price) / 2
print(f"  Mid: ${yes_mid / 100:.2f}")  # Prices in cents
```

### Placing Orders

```python
# Place a limit order (demo mode)
order = client.place_order(
    ticker="INFL-25JAN-T3.0",
    action="buy",
    side="yes",
    order_type="limit",
    count=10,
    price=70,  # Price in cents
)

print(f"Order placed: {order.order_id}")
print(f"Status: {order.status}")

# Cancel order
client.cancel_order(order_id=order.order_id)
```

### Historical Data

```python
import pandas as pd

# Get trade history
trades = client.get_trades(
    ticker="INFL-25JAN-T3.0",
    min_ts="2025-01-01T00:00:00Z",
    max_ts="2025-01-15T00:00:00Z",
)

# Convert to DataFrame
df = pd.DataFrame([
    {
        "timestamp": t.created_time,
        "price": t.yes_price / 100,
        "count": t.count,
    }
    for t in trades
])

df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# Resample to hourly OHLC
ohlc = df["price"].resample("1h").ohlc()
print(ohlc.head())
```

---

## Strategies

### 1. Economic Calendar Trading

Trade around scheduled economic releases:

```python
from datetime import datetime, timedelta

def find_pre_release_opportunities(
    client: KalshiClient,
    release_date: datetime,
    series: str = "INFL",
) -> list:
    """Find markets settling soon after economic release.

    Strategy: Volatility typically increases before releases,
    then settles rapidly after the data is announced.

    Args:
        client: Kalshi API client
        release_date: Date of economic release
        series: Market series to search

    Returns:
        List of relevant markets
    """
    markets = client.get_markets(
        status="active",
        series_ticker=series,
    )

    relevant = []
    for market in markets:
        close_time = datetime.fromisoformat(market.close_time.replace("Z", "+00:00"))

        # Markets closing within 48 hours of release
        if release_date <= close_time <= release_date + timedelta(hours=48):
            spread = market.yes_ask - market.yes_bid
            relevant.append({
                "market": market,
                "spread": spread,
                "hours_to_close": (close_time - release_date).total_seconds() / 3600,
            })

    return sorted(relevant, key=lambda x: x["spread"])
```

### 2. Weather Model Alpha

Use weather forecasting models for edge:

```python
def weather_model_signal(
    market_ticker: str,
    model_probability: float,
    client: KalshiClient,
) -> dict:
    """Compare weather model forecast to market price.

    Args:
        market_ticker: Kalshi market ticker
        model_probability: Your model's probability estimate (0-1)
        client: Kalshi API client

    Returns:
        Trading signal with edge calculation
    """
    market = client.get_market(market_ticker)

    # Market implied probability (using mid price)
    market_prob = (market.yes_bid + market.yes_ask) / 2 / 100

    edge = model_probability - market_prob

    return {
        "ticker": market_ticker,
        "model_prob": model_probability,
        "market_prob": market_prob,
        "edge": edge,
        "signal": "BUY_YES" if edge > 0.05 else "BUY_NO" if edge < -0.05 else "HOLD",
        "confidence": abs(edge),
    }
```

### 3. Cross-Event Correlation

Find correlated events that should move together:

```python
def find_correlation_opportunities(
    markets: list,
    correlation_pairs: list[tuple[str, str, float]],
) -> list:
    """Find mispricings in correlated markets.

    Args:
        markets: List of market data
        correlation_pairs: List of (ticker1, ticker2, expected_correlation)

    Returns:
        List of potential opportunities
    """
    market_dict = {m.ticker: m for m in markets}
    opportunities = []

    for ticker1, ticker2, expected_corr in correlation_pairs:
        if ticker1 not in market_dict or ticker2 not in market_dict:
            continue

        m1 = market_dict[ticker1]
        m2 = market_dict[ticker2]

        # Calculate implied probabilities
        p1 = (m1.yes_bid + m1.yes_ask) / 2 / 100
        p2 = (m2.yes_bid + m2.yes_ask) / 2 / 100

        # If highly correlated events, prices should be similar
        if expected_corr > 0.8:
            price_diff = abs(p1 - p2)
            if price_diff > 0.10:  # 10% divergence
                opportunities.append({
                    "pair": (ticker1, ticker2),
                    "prices": (p1, p2),
                    "divergence": price_diff,
                    "action": f"Buy {ticker1 if p1 < p2 else ticker2}, Sell {ticker2 if p1 < p2 else ticker1}",
                })

    return opportunities
```

### 4. Limit Order Market Making

Provide liquidity and earn the spread:

```python
def market_making_quotes(
    market: dict,
    fair_value: float,
    spread_width: float = 0.04,
    size: int = 100,
) -> dict:
    """Generate two-sided quotes around fair value.

    Args:
        market: Market data
        fair_value: Your estimated fair value (0-1)
        spread_width: Total spread to capture
        size: Contract size per side

    Returns:
        Bid and ask quotes
    """
    half_spread = spread_width / 2

    bid_price = int((fair_value - half_spread) * 100)
    ask_price = int((fair_value + half_spread) * 100)

    # Ensure within valid range
    bid_price = max(1, min(99, bid_price))
    ask_price = max(1, min(99, ask_price))

    return {
        "bid": {"side": "yes", "action": "buy", "price": bid_price, "count": size},
        "ask": {"side": "yes", "action": "sell", "price": ask_price, "count": size},
        "expected_profit_per_round_trip": spread_width * size,
    }
```

---

## Resources

### Official Documentation

- [Kalshi API Docs](https://trading-api.readme.io/reference/getting-started)
- [Market Rules](https://kalshi.com/documents/market-rules)
- [Fee Schedule](https://kalshi.com/fee-schedule)

### Community

- [Kalshi Discord](https://discord.gg/kalshi)
- [Twitter/X](https://twitter.com/Kalshi)
- [Reddit r/Kalshi](https://reddit.com/r/Kalshi)

### Academic Research

- Event Contract Markets: Theory and Evidence
- Prediction Market Accuracy in Regulated Environments
- The Role of Information in Event Contract Pricing

---

## Demo Trading

Kalshi offers a demo environment for testing strategies without risking real money:

```python
# Use demo environment
demo_client = KalshiClient(
    email=os.getenv("KALSHI_EMAIL"),
    password=os.getenv("KALSHI_PASSWORD"),
    demo=True,  # Connect to demo API
)

# Demo environment has $100,000 virtual balance
# All API calls work identically to production
```

---

## Fees

| Fee Type | Amount |
|----------|--------|
| Trading Fee | $0.01 per contract (both sides) |
| Settlement Fee | $0.00 |
| Deposit Fee | $0.00 (ACH) |
| Withdrawal Fee | $0.00 (ACH) |

---

## Next Steps

1. Create account at [kalshi.com](https://kalshi.com)
2. Complete verification
3. Practice in demo environment
4. Set up API credentials (see [API Keys Guide](../setup/api-keys.md))
5. Review the [Polymarket Guide](polymarket.md) for comparison
