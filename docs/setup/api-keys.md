# API Keys Setup Guide

Guide to obtaining and configuring API keys for the CUIC Quant Fund project.

---

## Table of Contents

1. [Overview](#overview)
2. [The Odds API](#the-odds-api)
3. [Polymarket](#polymarket)
4. [Kalshi](#kalshi)
5. [Environment Configuration](#environment-configuration)
6. [Security Best Practices](#security-best-practices)

---

## Overview

This project uses several external APIs. Each team member should obtain their own API keys to avoid rate limiting issues.

### Required APIs

| API | Purpose | Cost | Required |
|-----|---------|------|----------|
| **The Odds API** | Sports betting odds | Free tier available | Recommended |
| **Polymarket** | Prediction market data | Free | Optional |
| **Kalshi** | Event contracts data | Free | Optional |

### Environment File

All API keys are stored in a `.env` file (never committed to git):

```bash
# Copy the example file
cp configs/example.env .env

# Edit with your keys
nano .env  # or your preferred editor
```

---

## The Odds API

**Website:** [the-odds-api.com](https://the-odds-api.com/)

### Getting Your API Key

1. Go to [the-odds-api.com](https://the-odds-api.com/)
2. Click "Get API Key" or "Sign Up"
3. Enter your email address
4. Check your email for the API key

### Free Tier Limits

| Limit | Value |
|-------|-------|
| Requests per month | 500 |
| Sports available | All |
| Historical data | No |

### Testing Your Key

```python
import requests
import os

api_key = os.getenv("ODDS_API_KEY")

response = requests.get(
    "https://api.the-odds-api.com/v4/sports",
    params={"apiKey": api_key}
)

if response.status_code == 200:
    print("API key works!")
    print(f"Available sports: {len(response.json())}")
else:
    print(f"Error: {response.status_code}")
```

### Configuration

Add to your `.env` file:

```env
ODDS_API_KEY=your_key_here
```

---

## Polymarket

**Website:** [polymarket.com](https://polymarket.com/)

### Public vs Private API

| Endpoint Type | Authentication | Use Case |
|---------------|----------------|----------|
| **Public** | None required | Reading market data |
| **Private** | API key required | Trading |

### Getting API Credentials (For Trading)

1. Create account at [polymarket.com](https://polymarket.com/)
2. Connect a wallet (MetaMask recommended)
3. Go to Settings → API
4. Generate API credentials

### Public Endpoints (No Key Required)

Many endpoints work without authentication:

```python
import requests

# Public endpoint - no key needed
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={"limit": 10}
)

markets = response.json()
for market in markets:
    print(f"{market['question']}: {market.get('outcomePrices', 'N/A')}")
```

### Private Endpoints (Key Required)

For trading, you need full authentication:

```env
POLYMARKET_API_KEY=your_api_key
POLYMARKET_API_SECRET=your_api_secret
POLYMARKET_PASSPHRASE=your_passphrase
POLYMARKET_WALLET_ADDRESS=0x...
```

### Important Notes

> **Warning:** Polymarket is not available to US residents. Verify your local regulations before using.

---

## Kalshi

**Website:** [kalshi.com](https://kalshi.com/)

### Getting API Credentials

1. Create account at [kalshi.com](https://kalshi.com/)
2. Complete identity verification (KYC)
3. Go to Settings → API (or use email/password auth)

### Authentication Methods

**Option 1: Email/Password (Simpler)**

```python
import requests

# Login to get session token
response = requests.post(
    "https://trading-api.kalshi.com/trade-api/v2/login",
    json={
        "email": os.getenv("KALSHI_EMAIL"),
        "password": os.getenv("KALSHI_PASSWORD"),
    }
)

token = response.json()["token"]
```

**Option 2: API Keys (More Secure)**

Generate API keys from your account settings.

### Demo Environment

Kalshi offers a demo environment for testing:

```env
# Production
KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2

# Demo (for testing)
KALSHI_API_URL=https://demo-api.kalshi.co/trade-api/v2
```

### Configuration

Add to your `.env` file:

```env
# Option 1: Email/Password
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password

# Option 2: API Keys (if available)
KALSHI_API_KEY=your_api_key
KALSHI_API_SECRET=your_api_secret

# Environment (demo for testing, trading-api for production)
KALSHI_API_URL=https://demo-api.kalshi.co/trade-api/v2
```

### Testing Your Credentials

```python
import requests
import os

# Login
response = requests.post(
    f"{os.getenv('KALSHI_API_URL')}/login",
    json={
        "email": os.getenv("KALSHI_EMAIL"),
        "password": os.getenv("KALSHI_PASSWORD"),
    }
)

if response.status_code == 200:
    print("Login successful!")
    print(f"Token: {response.json()['token'][:20]}...")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

---

## Environment Configuration

### Complete .env Template

Create your `.env` file with all available keys:

```env
# =============================================================================
# CUIC Quant Fund - Environment Variables
# =============================================================================
# NEVER commit this file to git!

# -----------------------------------------------------------------------------
# The Odds API
# https://the-odds-api.com/
# -----------------------------------------------------------------------------
ODDS_API_KEY=

# -----------------------------------------------------------------------------
# Polymarket (optional - for trading)
# https://polymarket.com/
# Note: Not available to US residents
# -----------------------------------------------------------------------------
POLYMARKET_API_KEY=
POLYMARKET_API_SECRET=
POLYMARKET_PASSPHRASE=
POLYMARKET_WALLET_ADDRESS=

# -----------------------------------------------------------------------------
# Kalshi
# https://kalshi.com/
# -----------------------------------------------------------------------------
KALSHI_EMAIL=
KALSHI_PASSWORD=
# Or use API keys:
# KALSHI_API_KEY=
# KALSHI_API_SECRET=

# Use demo environment for testing:
KALSHI_API_URL=https://demo-api.kalshi.co/trade-api/v2
# Production:
# KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Data cache directory (relative to project root)
CACHE_DIR=data/cache
```

### Loading Environment Variables

In Python code:

```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access variables
odds_key = os.getenv("ODDS_API_KEY")
kalshi_email = os.getenv("KALSHI_EMAIL")

# With defaults
log_level = os.getenv("LOG_LEVEL", "INFO")
```

In our API clients:

```python
from cuic_quant.data import OddsAPIClient

# Client loads from environment automatically
client = OddsAPIClient()  # Uses ODDS_API_KEY from .env

# Or pass explicitly
client = OddsAPIClient(api_key="your_key")
```

---

## Security Best Practices

### Never Commit Credentials

The `.env` file is in `.gitignore`. Never commit it.

```bash
# Check if .env is tracked
git status

# If accidentally added, remove from tracking
git rm --cached .env
```

### Use Environment Variables

Never hardcode credentials:

```python
# BAD - Never do this!
api_key = "sk_live_12345abcdef"

# GOOD - Use environment variables
api_key = os.getenv("API_KEY")

# BETTER - Fail if not set
api_key = os.environ["API_KEY"]  # Raises KeyError if missing
```

### Rotate Compromised Keys

If a key is accidentally exposed:

1. **Immediately** revoke/regenerate the key on the provider's website
2. Update your `.env` file with the new key
3. Check git history for the exposed key
4. If in git history, consider it permanently compromised

### Separate Development and Production

```env
# Development
KALSHI_API_URL=https://demo-api.kalshi.co/trade-api/v2

# Production (only on secure servers)
# KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2
```

### Key Permissions

Request minimum necessary permissions:

| API | Recommended Scope |
|-----|-------------------|
| The Odds API | Read only (default) |
| Polymarket | Read only (unless trading) |
| Kalshi | Demo environment for development |

---

## Verification Script

Run this script to verify all your API keys:

```python
"""Verify API key configuration."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def check_odds_api() -> bool:
    """Check The Odds API key."""
    key = os.getenv("ODDS_API_KEY")
    if not key:
        print("❌ ODDS_API_KEY not set")
        return False

    response = requests.get(
        "https://api.the-odds-api.com/v4/sports",
        params={"apiKey": key},
        timeout=10,
    )

    if response.status_code == 200:
        print(f"✅ The Odds API: {len(response.json())} sports available")
        return True
    else:
        print(f"❌ The Odds API: {response.status_code} - {response.text}")
        return False


def check_kalshi() -> bool:
    """Check Kalshi credentials."""
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")
    api_url = os.getenv("KALSHI_API_URL", "https://demo-api.kalshi.co/trade-api/v2")

    if not email or not password:
        print("❌ KALSHI_EMAIL or KALSHI_PASSWORD not set")
        return False

    response = requests.post(
        f"{api_url}/login",
        json={"email": email, "password": password},
        timeout=10,
    )

    if response.status_code == 200:
        print(f"✅ Kalshi: Logged in successfully (using {api_url})")
        return True
    else:
        print(f"❌ Kalshi: {response.status_code} - {response.json()}")
        return False


def check_polymarket() -> bool:
    """Check Polymarket (public endpoint only)."""
    # Public endpoint doesn't require auth
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"limit": 1},
        timeout=10,
    )

    if response.status_code == 200:
        print("✅ Polymarket: Public API accessible")
        return True
    else:
        print(f"❌ Polymarket: {response.status_code}")
        return False


if __name__ == "__main__":
    print("Checking API configurations...\n")

    results = {
        "The Odds API": check_odds_api(),
        "Kalshi": check_kalshi(),
        "Polymarket": check_polymarket(),
    }

    print("\n" + "=" * 40)
    print("Summary:")
    for api, success in results.items():
        status = "✅ OK" if success else "❌ Failed"
        print(f"  {api}: {status}")
```

Save as `scripts/check_api_keys.py` and run:

```bash
python scripts/check_api_keys.py
```

---

## Next Steps

1. Copy `configs/example.env` to `.env`
2. Obtain API keys for services you'll use
3. Run the verification script
4. Review [Environment Setup](environment-setup.md)
5. Start building with our API clients in `src/cuic_quant/data/`
