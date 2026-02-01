# Polymarket Guide

A comprehensive guide to Polymarket, the world's largest decentralized prediction market.

---

## Table of Contents

1. [What is Polymarket?](#what-is-polymarket)
2. [How It Works](#how-it-works)
3. [Key Concepts](#key-concepts)
4. [Market Types](#market-types)
5. [API Overview](#api-overview)
6. [Python Client Usage](#python-client-usage)
7. [Strategies](#strategies)
8. [Resources](#resources)

---

## What is Polymarket?

**Polymarket** is a decentralized prediction market platform built on the Polygon blockchain. It allows users to trade on the outcomes of real-world events, from political elections to sports outcomes to economic indicators.

### Key Facts

| Attribute | Value |
|-----------|-------|
| **Founded** | 2020 |
| **Blockchain** | Polygon (MATIC) |
| **Currency** | USDC (stablecoin) |
| **Settlement** | UMA Optimistic Oracle |
| **Headquarters** | New York, USA |
| **2024 Volume** | $9B+ traded |

### Why Polymarket Matters for Quant Research

1. **Price Discovery**: Markets aggregate information efficiently
2. **Real-time Probabilities**: Prices reflect crowd wisdom
3. **Arbitrage Opportunities**: Mispricings between markets
4. **Novel Alpha**: Less competition than traditional markets
5. **24/7 Trading**: Continuous liquidity

---

## How It Works

### 1. Market Creation

Markets are created for binary or multi-outcome events:

```
Example Market: "Will Bitcoin exceed $100,000 by December 31, 2025?"

Outcomes:
- YES: Currently trading at $0.65 (65% implied probability)
- NO: Currently trading at $0.35 (35% implied probability)

Total always equals ~$1.00 (minus spread)
```

### 2. Trading Mechanism

Polymarket uses an **order book model** similar to traditional exchanges:

```
Bid/Ask for "Trump wins 2024"

BIDS (Buy YES)          ASKS (Sell YES)
$0.52 × 10,000         $0.53 × 5,000
$0.51 × 25,000         $0.54 × 15,000
$0.50 × 50,000         $0.55 × 8,000
```

### 3. Settlement

When an event resolves:
- **YES shares** pay out **$1.00** if the event occurs
- **NO shares** pay out **$1.00** if the event doesn't occur
- Settlement uses UMA's Optimistic Oracle

### 4. Flow Diagram

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Deposit    │───▶│   Trade      │───▶│   Settle    │
│   USDC      │    │  YES/NO      │    │  at $1/$0   │
└─────────────┘    └──────────────┘    └─────────────┘
      │                   │                    │
      ▼                   ▼                    ▼
  Polygon            Order Book            UMA Oracle
  Wallet            Matching               Resolution
```

---

## Key Concepts

### Implied Probability

The market price directly represents the implied probability:

```python
# Price to probability
implied_prob = share_price  # $0.65 = 65% probability

# Probability to fair price
fair_price = estimated_probability  # 70% = $0.70
```

### Expected Value (EV)

```python
def calculate_ev(your_probability: float, market_price: float) -> float:
    """Calculate expected value of buying YES shares.

    Args:
        your_probability: Your estimated probability (0-1)
        market_price: Current YES price (0-1)

    Returns:
        Expected profit per dollar risked

    Example:
        >>> calculate_ev(0.70, 0.60)  # You think 70%, market says 60%
        0.167  # +16.7% expected return
    """
    # If YES wins, you get $1 for each share bought at market_price
    # If NO wins, you lose your investment
    profit_if_yes = (1 - market_price) / market_price
    loss_if_no = -1  # Lose entire stake

    ev = (your_probability * profit_if_yes) + ((1 - your_probability) * loss_if_no)
    return ev
```

### The Spread

```python
# Typical market spread
yes_bid = 0.52  # Best price to sell YES
yes_ask = 0.54  # Best price to buy YES
no_bid = 0.46   # Best price to sell NO
no_ask = 0.48   # Best price to buy NO

spread = yes_ask - yes_bid  # $0.02 = 2 cents
spread_percentage = spread / yes_ask * 100  # 3.7%

# Note: yes_ask + no_ask > $1.00 (this is the house edge)
combined_ask = yes_ask + no_ask  # $1.02
vig = combined_ask - 1.00  # $0.02 = 2% vigorish
```

---

## Market Types

### Binary Markets

Simple YES/NO outcomes:

```
"Will inflation exceed 3% in December 2025?"
- YES: $0.45
- NO: $0.55
```

### Multi-Outcome Markets

Multiple possible outcomes (sum to ~100%):

```
"Who will win the 2028 Presidential Election?"
- Candidate A: $0.35
- Candidate B: $0.30
- Candidate C: $0.20
- Candidate D: $0.10
- Other: $0.05
```

### Conditional Markets

Markets dependent on other events:

```
"If Democrats win, will X policy pass?"
```

---

## API Overview

### Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://clob.polymarket.com` |
| Gamma API | `https://gamma-api.polymarket.com` |

### Authentication

Polymarket uses API keys for authenticated endpoints:

```python
import os

API_KEY = os.getenv("POLYMARKET_API_KEY")
API_SECRET = os.getenv("POLYMARKET_API_SECRET")
PASSPHRASE = os.getenv("POLYMARKET_PASSPHRASE")
```

### Key Endpoints

#### Get Markets (Public)

```http
GET https://gamma-api.polymarket.com/markets
```

Response:
```json
{
  "markets": [
    {
      "id": "0x...",
      "question": "Will BTC exceed $100k by Dec 2025?",
      "outcomes": ["Yes", "No"],
      "outcomePrices": ["0.65", "0.35"],
      "volume": "5000000",
      "liquidity": "250000",
      "endDate": "2025-12-31T23:59:59Z"
    }
  ]
}
```

#### Get Order Book

```http
GET https://clob.polymarket.com/book?token_id={token_id}
```

Response:
```json
{
  "bids": [
    {"price": "0.52", "size": "10000"},
    {"price": "0.51", "size": "25000"}
  ],
  "asks": [
    {"price": "0.53", "size": "5000"},
    {"price": "0.54", "size": "15000"}
  ]
}
```

#### Place Order (Authenticated)

```http
POST https://clob.polymarket.com/order
Content-Type: application/json
POLY_ADDRESS: {your_address}
POLY_SIGNATURE: {signature}
POLY_TIMESTAMP: {timestamp}
POLY_NONCE: {nonce}

{
  "tokenID": "0x...",
  "price": "0.52",
  "size": "100",
  "side": "BUY",
  "orderType": "GTC"
}
```

---

## Python Client Usage

### Basic Setup

```python
"""Polymarket API client example."""

import os
from cuic_quant.data.polymarket_client import PolymarketClient

# Initialize client
client = PolymarketClient(
    api_key=os.getenv("POLYMARKET_API_KEY"),
    api_secret=os.getenv("POLYMARKET_API_SECRET"),
)

# Fetch all active markets
markets = client.get_markets()
print(f"Found {len(markets)} active markets")
```

### Fetching Market Data

```python
# Get specific market
market = client.get_market(market_id="0x...")

print(f"Question: {market.question}")
print(f"YES Price: ${market.yes_price:.2f}")
print(f"NO Price: ${market.no_price:.2f}")
print(f"Volume: ${market.volume:,.0f}")
print(f"Ends: {market.end_date}")
```

### Getting Order Book

```python
# Fetch order book
orderbook = client.get_orderbook(token_id="0x...")

print("Top 5 Bids:")
for bid in orderbook.bids[:5]:
    print(f"  ${bid.price:.2f} × {bid.size:,.0f}")

print("Top 5 Asks:")
for ask in orderbook.asks[:5]:
    print(f"  ${ask.price:.2f} × {ask.size:,.0f}")
```

### Historical Prices

```python
import pandas as pd

# Get price history
history = client.get_price_history(
    market_id="0x...",
    interval="1h",
    start_date="2025-01-01",
    end_date="2025-01-31",
)

# Convert to DataFrame
df = pd.DataFrame(history)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

print(df.head())
#                      yes_price  no_price  volume
# timestamp
# 2025-01-01 00:00:00      0.52      0.48   50000
# 2025-01-01 01:00:00      0.53      0.47   45000
```

---

## Strategies

### 1. Information Edge

Use superior information or analysis to identify mispricings:

```python
def find_mispriced_markets(
    markets: list,
    model_probabilities: dict[str, float],
    min_edge: float = 0.05,
) -> list:
    """Find markets where model disagrees with market price.

    Args:
        markets: List of market objects
        model_probabilities: Dict mapping market_id to model probability
        min_edge: Minimum edge to consider (default 5%)

    Returns:
        List of (market, edge, direction) tuples
    """
    opportunities = []

    for market in markets:
        if market.id not in model_probabilities:
            continue

        model_prob = model_probabilities[market.id]
        market_prob = market.yes_price

        edge = model_prob - market_prob

        if abs(edge) >= min_edge:
            direction = "BUY_YES" if edge > 0 else "BUY_NO"
            opportunities.append((market, abs(edge), direction))

    return sorted(opportunities, key=lambda x: x[1], reverse=True)
```

### 2. Cross-Market Arbitrage

Find mispricings between related markets:

```python
def find_arbitrage(
    market_a: dict,
    market_b: dict,
    relationship: str = "sum_to_one",
) -> dict | None:
    """Find arbitrage between related markets.

    Example: "Trump wins" + "Trump loses" should sum to ~$1.00

    Args:
        market_a: First market data
        market_b: Second market data
        relationship: How markets relate

    Returns:
        Arbitrage opportunity details or None
    """
    if relationship == "sum_to_one":
        # These should be complementary
        combined_cost = market_a["yes_ask"] + market_b["yes_ask"]

        if combined_cost < 1.0:
            profit = 1.0 - combined_cost
            return {
                "type": "guaranteed_profit",
                "buy": [
                    (market_a["id"], "YES", market_a["yes_ask"]),
                    (market_b["id"], "YES", market_b["yes_ask"]),
                ],
                "profit_per_dollar": profit / combined_cost,
            }

    return None
```

### 3. Mean Reversion

Markets often overreact to news:

```python
import numpy as np

def calculate_mean_reversion_signal(
    prices: list[float],
    lookback: int = 24,
    threshold: float = 2.0,
) -> str:
    """Generate mean reversion signal.

    Args:
        prices: Historical prices
        lookback: Period for mean/std calculation
        threshold: Z-score threshold for signal

    Returns:
        'BUY', 'SELL', or 'HOLD'
    """
    if len(prices) < lookback:
        return "HOLD"

    recent_prices = prices[-lookback:]
    mean = np.mean(recent_prices)
    std = np.std(recent_prices)

    current = prices[-1]
    z_score = (current - mean) / std if std > 0 else 0

    if z_score < -threshold:
        return "BUY"  # Price below mean, expect reversion up
    elif z_score > threshold:
        return "SELL"  # Price above mean, expect reversion down
    else:
        return "HOLD"
```

---

## Resources

### Official Documentation

- [Polymarket Docs](https://docs.polymarket.com/)
- [API Reference](https://docs.polymarket.com/#api)
- [Trading Guide](https://polymarket.com/trading)

### Community

- [Polymarket Discord](https://discord.gg/polymarket)
- [Twitter/X](https://twitter.com/Polymarket)

### Academic Papers

- Prediction Markets: Theory and Applications
- The Wisdom of Crowds in Prediction Markets
- Market Microstructure and Prediction Markets

### Related Tools

- [py-clob-client](https://github.com/Polymarket/py-clob-client) - Official Python client
- [Polymarket Subgraph](https://thegraph.com/hosted-service/subgraph/polymarket/polymarket-matic)

---

## Legal Considerations

> **Note**: Polymarket is not available to US residents due to regulatory restrictions. Always ensure compliance with local laws before trading on prediction markets.

---

## Next Steps

1. Set up API credentials (see [API Keys Guide](../setup/api-keys.md))
2. Explore live markets at [polymarket.com](https://polymarket.com)
3. Review the [Kalshi Guide](kalshi.md) for a regulated alternative
4. Start with paper trading before risking real capital
