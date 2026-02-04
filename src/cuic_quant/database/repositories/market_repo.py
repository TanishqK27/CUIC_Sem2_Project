"""Market repository for database access with DataFrame support.

This module provides the MarketRepository class that encapsulates all
database operations for market data. It supports both ORM model returns
for API endpoints and DataFrame returns for notebook analysis.

Example:
    >>> from cuic_quant.database.repositories import MarketRepository
    >>>
    >>> # Basic usage with default engine
    >>> repo = MarketRepository()
    >>> markets = repo.get_latest_markets(limit=10)
    >>>
    >>> # DataFrame for notebooks
    >>> df = repo.get_markets_df(limit=100, active_only=True)
    >>> df.head()
    >>>
    >>> # Price history analysis
    >>> price_df = repo.get_price_history_df(
    ...     token_id="abc123",
    ...     start_date=datetime(2024, 1, 1),
    ...     end_date=datetime(2024, 12, 31),
    ... )
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from cuic_quant.database.connection import get_default_engine, get_session
from cuic_quant.database.models import MarketSnapshot, PricePoint


class MarketRepository:
    """Repository for market data database operations.

    Provides a clean interface for querying and persisting market data.
    Supports both ORM model returns (for API endpoints) and DataFrame
    returns (for Jupyter notebooks and analysis).

    Attributes:
        _engine: SQLAlchemy engine for database connections.

    Example:
        >>> repo = MarketRepository()
        >>> # Query methods return ORM models
        >>> market = repo.get_market_by_id("market123")
        >>> # DataFrame methods return pandas DataFrames
        >>> df = repo.get_markets_df(limit=50)
    """

    def __init__(
        self,
        session: Session | None = None,
        engine: Engine | None = None,
    ) -> None:
        """Initialize the repository with a database engine.

        Args:
            session: Optional SQLAlchemy session (currently unused, for future
                dependency injection support).
            engine: SQLAlchemy engine to use. If None, uses the default
                singleton engine from get_default_engine().

        Example:
            >>> # Use default engine
            >>> repo = MarketRepository()
            >>> # Use custom engine
            >>> from cuic_quant.database import get_engine
            >>> engine = get_engine("data/custom.db")
            >>> repo = MarketRepository(engine=engine)
        """
        self._engine = engine if engine is not None else get_default_engine()
        # Note: session parameter reserved for future DI support

    # -------------------------------------------------------------------------
    # Query Methods (return ORM models)
    # -------------------------------------------------------------------------

    def get_latest_markets(
        self,
        limit: int = 50,
        active_only: bool = True,
    ) -> list[MarketSnapshot]:
        """Get the most recently updated market snapshots.

        Args:
            limit: Maximum number of markets to return. Defaults to 50.
            active_only: If True, only return active markets. Defaults to True.

        Returns:
            List of MarketSnapshot objects ordered by snapshot_at descending.

        Example:
            >>> repo = MarketRepository()
            >>> markets = repo.get_latest_markets(limit=10, active_only=True)
            >>> for m in markets:
            ...     print(f"{m.question}: {m.yes_price}")
        """
        with get_session(self._engine) as session:
            stmt = select(MarketSnapshot).order_by(MarketSnapshot.snapshot_at.desc())

            if active_only:
                stmt = stmt.where(MarketSnapshot.active == True)  # noqa: E712

            stmt = stmt.limit(limit)
            result = session.execute(stmt)
            markets = list(result.scalars().all())

            # Detach from session
            session.expunge_all()
            return markets

    def get_market_by_id(self, polymarket_id: str) -> MarketSnapshot | None:
        """Get a market snapshot by its Polymarket ID.

        Returns the most recent snapshot for the given market ID.

        Args:
            polymarket_id: The Polymarket market identifier.

        Returns:
            MarketSnapshot if found, None otherwise.

        Example:
            >>> repo = MarketRepository()
            >>> market = repo.get_market_by_id("market_abc123")
            >>> if market:
            ...     print(f"Yes price: {market.yes_price}")
        """
        with get_session(self._engine) as session:
            stmt = (
                select(MarketSnapshot)
                .where(MarketSnapshot.polymarket_id == polymarket_id)
                .order_by(MarketSnapshot.snapshot_at.desc())
                .limit(1)
            )
            result = session.execute(stmt)
            market = result.scalar_one_or_none()

            if market:
                session.expunge(market)
            return market

    def get_price_history(
        self,
        token_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[PricePoint]:
        """Get price history for a specific token.

        Args:
            token_id: The token identifier to get prices for.
            start_date: Optional start date filter (inclusive).
            end_date: Optional end date filter (inclusive).

        Returns:
            List of PricePoint objects ordered by timestamp ascending.

        Example:
            >>> repo = MarketRepository()
            >>> from datetime import datetime
            >>> prices = repo.get_price_history(
            ...     token_id="token_abc",
            ...     start_date=datetime(2024, 1, 1),
            ... )
            >>> for p in prices:
            ...     print(f"{p.timestamp}: {p.price}")
        """
        with get_session(self._engine) as session:
            stmt = (
                select(PricePoint)
                .where(PricePoint.token_id == token_id)
                .order_by(PricePoint.timestamp.asc())
            )

            if start_date:
                stmt = stmt.where(PricePoint.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(PricePoint.timestamp <= end_date)

            result = session.execute(stmt)
            points = list(result.scalars().all())

            session.expunge_all()
            return points

    def get_top_markets_by_volume(self, limit: int = 20) -> list[MarketSnapshot]:
        """Get markets with the highest trading volume.

        Returns the latest snapshot for each market, ordered by total volume.

        Args:
            limit: Maximum number of markets to return. Defaults to 20.

        Returns:
            List of MarketSnapshot objects ordered by volume descending.

        Example:
            >>> repo = MarketRepository()
            >>> top_markets = repo.get_top_markets_by_volume(limit=10)
            >>> for m in top_markets:
            ...     print(f"{m.question}: ${m.volume:,.0f}")
        """
        with get_session(self._engine) as session:
            # Subquery to get the latest snapshot for each market
            latest_subq = (
                select(
                    MarketSnapshot.polymarket_id,
                    func.max(MarketSnapshot.snapshot_at).label("max_snapshot"),
                )
                .group_by(MarketSnapshot.polymarket_id)
                .subquery()
            )

            stmt = (
                select(MarketSnapshot)
                .join(
                    latest_subq,
                    (MarketSnapshot.polymarket_id == latest_subq.c.polymarket_id)
                    & (MarketSnapshot.snapshot_at == latest_subq.c.max_snapshot),
                )
                .where(MarketSnapshot.volume.isnot(None))
                .order_by(MarketSnapshot.volume.desc())
                .limit(limit)
            )

            result = session.execute(stmt)
            markets = list(result.scalars().all())

            session.expunge_all()
            return markets

    def search_markets(self, query: str, limit: int = 20) -> list[MarketSnapshot]:
        """Search markets by question text.

        Performs a case-insensitive search on the market question field.
        Returns the latest snapshot for each matching market.

        Args:
            query: Search string to match against market questions.
            limit: Maximum number of results. Defaults to 20.

        Returns:
            List of MarketSnapshot objects matching the search query.

        Example:
            >>> repo = MarketRepository()
            >>> results = repo.search_markets("election", limit=10)
            >>> for m in results:
            ...     print(m.question)
        """
        with get_session(self._engine) as session:
            # Subquery to get the latest snapshot for each market
            latest_subq = (
                select(
                    MarketSnapshot.polymarket_id,
                    func.max(MarketSnapshot.snapshot_at).label("max_snapshot"),
                )
                .group_by(MarketSnapshot.polymarket_id)
                .subquery()
            )

            stmt = (
                select(MarketSnapshot)
                .join(
                    latest_subq,
                    (MarketSnapshot.polymarket_id == latest_subq.c.polymarket_id)
                    & (MarketSnapshot.snapshot_at == latest_subq.c.max_snapshot),
                )
                .where(MarketSnapshot.question.ilike(f"%{query}%"))
                .order_by(MarketSnapshot.snapshot_at.desc())
                .limit(limit)
            )

            result = session.execute(stmt)
            markets = list(result.scalars().all())

            session.expunge_all()
            return markets

    # -------------------------------------------------------------------------
    # DataFrame Methods (for notebooks)
    # -------------------------------------------------------------------------

    def get_markets_df(
        self,
        limit: int = 100,
        active_only: bool = True,
    ) -> pd.DataFrame:
        """Get markets as a pandas DataFrame.

        Converts market snapshots to a DataFrame for easy analysis in
        Jupyter notebooks. Includes the most relevant columns for analysis.

        Args:
            limit: Maximum number of markets to return. Defaults to 100.
            active_only: If True, only return active markets. Defaults to True.

        Returns:
            DataFrame with columns: polymarket_id, question, yes_price, no_price,
            volume, volume_24h, liquidity, status, active, end_date, snapshot_at.

        Example:
            >>> repo = MarketRepository()
            >>> df = repo.get_markets_df(limit=50)
            >>> df[['question', 'yes_price', 'volume']].head()
        """
        markets = self.get_latest_markets(limit=limit, active_only=active_only)

        if not markets:
            return pd.DataFrame(
                columns=[
                    "polymarket_id",
                    "question",
                    "yes_price",
                    "no_price",
                    "volume",
                    "volume_24h",
                    "liquidity",
                    "status",
                    "active",
                    "end_date",
                    "snapshot_at",
                ]
            )

        data = [
            {
                "polymarket_id": m.polymarket_id,
                "question": m.question,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "volume": m.volume,
                "volume_24h": m.volume_24h,
                "liquidity": m.liquidity,
                "status": m.status,
                "active": m.active,
                "end_date": m.end_date,
                "snapshot_at": m.snapshot_at,
            }
            for m in markets
        ]

        return pd.DataFrame(data)

    def get_price_history_df(
        self,
        token_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Get price history as a pandas DataFrame.

        Converts price points to a DataFrame optimized for time series
        analysis in Jupyter notebooks. Sets timestamp as the index.

        Args:
            token_id: The token identifier to get prices for.
            start_date: Optional start date filter (inclusive).
            end_date: Optional end date filter (inclusive).

        Returns:
            DataFrame with columns: price, best_bid, best_ask, spread.
            Index is the timestamp.

        Example:
            >>> repo = MarketRepository()
            >>> df = repo.get_price_history_df("token_abc")
            >>> df['price'].plot(title="Price History")
        """
        points = self.get_price_history(
            token_id=token_id,
            start_date=start_date,
            end_date=end_date,
        )

        if not points:
            return pd.DataFrame(
                columns=["price", "best_bid", "best_ask", "spread"],
                index=pd.DatetimeIndex([], name="timestamp"),
            )

        data = [
            {
                "timestamp": p.timestamp,
                "price": p.price,
                "best_bid": p.best_bid,
                "best_ask": p.best_ask,
                "spread": p.spread,
            }
            for p in points
        ]

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    # -------------------------------------------------------------------------
    # Write Methods
    # -------------------------------------------------------------------------

    def save_market_snapshot(self, snapshot: MarketSnapshot) -> MarketSnapshot:
        """Save a market snapshot to the database.

        Args:
            snapshot: MarketSnapshot object to save.

        Returns:
            The saved MarketSnapshot with generated id.

        Example:
            >>> repo = MarketRepository()
            >>> from cuic_quant.database import MarketSnapshot
            >>> snapshot = MarketSnapshot(
            ...     polymarket_id="market_new",
            ...     question="Will X happen?",
            ...     yes_price=0.5,
            ... )
            >>> saved = repo.save_market_snapshot(snapshot)
            >>> print(saved.id)  # Generated ID
        """
        with get_session(self._engine) as session:
            session.add(snapshot)
            session.flush()  # Get the generated ID
            session.expunge(snapshot)
            return snapshot

    def save_price_point(self, point: PricePoint) -> PricePoint:
        """Save a price point to the database.

        Args:
            point: PricePoint object to save.

        Returns:
            The saved PricePoint with generated id.

        Example:
            >>> repo = MarketRepository()
            >>> from cuic_quant.database import PricePoint
            >>> from datetime import datetime
            >>> point = PricePoint(
            ...     token_id="token_abc",
            ...     price=0.65,
            ...     timestamp=datetime.utcnow(),
            ... )
            >>> saved = repo.save_price_point(point)
        """
        with get_session(self._engine) as session:
            session.add(point)
            session.flush()
            session.expunge(point)
            return point

    def bulk_save_markets(self, snapshots: list[MarketSnapshot]) -> int:
        """Bulk save multiple market snapshots.

        Efficiently saves multiple snapshots in a single transaction.

        Args:
            snapshots: List of MarketSnapshot objects to save.

        Returns:
            Number of snapshots saved.

        Example:
            >>> repo = MarketRepository()
            >>> snapshots = [MarketSnapshot(...), MarketSnapshot(...)]
            >>> count = repo.bulk_save_markets(snapshots)
            >>> print(f"Saved {count} markets")
        """
        if not snapshots:
            return 0

        with get_session(self._engine) as session:
            session.add_all(snapshots)
            session.flush()
            return len(snapshots)

    def bulk_save_price_points(self, points: list[PricePoint]) -> int:
        """Bulk save multiple price points.

        Efficiently saves multiple price points in a single transaction.
        Handles duplicate constraint violations gracefully by skipping
        duplicates.

        Args:
            points: List of PricePoint objects to save.

        Returns:
            Number of price points saved.

        Example:
            >>> repo = MarketRepository()
            >>> points = [PricePoint(...), PricePoint(...)]
            >>> count = repo.bulk_save_price_points(points)
            >>> print(f"Saved {count} price points")
        """
        if not points:
            return 0

        with get_session(self._engine) as session:
            session.add_all(points)
            session.flush()
            return len(points)

    # -------------------------------------------------------------------------
    # Stats Methods
    # -------------------------------------------------------------------------

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the collected data.

        Returns counts and date ranges for markets and price points.
        Useful for monitoring data collection health.

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
            >>> repo = MarketRepository()
            >>> stats = repo.get_collection_stats()
            >>> print(f"Total markets: {stats['total_markets']}")
            >>> print(f"Date range: {stats['oldest_snapshot']} to {stats['newest_snapshot']}")
        """
        with get_session(self._engine) as session:
            # Market statistics
            total_snapshots = session.execute(
                select(func.count(MarketSnapshot.id))
            ).scalar_one()

            total_markets = session.execute(
                select(func.count(func.distinct(MarketSnapshot.polymarket_id)))
            ).scalar_one()

            active_markets = session.execute(
                select(func.count(func.distinct(MarketSnapshot.polymarket_id))).where(
                    MarketSnapshot.active == True  # noqa: E712
                )
            ).scalar_one()

            oldest_snapshot = session.execute(
                select(func.min(MarketSnapshot.snapshot_at))
            ).scalar_one()

            newest_snapshot = session.execute(
                select(func.max(MarketSnapshot.snapshot_at))
            ).scalar_one()

            # Price point statistics
            total_price_points = session.execute(
                select(func.count(PricePoint.id))
            ).scalar_one()

            oldest_price = session.execute(
                select(func.min(PricePoint.timestamp))
            ).scalar_one()

            newest_price = session.execute(
                select(func.max(PricePoint.timestamp))
            ).scalar_one()

            return {
                "total_markets": total_markets,
                "total_snapshots": total_snapshots,
                "total_price_points": total_price_points,
                "active_markets": active_markets,
                "oldest_snapshot": oldest_snapshot,
                "newest_snapshot": newest_snapshot,
                "oldest_price": oldest_price,
                "newest_price": newest_price,
            }
