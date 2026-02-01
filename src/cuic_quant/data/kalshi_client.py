"""Kalshi API client for event contracts data.

Kalshi is a CFTC-regulated prediction market exchange in the United States.
This client provides access to market data, order books, and trading.

Example:
    >>> from cuic_quant.data import KalshiClient
    >>>
    >>> client = KalshiClient(demo=True)
    >>> client.login()
    >>> events = client.get_events()
    >>> for event in events[:5]:
    ...     print(f"{event.title}: {event.yes_bid}¢ / {event.yes_ask}¢")

Note:
    - Requires account credentials for all endpoints
    - Use demo=True for testing with paper money
    - See docs/platforms/kalshi.md for full documentation
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class KalshiMarket:
    """Represents a Kalshi event contract market."""

    ticker: str
    title: str
    subtitle: str
    status: str
    yes_bid: int  # Price in cents
    yes_ask: int
    no_bid: int
    no_ask: int
    volume: int
    open_interest: int
    close_time: datetime | None

    @property
    def yes_mid(self) -> float:
        """Calculate mid price for YES in cents."""
        return (self.yes_bid + self.yes_ask) / 2

    @property
    def implied_probability(self) -> float:
        """Calculate implied probability from mid price."""
        return self.yes_mid / 100

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> KalshiMarket:
        """Create KalshiMarket from API response data.

        Args:
            data: Raw API response dictionary.

        Returns:
            KalshiMarket instance.
        """
        close_time = None
        if data.get("close_time"):
            try:
                close_time = datetime.fromisoformat(
                    data["close_time"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return cls(
            ticker=data.get("ticker", ""),
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            status=data.get("status", "unknown"),
            yes_bid=int(data.get("yes_bid", 0)),
            yes_ask=int(data.get("yes_ask", 0)),
            no_bid=int(data.get("no_bid", 0)),
            no_ask=int(data.get("no_ask", 0)),
            volume=int(data.get("volume", 0)),
            open_interest=int(data.get("open_interest", 0)),
            close_time=close_time,
        )


@dataclass
class KalshiOrder:
    """Represents a Kalshi order."""

    order_id: str
    ticker: str
    status: str
    action: str  # buy or sell
    side: str  # yes or no
    order_type: str  # limit or market
    count: int
    remaining_count: int
    price: int  # Price in cents
    created_time: datetime


@dataclass
class KalshiPosition:
    """Represents a position in a Kalshi market."""

    ticker: str
    yes_count: int
    no_count: int
    average_yes_price: int
    average_no_price: int


@dataclass
class KalshiBalance:
    """Represents account balance."""

    available: float
    pending: float
    total: float


class KalshiClient:
    """Client for interacting with Kalshi APIs.

    This client provides access to Kalshi event contracts including
    market data, trading, and account management.

    Args:
        email: Kalshi account email.
        password: Kalshi account password.
        demo: If True, use demo environment (default: True for safety).
        api_url: Override API URL.

    Example:
        >>> client = KalshiClient(demo=True)
        >>> client.login()
        >>> markets = client.get_markets(series_ticker="INFL")
        >>> print(f"Found {len(markets)} inflation markets")
    """

    PRODUCTION_URL = "https://trading-api.kalshi.com/trade-api/v2"
    DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2"

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        demo: bool = True,
        api_url: str | None = None,
    ) -> None:
        """Initialize the Kalshi client."""
        self.email = email or os.getenv("KALSHI_EMAIL")
        self.password = password or os.getenv("KALSHI_PASSWORD")
        self.demo = demo

        if api_url:
            self.api_url = api_url
        elif os.getenv("KALSHI_API_URL"):
            self.api_url = os.getenv("KALSHI_API_URL")
        else:
            self.api_url = self.DEMO_URL if demo else self.PRODUCTION_URL

        self._session = requests.Session()
        self._token: str | None = None

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._token is not None

    def login(self) -> None:
        """Authenticate with Kalshi API.

        Raises:
            ValueError: If credentials are not provided.
            requests.HTTPError: If authentication fails.
        """
        if not self.email or not self.password:
            raise ValueError(
                "Email and password required. Set KALSHI_EMAIL and "
                "KALSHI_PASSWORD environment variables."
            )

        response = self._session.post(
            f"{self.api_url}/login",
            json={"email": self.email, "password": self.password},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        self._token = data.get("token")

        if not self._token:
            raise ValueError("No token received from login")

        self._session.headers["Authorization"] = f"Bearer {self._token}"

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated before making requests."""
        if not self.is_authenticated:
            raise RuntimeError(
                "Not authenticated. Call login() first or provide credentials."
            )

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
    ) -> dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: Query parameters.
            json: JSON body for POST requests.

        Returns:
            Parsed JSON response.

        Raises:
            RuntimeError: If not authenticated.
            requests.HTTPError: If the request fails.
        """
        self._ensure_authenticated()

        url = f"{self.api_url}{endpoint}"

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
        status: str = "active",
        series_ticker: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> list[KalshiMarket]:
        """Fetch markets from Kalshi.

        Args:
            status: Market status filter (active, closed, settled).
            series_ticker: Filter by series (e.g., "INFL" for inflation).
            limit: Maximum number of markets to return.
            cursor: Pagination cursor.

        Returns:
            List of KalshiMarket objects.

        Example:
            >>> markets = client.get_markets(series_ticker="INFL")
            >>> for m in markets:
            ...     print(f"{m.ticker}: {m.yes_mid}¢")
        """
        params: dict[str, Any] = {
            "status": status,
            "limit": limit,
        }
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor

        data = self._request("GET", "/markets", params=params)

        markets = data.get("markets", [])
        return [KalshiMarket.from_api_response(m) for m in markets]

    def get_market(self, ticker: str) -> KalshiMarket:
        """Fetch a specific market by ticker.

        Args:
            ticker: The market ticker (e.g., "INFL-25JAN-T3.0").

        Returns:
            KalshiMarket object.
        """
        data = self._request("GET", f"/markets/{ticker}")
        return KalshiMarket.from_api_response(data.get("market", data))

    def get_orderbook(self, ticker: str, depth: int = 10) -> dict[str, Any]:
        """Fetch order book for a market.

        Args:
            ticker: Market ticker.
            depth: Number of price levels to return.

        Returns:
            Order book data with yes/no bids and asks.
        """
        data = self._request(
            "GET",
            f"/markets/{ticker}/orderbook",
            params={"depth": depth},
        )
        return data.get("orderbook", data)

    def get_balance(self) -> KalshiBalance:
        """Fetch account balance.

        Returns:
            KalshiBalance with available, pending, and total amounts.
        """
        data = self._request("GET", "/portfolio/balance")

        balance_data = data.get("balance", data)
        return KalshiBalance(
            available=float(balance_data.get("available_balance", 0)) / 100,
            pending=float(balance_data.get("pending_balance", 0)) / 100,
            total=float(balance_data.get("total_balance", 0)) / 100,
        )

    def get_positions(self) -> list[KalshiPosition]:
        """Fetch current positions.

        Returns:
            List of KalshiPosition objects.
        """
        data = self._request("GET", "/portfolio/positions")

        positions = data.get("market_positions", [])
        return [
            KalshiPosition(
                ticker=p.get("ticker", ""),
                yes_count=int(p.get("yes_count", 0)),
                no_count=int(p.get("no_count", 0)),
                average_yes_price=int(p.get("average_yes_price", 0)),
                average_no_price=int(p.get("average_no_price", 0)),
            )
            for p in positions
        ]

    def place_order(
        self,
        ticker: str,
        action: str,
        side: str,
        order_type: str,
        count: int,
        price: int | None = None,
    ) -> KalshiOrder:
        """Place an order.

        Args:
            ticker: Market ticker.
            action: "buy" or "sell".
            side: "yes" or "no".
            order_type: "limit" or "market".
            count: Number of contracts.
            price: Price in cents (required for limit orders).

        Returns:
            KalshiOrder with order details.

        Example:
            >>> order = client.place_order(
            ...     ticker="INFL-25JAN-T3.0",
            ...     action="buy",
            ...     side="yes",
            ...     order_type="limit",
            ...     count=10,
            ...     price=70,
            ... )
        """
        if order_type == "limit" and price is None:
            raise ValueError("Price required for limit orders")

        payload: dict[str, Any] = {
            "ticker": ticker,
            "action": action,
            "side": side,
            "type": order_type,
            "count": count,
        }
        if price is not None:
            payload["price"] = price

        data = self._request("POST", "/portfolio/orders", json=payload)

        order_data = data.get("order", data)
        return KalshiOrder(
            order_id=order_data.get("order_id", ""),
            ticker=order_data.get("ticker", ticker),
            status=order_data.get("status", "unknown"),
            action=order_data.get("action", action),
            side=order_data.get("side", side),
            order_type=order_data.get("type", order_type),
            count=order_data.get("count", count),
            remaining_count=order_data.get("remaining_count", count),
            price=order_data.get("price", price or 0),
            created_time=datetime.now(),
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            True if cancellation successful.
        """
        self._request("DELETE", f"/portfolio/orders/{order_id}")
        return True

    def get_trades(
        self,
        ticker: str,
        limit: int = 100,
        min_ts: str | None = None,
        max_ts: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch trade history for a market.

        Args:
            ticker: Market ticker.
            limit: Maximum trades to return.
            min_ts: Minimum timestamp (ISO format).
            max_ts: Maximum timestamp (ISO format).

        Returns:
            List of trade records.
        """
        params: dict[str, Any] = {"limit": limit}
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts

        data = self._request("GET", f"/markets/{ticker}/trades", params=params)
        return data.get("trades", [])

    def logout(self) -> None:
        """Logout and clear authentication."""
        if self.is_authenticated:
            try:
                self._session.post(f"{self.api_url}/logout", timeout=10)
            except Exception:
                pass  # Ignore logout errors
            finally:
                self._token = None
                self._session.headers.pop("Authorization", None)

    def close(self) -> None:
        """Close the HTTP session."""
        self.logout()
        self._session.close()

    def __enter__(self) -> KalshiClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
