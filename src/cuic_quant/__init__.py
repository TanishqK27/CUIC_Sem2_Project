"""CUIC Quant Fund - Quantitative Research for Prediction Markets & Sports Betting.

This package provides tools for:
- API clients for prediction markets (Polymarket, Kalshi) and sports betting odds
- Statistical models for probability estimation
- Trading strategies (arbitrage, mean reversion, Kelly criterion)
- Backtesting framework for strategy validation

Example:
    >>> from cuic_quant.data import PolymarketClient
    >>> client = PolymarketClient()
    >>> markets = client.get_markets()

    >>> from cuic_quant.strategies import calculate_kelly_fraction
    >>> fraction = calculate_kelly_fraction(0.55, 2.0)
"""

__version__ = "0.1.0"
__author__ = "Cardiff University Investment Club Quant Team"

# Convenience imports
from cuic_quant.data import KalshiClient, OddsAPIClient, PolymarketClient
from cuic_quant.strategies import (
    calculate_kelly_fraction,
    find_arbitrage,
    mean_reversion_signal,
)

__all__ = [
    # Data clients
    "PolymarketClient",
    "KalshiClient",
    "OddsAPIClient",
    # Strategies
    "calculate_kelly_fraction",
    "find_arbitrage",
    "mean_reversion_signal",
]
