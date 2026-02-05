"""Data clients for prediction markets and sports betting APIs.

This module provides unified access to various data sources:
- KalshiClient: CFTC-regulated event contracts
- OddsAPIClient: Aggregated sports betting odds
"""

from cuic_quant.data.kalshi_client import KalshiClient
from cuic_quant.data.odds_api import OddsAPIClient

__all__ = ["KalshiClient", "OddsAPIClient"]
