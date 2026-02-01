"""Data clients for prediction markets and sports betting APIs.

This module provides clients for:
- Polymarket: Decentralized prediction market on Polygon
- Kalshi: CFTC-regulated event contracts exchange
- The Odds API: Aggregated sports betting odds

Example:
    >>> from cuic_quant.data import PolymarketClient, KalshiClient, OddsAPIClient
    >>>
    >>> # Polymarket (public endpoints)
    >>> poly = PolymarketClient()
    >>> markets = poly.get_markets()
    >>>
    >>> # Kalshi (requires authentication)
    >>> kalshi = KalshiClient()
    >>> kalshi.login()
    >>> events = kalshi.get_events()
    >>>
    >>> # The Odds API
    >>> odds = OddsAPIClient(api_key="your_key")
    >>> nba_odds = odds.get_odds("basketball_nba")
"""

from cuic_quant.data.kalshi_client import KalshiClient
from cuic_quant.data.odds_api import OddsAPIClient
from cuic_quant.data.polymarket_client import PolymarketClient

__all__ = [
    "PolymarketClient",
    "KalshiClient",
    "OddsAPIClient",
]
