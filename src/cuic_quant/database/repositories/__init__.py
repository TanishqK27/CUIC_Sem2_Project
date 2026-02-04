"""Repository layer for database access.

This module provides repository classes that encapsulate database queries
and provide a clean interface for accessing Polymarket data from both
API endpoints and Jupyter notebooks.

Example:
    >>> from cuic_quant.database.repositories import MarketRepository
    >>>
    >>> repo = MarketRepository()
    >>> markets = repo.get_latest_markets(limit=10)
    >>> df = repo.get_markets_df(limit=100, active_only=True)
"""

from cuic_quant.database.repositories.market_repo import MarketRepository

__all__ = ["MarketRepository"]
