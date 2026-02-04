"""Polymarket data collector service.

This module provides a service class for collecting data from the Polymarket API
and storing it in the local database for analysis and backtesting.

Example:
    >>> from cuic_quant.collector import PolymarketCollector
    >>>
    >>> collector = PolymarketCollector()
    >>> result = collector.run_full_collection()
    >>> print(f"Collected {result['markets_saved']} markets")

The collector handles:
    - Fetching market data from Polymarket API
    - Converting API responses to database models
    - Storing snapshots with proper timestamps
    - Collecting orderbook data for price points
    - Tracking collection runs for monitoring
"""

from __future__ import annotations

import logging
from datetime import datetime

import requests
from sqlalchemy import Engine

from cuic_quant.data.polymarket_client import Market, PolymarketClient
from cuic_quant.database.connection import get_default_engine, get_session
from cuic_quant.database.models import CollectionRun, MarketSnapshot, PricePoint

logger = logging.getLogger(__name__)


class PolymarketCollector:
    """Service for collecting and storing Polymarket data.

    This collector fetches market data and orderbooks from the Polymarket API
    and persists them to the local SQLite database. It tracks collection runs
    for monitoring and debugging purposes.

    Args:
        client: Optional PolymarketClient instance. If not provided, a new
            client is created.
        engine: Optional SQLAlchemy Engine. If not provided, uses the default
            singleton engine.

    Attributes:
        client: The Polymarket API client.
        engine: The SQLAlchemy database engine.

    Example:
        >>> collector = PolymarketCollector()
        >>> result = collector.collect_markets(limit=50)
        >>> print(f"Status: {result['status']}")
        >>> print(f"Markets saved: {result['markets_saved']}")
    """

    def __init__(
        self,
        client: PolymarketClient | None = None,
        engine: Engine | None = None,
    ) -> None:
        """Initialize the Polymarket collector.

        Args:
            client: Optional PolymarketClient instance. If not provided,
                creates a new client.
            engine: Optional SQLAlchemy Engine. If not provided, uses
                get_default_engine() which initializes the database.
        """
        self.client = client if client is not None else PolymarketClient()
        self.engine = engine if engine is not None else get_default_engine()

    def _market_to_snapshot(self, market: Market) -> MarketSnapshot:
        """Convert an API Market object to a database MarketSnapshot.

        Args:
            market: Market object from the Polymarket API client.

        Returns:
            MarketSnapshot model ready for database insertion.

        Note:
            Uses getattr() with defaults to handle potentially missing
            fields in the Market dataclass.
        """
        return MarketSnapshot(
            polymarket_id=getattr(market, "id", ""),
            question=getattr(market, "question", None),
            description=getattr(market, "description", None),
            slug=None,  # Not available in current Market dataclass
            yes_token_id=None,  # Would need to be added to Market
            no_token_id=None,  # Would need to be added to Market
            yes_price=getattr(market, "yes_price", None),
            no_price=getattr(market, "no_price", None),
            volume=getattr(market, "volume", None),
            volume_24h=None,  # Not available in current Market dataclass
            liquidity=getattr(market, "liquidity", None),
            status=getattr(market, "status", None),
            active=getattr(market, "status", "") == "active",
            end_date=getattr(market, "end_date", None),
            snapshot_at=datetime.utcnow(),
        )

    def collect_markets(
        self,
        limit: int = 100,
        active_only: bool = True,
    ) -> dict[str, int | str]:
        """Fetch markets from Polymarket API and store to database.

        Retrieves market data from the Polymarket API, converts each market
        to a MarketSnapshot, and saves them to the database. A CollectionRun
        record is created to track the operation.

        Args:
            limit: Maximum number of markets to fetch. Default 100.
            active_only: If True, only fetch active markets. Default True.

        Returns:
            Dictionary with collection statistics:
                - markets_fetched: Number of markets retrieved from API
                - markets_saved: Number of markets successfully saved
                - status: "success" or "error"
                - error: Error message if status is "error"

        Example:
            >>> collector = PolymarketCollector()
            >>> result = collector.collect_markets(limit=50, active_only=True)
            >>> if result["status"] == "success":
            ...     print(f"Saved {result['markets_saved']} markets")
        """
        logger.info(f"Starting market collection (limit={limit}, active_only={active_only})")

        # Create collection run record
        collection_run = CollectionRun(
            started_at=datetime.utcnow(),
            status="running",
        )

        markets_fetched = 0
        markets_saved = 0

        try:
            # Fetch markets from API
            markets = self.client.get_markets(limit=limit, active=active_only)
            markets_fetched = len(markets)
            logger.info(f"Fetched {markets_fetched} markets from API")

            # Convert and save to database
            with get_session(self.engine) as session:
                # Add collection run first
                session.add(collection_run)

                for market in markets:
                    try:
                        snapshot = self._market_to_snapshot(market)
                        session.add(snapshot)
                        markets_saved += 1
                    except Exception as e:
                        logger.warning(f"Failed to save market {market.id}: {e}")
                        continue

                # Update collection run with results
                collection_run.completed_at = datetime.utcnow()
                collection_run.status = "completed"
                collection_run.markets_collected = markets_saved
                session.flush()

            logger.info(f"Successfully saved {markets_saved} market snapshots")

            return {
                "markets_fetched": markets_fetched,
                "markets_saved": markets_saved,
                "status": "success",
            }

        except requests.HTTPError as e:
            error_msg = str(e)
            logger.error(f"HTTP error during market collection: {error_msg}")

            # Try to save the failed collection run
            try:
                with get_session(self.engine) as session:
                    collection_run.completed_at = datetime.utcnow()
                    collection_run.status = "failed"
                    collection_run.error_message = error_msg
                    collection_run.markets_collected = markets_saved
                    session.add(collection_run)
                    session.flush()
            except Exception as save_error:
                logger.error(f"Failed to save collection run: {save_error}")

            return {
                "markets_fetched": markets_fetched,
                "markets_saved": markets_saved,
                "status": "error",
                "error": error_msg,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Market collection failed: {error_msg}")

            # Try to save the failed collection run
            try:
                with get_session(self.engine) as session:
                    collection_run.completed_at = datetime.utcnow()
                    collection_run.status = "failed"
                    collection_run.error_message = error_msg
                    collection_run.markets_collected = markets_saved
                    session.add(collection_run)
                    session.flush()
            except Exception as save_error:
                logger.error(f"Failed to save collection run: {save_error}")

            return {
                "markets_fetched": markets_fetched,
                "markets_saved": markets_saved,
                "status": "error",
                "error": error_msg,
            }

    def collect_orderbooks(
        self,
        token_ids: list[str] | None = None,
        limit: int = 50,
    ) -> dict[str, int | str]:
        """Fetch orderbooks and create price points for tokens.

        If token_ids is not provided, retrieves token IDs from recent
        MarketSnapshot records. For each token, fetches the orderbook
        and creates a PricePoint with the midpoint price and spread data.

        Args:
            token_ids: List of token IDs to fetch orderbooks for. If None,
                gets token IDs from recent market snapshots.
            limit: Maximum number of orderbooks to fetch when getting
                token IDs from database. Default 50.

        Returns:
            Dictionary with collection statistics:
                - price_points_saved: Number of price points created
                - errors: Number of orderbook fetch errors
                - status: "success", "partial", or "error"

        Example:
            >>> collector = PolymarketCollector()
            >>> # Collect orderbooks for specific tokens
            >>> result = collector.collect_orderbooks(token_ids=["token1", "token2"])
            >>> print(f"Saved {result['price_points_saved']} price points")
        """
        logger.info("Starting orderbook collection")

        price_points_saved = 0
        errors = 0

        try:
            # Get token IDs if not provided
            if token_ids is None:
                with get_session(self.engine) as session:
                    # Query recent market snapshots for yes_token_ids
                    snapshots = (
                        session.query(MarketSnapshot)
                        .filter(MarketSnapshot.yes_token_id.isnot(None))
                        .order_by(MarketSnapshot.snapshot_at.desc())
                        .limit(limit)
                        .all()
                    )
                    token_ids = [s.yes_token_id for s in snapshots if s.yes_token_id]

            if not token_ids:
                logger.warning("No token IDs available for orderbook collection")
                return {
                    "price_points_saved": 0,
                    "errors": 0,
                    "status": "success",
                }

            logger.info(f"Collecting orderbooks for {len(token_ids)} tokens")

            # Fetch orderbooks and create price points
            with get_session(self.engine) as session:
                for token_id in token_ids:
                    try:
                        orderbook = self.client.get_orderbook(token_id)

                        # Calculate midpoint price
                        best_bid = orderbook.best_bid
                        best_ask = orderbook.best_ask
                        spread = orderbook.spread

                        if best_bid is not None and best_ask is not None:
                            midpoint = (best_bid + best_ask) / 2
                        elif best_bid is not None:
                            midpoint = best_bid
                        elif best_ask is not None:
                            midpoint = best_ask
                        else:
                            # No valid prices, skip this token
                            logger.debug(f"No valid prices for token {token_id}")
                            continue

                        price_point = PricePoint(
                            token_id=token_id,
                            price=midpoint,
                            timestamp=orderbook.timestamp,
                            best_bid=best_bid,
                            best_ask=best_ask,
                            spread=spread,
                        )
                        session.add(price_point)
                        price_points_saved += 1

                    except requests.HTTPError as e:
                        logger.warning(f"HTTP error fetching orderbook for {token_id}: {e}")
                        errors += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to fetch orderbook for {token_id}: {e}")
                        errors += 1
                        continue

                session.flush()

            logger.info(
                f"Orderbook collection complete: {price_points_saved} saved, {errors} errors"
            )

            status = "success" if errors == 0 else "partial"
            return {
                "price_points_saved": price_points_saved,
                "errors": errors,
                "status": status,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Orderbook collection failed: {error_msg}")

            return {
                "price_points_saved": price_points_saved,
                "errors": errors,
                "status": "error",
                "error": error_msg,
            }

    def run_full_collection(self) -> dict[str, int | str]:
        """Run a complete data collection cycle.

        Performs both market collection and orderbook collection in sequence.
        First collects markets, then collects orderbooks for available tokens.

        Returns:
            Dictionary with combined collection statistics:
                - markets_fetched: Number of markets retrieved from API
                - markets_saved: Number of markets saved to database
                - price_points_saved: Number of price points created
                - orderbook_errors: Number of orderbook fetch errors
                - status: Overall status ("success", "partial", or "error")

        Example:
            >>> collector = PolymarketCollector()
            >>> result = collector.run_full_collection()
            >>> print(f"Markets: {result['markets_saved']}")
            >>> print(f"Price points: {result['price_points_saved']}")
        """
        logger.info("Starting full collection cycle")

        # Collect markets
        market_result = self.collect_markets()

        # Collect orderbooks
        orderbook_result = self.collect_orderbooks()

        # Determine overall status
        if market_result["status"] == "error":
            overall_status = "error"
        elif orderbook_result["status"] == "error":
            overall_status = "partial"
        elif market_result["status"] == "success" and orderbook_result["status"] == "success":
            overall_status = "success"
        else:
            overall_status = "partial"

        result = {
            "markets_fetched": market_result["markets_fetched"],
            "markets_saved": market_result["markets_saved"],
            "price_points_saved": orderbook_result["price_points_saved"],
            "orderbook_errors": orderbook_result["errors"],
            "status": overall_status,
        }

        logger.info(f"Full collection complete: {result}")
        return result
