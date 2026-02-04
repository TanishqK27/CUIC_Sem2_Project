"""Market data API endpoints.

This module defines the REST API endpoints for accessing Polymarket data
including market snapshots, price history, search, and collection statistics.

Example:
    >>> from fastapi import FastAPI
    >>> from cuic_quant.api.routes.markets import router
    >>>
    >>> app = FastAPI()
    >>> app.include_router(router, prefix="/api/v1")

Endpoints:
    - GET /markets - List latest market snapshots
    - GET /markets/top - List top markets by volume
    - GET /markets/search - Search markets by question text
    - GET /markets/{market_id} - Get a specific market by ID
    - GET /prices/{token_id} - Get price history for a token
    - GET /stats - Get collection statistics
    - POST /collect - Trigger a data collection run
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from cuic_quant.collector import PolymarketCollector
from cuic_quant.database import MarketRepository

router = APIRouter(tags=["markets"])


# -----------------------------------------------------------------------------
# Dependency Injection
# -----------------------------------------------------------------------------


def get_repository() -> MarketRepository:
    """Dependency to get MarketRepository instance.

    Returns:
        MarketRepository instance for database operations.
    """
    return MarketRepository()


# -----------------------------------------------------------------------------
# Pydantic Response Models
# -----------------------------------------------------------------------------


class MarketResponse(BaseModel):
    """Response model for market snapshot data.

    Attributes:
        id: Internal database ID of the snapshot.
        question: The prediction question being traded.
        yes_price: Current YES token price (0-1).
        no_price: Current NO token price (0-1).
        volume: Total market volume in USDC.
        volume_24h: 24-hour trading volume.
        liquidity: Current market liquidity.
        status: Market status (e.g., "active", "resolved").
        active: Whether trading is currently enabled.
        end_date: When the market resolves.
        snapshot_at: When this snapshot was taken.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str | None = None
    yes_price: float | None = None
    no_price: float | None = None
    volume: float | None = None
    volume_24h: float | None = None
    liquidity: float | None = None
    status: str | None = None
    active: bool = True
    end_date: datetime | None = None
    snapshot_at: datetime


class PricePointResponse(BaseModel):
    """Response model for price point data.

    Attributes:
        timestamp: When this price was observed.
        price: Token price at this timestamp (0-1).
        best_bid: Best bid price from order book.
        best_ask: Best ask price from order book.
        spread: Bid-ask spread.
    """

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    price: float
    best_bid: float | None = None
    best_ask: float | None = None
    spread: float | None = None


class StatsResponse(BaseModel):
    """Response model for collection statistics.

    Attributes:
        total_market_snapshots: Total number of market snapshots stored.
        total_price_points: Total number of price points stored.
        total_events: Total number of unique markets tracked.
        oldest_snapshot: Timestamp of the oldest snapshot.
        newest_snapshot: Timestamp of the newest snapshot.
    """

    total_market_snapshots: int
    total_price_points: int
    total_events: int
    oldest_snapshot: datetime | None = None
    newest_snapshot: datetime | None = None


class CollectionResponse(BaseModel):
    """Response model for data collection results.

    Attributes:
        markets_fetched: Number of markets retrieved from API.
        markets_saved: Number of markets successfully saved.
        status: Collection status ("success", "partial", or "error").
        error: Error message if status is "error".
    """

    markets_fetched: int
    markets_saved: int
    status: str
    error: str | None = None


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------


@router.get("/markets", response_model=list[MarketResponse])
def list_markets(
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum number of markets to return")] = 50,
    active_only: Annotated[bool, Query(description="Only return active markets")] = True,
    repo: MarketRepository = Depends(get_repository),
) -> list[MarketResponse]:
    """List the most recently updated market snapshots.

    Returns market snapshots ordered by snapshot timestamp (newest first).
    Use the limit parameter to control the number of results.

    Args:
        limit: Maximum number of markets to return (1-1000). Default 50.
        active_only: If True, only return active markets. Default True.
        repo: MarketRepository instance (injected via Depends).

    Returns:
        List of MarketResponse objects.

    Example:
        GET /api/v1/markets?limit=10&active_only=true
    """
    markets = repo.get_latest_markets(limit=limit, active_only=active_only)
    return [MarketResponse.model_validate(m) for m in markets]


@router.get("/markets/top", response_model=list[MarketResponse])
def list_top_markets(
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of markets to return")] = 20,
    repo: MarketRepository = Depends(get_repository),
) -> list[MarketResponse]:
    """List markets with the highest trading volume.

    Returns the latest snapshot for each market, ordered by total volume
    (highest first). Useful for finding the most popular markets.

    Args:
        limit: Maximum number of markets to return (1-100). Default 20.
        repo: MarketRepository instance (injected via Depends).

    Returns:
        List of MarketResponse objects ordered by volume descending.

    Example:
        GET /api/v1/markets/top?limit=10
    """
    markets = repo.get_top_markets_by_volume(limit=limit)
    return [MarketResponse.model_validate(m) for m in markets]


@router.get("/markets/search", response_model=list[MarketResponse])
def search_markets(
    q: Annotated[str, Query(min_length=2, description="Search query (min 2 characters)")],
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 20,
    repo: MarketRepository = Depends(get_repository),
) -> list[MarketResponse]:
    """Search markets by question text.

    Performs a case-insensitive search on market questions. Returns the
    latest snapshot for each matching market.

    Args:
        q: Search query string (minimum 2 characters).
        limit: Maximum number of results (1-100). Default 20.
        repo: MarketRepository instance (injected via Depends).

    Returns:
        List of MarketResponse objects matching the search query.

    Example:
        GET /api/v1/markets/search?q=election&limit=10
    """
    markets = repo.search_markets(query=q, limit=limit)
    return [MarketResponse.model_validate(m) for m in markets]


@router.get("/markets/{market_id}", response_model=MarketResponse)
def get_market(
    market_id: str,
    repo: MarketRepository = Depends(get_repository),
) -> MarketResponse:
    """Get a specific market by its Polymarket ID.

    Returns the most recent snapshot for the given market. Raises 404
    if no market with the given ID is found.

    Args:
        market_id: The Polymarket market identifier.
        repo: MarketRepository instance (injected via Depends).

    Returns:
        MarketResponse for the requested market.

    Raises:
        HTTPException: 404 if market not found.

    Example:
        GET /api/v1/markets/abc123
    """
    market = repo.get_market_by_id(market_id)

    if market is None:
        raise HTTPException(
            status_code=404,
            detail=f"Market with ID '{market_id}' not found",
        )

    return MarketResponse.model_validate(market)


@router.get("/prices/{token_id}", response_model=list[PricePointResponse])
def get_price_history(
    token_id: str,
    start_date: Annotated[datetime | None, Query(description="Filter prices after this date")] = None,
    end_date: Annotated[datetime | None, Query(description="Filter prices before this date")] = None,
    repo: MarketRepository = Depends(get_repository),
) -> list[PricePointResponse]:
    """Get price history for a specific token.

    Returns price points for the given token ordered by timestamp (oldest first).
    Optionally filter by date range.

    Args:
        token_id: The token identifier to get prices for.
        start_date: Optional start date filter (inclusive).
        end_date: Optional end date filter (inclusive).
        repo: MarketRepository instance (injected via Depends).

    Returns:
        List of PricePointResponse objects ordered by timestamp.

    Example:
        GET /api/v1/prices/token_abc?start_date=2024-01-01T00:00:00
    """
    points = repo.get_price_history(
        token_id=token_id,
        start_date=start_date,
        end_date=end_date,
    )
    return [PricePointResponse.model_validate(p) for p in points]


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    repo: MarketRepository = Depends(get_repository),
) -> StatsResponse:
    """Get collection statistics.

    Returns aggregate statistics about the collected data including
    total counts and date ranges.

    Args:
        repo: MarketRepository instance (injected via Depends).

    Returns:
        StatsResponse with collection statistics.

    Example:
        GET /api/v1/stats
    """
    stats = repo.get_collection_stats()

    return StatsResponse(
        total_market_snapshots=stats["total_snapshots"],
        total_price_points=stats["total_price_points"],
        total_events=stats["total_markets"],
        oldest_snapshot=stats["oldest_snapshot"],
        newest_snapshot=stats["newest_snapshot"],
    )


@router.post("/collect", response_model=CollectionResponse)
def trigger_collection() -> CollectionResponse:
    """Trigger a data collection run.

    Manually triggers the Polymarket collector to fetch and store
    the latest market data. Returns statistics about the collection.

    Returns:
        CollectionResponse with collection results.

    Raises:
        HTTPException: 500 if collection fails due to an unexpected error.

    Example:
        POST /api/v1/collect
    """
    try:
        collector = PolymarketCollector()
        result = collector.collect_markets()

        return CollectionResponse(
            markets_fetched=result.get("markets_fetched", 0),
            markets_saved=result.get("markets_saved", 0),
            status=result.get("status", "error"),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collection failed: {str(e)}",
        )
