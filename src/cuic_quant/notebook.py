"""Convenience functions for Jupyter notebook research.

This module provides easy access to both live API data and stored database data.
It is designed to make research workflows in Jupyter notebooks as smooth as
possible, with DataFrame outputs for all queries and lazy-loading of dependencies.

Example:
    >>> from cuic_quant.notebook import pm
    >>>
    >>> # Get live data from API
    >>> df = pm.fetch_markets(limit=100)
    >>>
    >>> # Get stored data from database
    >>> df = pm.load_markets(limit=100)
    >>>
    >>> # Get price history
    >>> prices = pm.load_prices("0x123...")
    >>>
    >>> # Search for specific markets
    >>> results = pm.search("election")
    >>>
    >>> # Get collection statistics
    >>> stats = pm.stats()
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from cuic_quant.collector import PolymarketCollector
    from cuic_quant.data import PolymarketClient
    from cuic_quant.database.repositories import MarketRepository


class PolymarketNotebook:
    """Notebook-friendly interface to Polymarket data.

    Provides both live API access and database queries with DataFrame output.
    Dependencies (API client, database repository) are lazy-loaded on first use
    to minimize import time and allow partial functionality without full setup.

    Args:
        db_path: Optional custom database path. If not provided, uses the
            default database location.

    Example:
        >>> from cuic_quant.notebook import pm
        >>>
        >>> # Fetch live markets from API
        >>> live_df = pm.fetch_markets(limit=50)
        >>> print(live_df[['question', 'yes_price', 'volume']].head())
        >>>
        >>> # Load markets from local database
        >>> stored_df = pm.load_markets(limit=100)
        >>> print(stored_df.describe())
        >>>
        >>> # Search for specific markets
        >>> election_markets = pm.search("election")
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize notebook helper.

        Args:
            db_path: Optional custom database path. If not provided, uses the
                default database location from the connection module.
        """
        self._db_path = db_path
        self._client: PolymarketClient | None = None
        self._repo: MarketRepository | None = None

    @property
    def client(self) -> PolymarketClient:
        """Lazy-load API client.

        Returns:
            PolymarketClient instance for API requests.

        Raises:
            RuntimeError: If the client cannot be imported or instantiated.

        Example:
            >>> pm.client.get_market("market_id")
        """
        if self._client is None:
            try:
                from cuic_quant.data import PolymarketClient

                self._client = PolymarketClient()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Polymarket client: {e}") from e
        return self._client

    @property
    def repo(self) -> MarketRepository:
        """Lazy-load repository.

        Returns:
            MarketRepository instance for database queries.

        Raises:
            RuntimeError: If the repository cannot be imported or instantiated.

        Example:
            >>> pm.repo.get_market_by_id("market_id")
        """
        if self._repo is None:
            try:
                from cuic_quant.database.repositories import MarketRepository

                self._repo = MarketRepository()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize market repository: {e}") from e
        return self._repo

    # ==================== Live API Methods ====================

    def fetch_markets(self, limit: int = 100, active: bool = True) -> pd.DataFrame:
        """Fetch markets directly from Polymarket API.

        Retrieves current market data from the live Polymarket API. Use this
        when you need the most up-to-date information and don't mind the
        network latency.

        Args:
            limit: Maximum number of markets to return. Default 100.
            active: If True, only return active markets. Default True.

        Returns:
            DataFrame with columns: id, question, yes_price, no_price,
            volume, liquidity, status, end_date.

        Raises:
            ValueError: If limit is not greater than 0.
            RuntimeError: If the API request fails.

        Example:
            >>> df = pm.fetch_markets(limit=50, active=True)
            >>> df.sort_values('volume', ascending=False).head(10)
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        try:
            markets = self.client.get_markets(limit=limit, active=active)
        except Exception as e:
            raise RuntimeError(f"API request failed: {e}") from e

        if not markets:
            return pd.DataFrame(
                columns=[
                    "id",
                    "question",
                    "yes_price",
                    "no_price",
                    "volume",
                    "liquidity",
                    "status",
                    "end_date",
                ]
            )

        data = [
            {
                "id": m.id,
                "question": m.question,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume": m.volume,
                "liquidity": m.liquidity,
                "status": m.status,
                "end_date": m.end_date,
            }
            for m in markets
        ]

        return pd.DataFrame(data)

    def fetch_orderbook(self, token_id: str) -> pd.DataFrame:
        """Fetch orderbook from Polymarket API.

        Retrieves the current order book for a specific token from the live
        Polymarket CLOB (Central Limit Order Book) API.

        Args:
            token_id: The token identifier to fetch the orderbook for.

        Returns:
            DataFrame with columns: price, size, side (bid/ask).

        Raises:
            ValueError: If token_id is empty or whitespace-only.
            RuntimeError: If the API request fails.

        Example:
            >>> orderbook = pm.fetch_orderbook("0x123...")
            >>> bids = orderbook[orderbook['side'] == 'bid']
            >>> asks = orderbook[orderbook['side'] == 'ask']
            >>> print(f"Best bid: {bids['price'].max()}")
            >>> print(f"Best ask: {asks['price'].min()}")
        """
        if not token_id or not token_id.strip():
            raise ValueError("token_id cannot be empty")

        try:
            orderbook = self.client.get_orderbook(token_id)
        except Exception as e:
            raise RuntimeError(f"API request failed: {e}") from e

        if not orderbook.bids and not orderbook.asks:
            return pd.DataFrame(columns=["price", "size", "side"])

        bids = pd.DataFrame(orderbook.bids)
        if not bids.empty:
            bids["side"] = "bid"

        asks = pd.DataFrame(orderbook.asks)
        if not asks.empty:
            asks["side"] = "ask"

        return pd.concat([bids, asks], ignore_index=True)

    # ==================== Database Methods ====================

    def load_markets(
        self, limit: int = 1000, active_only: bool = True
    ) -> pd.DataFrame:
        """Load markets from database.

        Retrieves market data from the local database. Faster than API calls
        and doesn't count against rate limits. Use this for analysis of
        historical data or when working offline.

        Args:
            limit: Maximum number of markets to return. Default 1000.
            active_only: If True, only return active markets. Default True.

        Returns:
            DataFrame with columns: polymarket_id, question, yes_price, no_price,
            volume, volume_24h, liquidity, status, active, end_date, snapshot_at.

        Raises:
            ValueError: If limit is not greater than 0.

        Example:
            >>> df = pm.load_markets(limit=500, active_only=True)
            >>> high_volume = df[df['volume'] > 100000]
            >>> print(f"Found {len(high_volume)} high-volume markets")
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        return self.repo.get_markets_df(limit=limit, active_only=active_only)

    def load_prices(
        self,
        token_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Load price history from database.

        Retrieves historical price data for a specific token from the local
        database. The DataFrame is indexed by timestamp for easy time series
        analysis.

        Args:
            token_id: The token identifier to get prices for.
            start_date: Optional start date filter (inclusive).
            end_date: Optional end date filter (inclusive).

        Returns:
            DataFrame with columns: price, best_bid, best_ask, spread.
            Index is the timestamp.

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.now()
            >>> start = end - timedelta(days=7)
            >>> prices = pm.load_prices("token123", start_date=start, end_date=end)
            >>> prices['price'].plot(title="7-Day Price History")
        """
        return self.repo.get_price_history_df(
            token_id=token_id,
            start_date=start_date,
            end_date=end_date,
        )

    def load_top_markets(self, limit: int = 20) -> pd.DataFrame:
        """Load top markets by volume from database.

        Retrieves the markets with the highest trading volume from the
        local database. Useful for finding the most liquid and active markets.

        Args:
            limit: Maximum number of markets to return. Default 20.

        Returns:
            DataFrame with columns: id, question, yes_price, no_price,
            volume, liquidity.

        Raises:
            ValueError: If limit is not greater than 0.

        Example:
            >>> top = pm.load_top_markets(limit=10)
            >>> print(top[['question', 'volume']].to_string())
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        markets = self.repo.get_top_markets_by_volume(limit=limit)

        if not markets:
            return pd.DataFrame(
                columns=["id", "question", "yes_price", "no_price", "volume", "liquidity"]
            )

        data = [
            {
                "id": m.polymarket_id,
                "question": m.question,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume": m.volume,
                "liquidity": m.liquidity,
            }
            for m in markets
        ]

        return pd.DataFrame(data)

    def search(self, query: str, limit: int = 50) -> pd.DataFrame:
        """Search markets in database.

        Performs a case-insensitive search on market questions. Useful for
        finding specific markets by topic or keyword.

        Args:
            query: Search string to match against market questions.
            limit: Maximum number of results. Default 50.

        Returns:
            DataFrame with columns: id, question, yes_price, volume.

        Raises:
            ValueError: If limit is not greater than 0, or if query exceeds 500 characters.

        Example:
            >>> results = pm.search("bitcoin", limit=20)
            >>> results = pm.search("election 2024")
            >>> results = pm.search("World Cup")
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        # Strip whitespace from query
        query = query.strip() if query else ""

        # Return empty DataFrame for empty/whitespace-only query
        if not query:
            return pd.DataFrame(columns=["id", "question", "yes_price", "volume"])

        # Validate query length
        if len(query) > 500:
            raise ValueError("query cannot exceed 500 characters")

        markets = self.repo.search_markets(query=query, limit=limit)

        if not markets:
            return pd.DataFrame(columns=["id", "question", "yes_price", "volume"])

        data = [
            {
                "id": m.polymarket_id,
                "question": m.question,
                "yes_price": m.yes_price,
                "volume": m.volume,
            }
            for m in markets
        ]

        return pd.DataFrame(data)

    def stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns statistics about the data stored in the local database,
        including counts and date ranges for markets and price points.

        Returns:
            Dictionary with keys:
                - total_markets: Total unique markets
                - total_snapshots: Total market snapshots
                - total_price_points: Total price points
                - active_markets: Number of active markets
                - oldest_snapshot: Timestamp of oldest snapshot
                - newest_snapshot: Timestamp of newest snapshot
                - oldest_price: Timestamp of oldest price point
                - newest_price: Timestamp of newest price point

        Example:
            >>> stats = pm.stats()
            >>> print(f"Total markets: {stats['total_markets']}")
            >>> print(f"Active markets: {stats['active_markets']}")
            >>> print(f"Date range: {stats['oldest_snapshot']} to {stats['newest_snapshot']}")
        """
        return self.repo.get_collection_stats()

    # ==================== Collection Methods ====================

    def collect_now(self, limit: int = 500) -> dict[str, int | str]:
        """Run data collection immediately.

        Triggers an immediate data collection from the Polymarket API,
        storing the results in the local database. Useful for refreshing
        data before analysis.

        Args:
            limit: Maximum number of markets to collect. Default 500.

        Returns:
            Dictionary with collection statistics:
                - markets_fetched: Number of markets retrieved from API
                - markets_saved: Number of markets saved to database
                - status: "success" or "error"
                - error: Error message if status is "error"

        Raises:
            ValueError: If limit is not greater than 0.

        Example:
            >>> result = pm.collect_now(limit=100)
            >>> if result['status'] == 'success':
            ...     print(f"Collected {result['markets_saved']} markets")
            ... else:
            ...     print(f"Error: {result.get('error')}")
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        from cuic_quant.collector import PolymarketCollector

        collector = PolymarketCollector()
        return collector.collect_markets(limit=limit)


# Default instance for easy import
pm = PolymarketNotebook()
