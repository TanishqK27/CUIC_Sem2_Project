"""Polymarket API client for prediction market data.

Polymarket is a decentralized prediction market built on Polygon.
This client provides access to market data, order books, and historical prices.

Example:
    >>> from cuic_quant.data import PolymarketClient
    >>>
    >>> client = PolymarketClient()
    >>> markets = client.get_markets(limit=10)
    >>> for market in markets:
    ...     print(f"{market.question}: {market.yes_price:.2%}")

Note:
    - Public endpoints do not require authentication
    - Trading endpoints require API keys (not implemented in this stub)
    - See docs/platforms/polymarket.md for full documentation
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class Market:
    """Represents a Polymarket prediction market."""

    id: str
    question: str
    description: str
    outcomes: list[str]
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    end_date: datetime | None
    status: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Market:
        """Create Market from API response data.

        Args:
            data: Raw API response dictionary.

        Returns:
            Market instance.
        """
        # outcomePrices may be a JSON string or a list
        prices = data.get("outcomePrices", ["0", "0"])
        if isinstance(prices, str):
            import json
            try:
                prices = json.loads(prices)
            except (json.JSONDecodeError, TypeError):
                prices = ["0", "0"]
        yes_price = float(prices[0]) if prices else 0.0
        no_price = float(prices[1]) if len(prices) > 1 else 1 - yes_price

        end_date = None
        if data.get("endDate"):
            try:
                end_date = datetime.fromisoformat(
                    data["endDate"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id", ""),
            question=data.get("question", ""),
            description=data.get("description", ""),
            outcomes=data.get("outcomes", ["Yes", "No"]),
            yes_price=yes_price,
            no_price=no_price,
            volume=float(data.get("volume", 0)),
            liquidity=float(data.get("liquidity", 0)),
            end_date=end_date,
            status=data.get("status", "unknown"),
        )


@dataclass
class OrderBook:
    """Represents an order book for a market."""

    token_id: str
    bids: list[dict[str, float]]
    asks: list[dict[str, float]]
    timestamp: datetime

    @property
    def best_bid(self) -> float | None:
        """Get the best (highest) bid price."""
        return self.bids[0]["price"] if self.bids else None

    @property
    def best_ask(self) -> float | None:
        """Get the best (lowest) ask price."""
        return self.asks[0]["price"] if self.asks else None

    @property
    def spread(self) -> float | None:
        """Calculate the bid-ask spread."""
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None


class PolymarketClient:
    """Client for interacting with Polymarket APIs.

    This client provides access to public Polymarket data including
    markets, prices, and order books.

    Args:
        api_key: Optional API key for authenticated endpoints.
        api_secret: Optional API secret for authenticated endpoints.
        base_url: Base URL for the API (default: gamma-api.polymarket.com).

    Example:
        >>> client = PolymarketClient()
        >>> markets = client.get_markets()
        >>> print(f"Found {len(markets)} markets")
    """

    GAMMA_API_URL = "https://gamma-api.polymarket.com"
    CLOB_API_URL = "https://clob.polymarket.com"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the Polymarket client."""
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY")
        self.api_secret = api_secret or os.getenv("POLYMARKET_API_SECRET")
        self.base_url = base_url or self.GAMMA_API_URL
        self._session = requests.Session()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        """Make an API request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: Query parameters.
            json: JSON body for POST requests.
            base_url: Override base URL.

        Returns:
            Parsed JSON response.

        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{base_url or self.base_url}{endpoint}"

        response = self._session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=30,
        )
        response.raise_for_status()

        return response.json()

    def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> list[Market]:
        """Fetch prediction markets.

        Args:
            limit: Maximum number of markets to return.
            offset: Number of markets to skip (for pagination).
            active: If True, only return active markets.

        Returns:
            List of Market objects.

        Example:
            >>> markets = client.get_markets(limit=10)
            >>> for m in markets:
            ...     print(f"{m.question}: ${m.volume:,.0f} volume")
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if active:
            params["active"] = "true"

        data = self._request("GET", "/markets", params=params)

        markets = data if isinstance(data, list) else data.get("markets", [])
        return [Market.from_api_response(m) for m in markets]

    def get_market(self, market_id: str) -> Market:
        """Fetch a specific market by ID.

        Args:
            market_id: The market's unique identifier.

        Returns:
            Market object.

        Raises:
            requests.HTTPError: If market not found.
        """
        data = self._request("GET", f"/markets/{market_id}")
        return Market.from_api_response(data)

    def get_orderbook(self, token_id: str) -> OrderBook:
        """Fetch the order book for a token.

        Args:
            token_id: The token's unique identifier.

        Returns:
            OrderBook object with bids and asks.

        Example:
            >>> orderbook = client.get_orderbook("0x...")
            >>> print(f"Spread: ${orderbook.spread:.4f}")
        """
        data = self._request(
            "GET",
            "/book",
            params={"token_id": token_id},
            base_url=self.CLOB_API_URL,
        )

        bids = [
            {"price": float(b["price"]), "size": float(b["size"])}
            for b in data.get("bids", [])
        ]
        asks = [
            {"price": float(a["price"]), "size": float(a["size"])}
            for a in data.get("asks", [])
        ]

        return OrderBook(
            token_id=token_id,
            bids=bids,
            asks=asks,
            timestamp=datetime.now(),
        )

    def get_price_history(
        self,
        market_id: str,
        interval: str = "1h",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch historical price data for a market.

        Args:
            market_id: The market's unique identifier.
            interval: Time interval (1m, 5m, 1h, 1d).
            start_date: Start date in ISO format.
            end_date: End date in ISO format.

        Returns:
            List of price data points.

        Note:
            This is a placeholder - actual endpoint may vary.
        """
        # TODO: Implement based on actual Polymarket historical data API
        raise NotImplementedError(
            "Historical price data endpoint not yet implemented. "
            "See docs/platforms/polymarket.md for data collection alternatives."
        )

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self) -> PolymarketClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
