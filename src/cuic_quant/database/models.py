"""SQLAlchemy ORM models for Polymarket data storage.

This module defines the database schema for storing prediction market data
including events, market snapshots, price time series, and collection run metadata.

Example:
    >>> from cuic_quant.database import Base, MarketSnapshot, get_engine
    >>> from sqlalchemy import create_engine
    >>>
    >>> engine = create_engine("sqlite:///polymarket.db")
    >>> Base.metadata.create_all(engine)

Models:
    - Event: Polymarket events (groups of related markets)
    - MarketSnapshot: Point-in-time market state
    - PricePoint: Time series price data for tokens
    - CollectionRun: Metadata for data collection jobs
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models inherit from this class to share common metadata
    and configuration settings.
    """

    pass


class Event(Base):
    """Polymarket event representing a group of related markets.

    Events are the top-level containers in Polymarket that group multiple
    related prediction markets together (e.g., "2024 US Presidential Election"
    may contain markets for different candidates).

    Attributes:
        id: Auto-incrementing primary key.
        polymarket_id: Unique identifier from Polymarket API.
        slug: URL-friendly identifier.
        title: Event display title.
        description: Detailed event description.
        category: Event category (e.g., "politics", "sports").
        active: Whether the event is currently active.
        closed: Whether the event has been resolved.
        volume: Total trading volume in USDC.
        liquidity: Current liquidity in USDC.
        start_date: When the event starts (if applicable).
        end_date: When the event ends/resolves.
        created_at: Record creation timestamp.
        updated_at: Record last update timestamp.
        market_snapshots: Related market snapshots.

    Example:
        >>> event = Event(
        ...     polymarket_id="abc123",
        ...     title="2024 US Presidential Election",
        ...     category="politics",
        ...     active=True,
        ... )
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    polymarket_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    market_snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        "MarketSnapshot", back_populates="event", lazy="dynamic"
    )

    def __repr__(self) -> str:
        """Return string representation of the event."""
        return f"<Event(id={self.id}, polymarket_id={self.polymarket_id!r}, title={self.title!r})>"


class MarketSnapshot(Base):
    """Point-in-time snapshot of a Polymarket market.

    Captures the state of a market at a specific moment, including
    prices, volume, and metadata. Multiple snapshots over time
    enable historical analysis of market evolution.

    Attributes:
        id: Auto-incrementing primary key.
        polymarket_id: Market identifier from Polymarket API.
        event_id: Foreign key to parent event.
        question: The prediction question being traded.
        description: Detailed market description.
        slug: URL-friendly identifier.
        yes_token_id: Token ID for YES outcome.
        no_token_id: Token ID for NO outcome.
        yes_price: Current YES token price (0-1).
        no_price: Current NO token price (0-1).
        volume: Total market volume in USDC.
        volume_24h: 24-hour trading volume.
        liquidity: Current market liquidity.
        status: Market status (e.g., "active", "resolved").
        active: Whether trading is currently enabled.
        end_date: When the market resolves.
        snapshot_at: When this snapshot was taken.
        event: Parent event relationship.
        price_points: Related price point records.

    Example:
        >>> snapshot = MarketSnapshot(
        ...     polymarket_id="market123",
        ...     question="Will candidate X win?",
        ...     yes_price=0.65,
        ...     no_price=0.35,
        ...     snapshot_at=datetime.utcnow(),
        ... )
    """

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    polymarket_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("events.id"), nullable=True
    )

    question: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True)

    yes_token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    no_token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    yes_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    no_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    event: Mapped["Event | None"] = relationship(
        "Event", back_populates="market_snapshots"
    )
    price_points: Mapped[list["PricePoint"]] = relationship(
        "PricePoint", back_populates="market_snapshot", lazy="dynamic"
    )

    __table_args__ = (
        Index("ix_market_snapshots_polymarket_id_snapshot_at", "polymarket_id", "snapshot_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of the market snapshot."""
        return (
            f"<MarketSnapshot(id={self.id}, polymarket_id={self.polymarket_id!r}, "
            f"yes_price={self.yes_price}, snapshot_at={self.snapshot_at})>"
        )


class PricePoint(Base):
    """Time series price data for a market token.

    Records individual price observations for YES/NO tokens,
    including order book data when available. Used for building
    historical price series and analyzing market microstructure.

    Attributes:
        id: Auto-incrementing primary key.
        market_id: Foreign key to market snapshot.
        token_id: Token identifier (YES or NO token).
        price: Token price at this timestamp (0-1).
        timestamp: When this price was observed.
        best_bid: Best bid price from order book.
        best_ask: Best ask price from order book.
        spread: Bid-ask spread.
        created_at: Record creation timestamp.
        market_snapshot: Parent market snapshot.

    Example:
        >>> price_point = PricePoint(
        ...     token_id="token_abc",
        ...     price=0.65,
        ...     timestamp=datetime.utcnow(),
        ...     best_bid=0.64,
        ...     best_ask=0.66,
        ...     spread=0.02,
        ... )
    """

    __tablename__ = "price_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    market_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("market_snapshots.id"), nullable=True
    )
    token_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    best_bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    spread: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    market_snapshot: Mapped["MarketSnapshot | None"] = relationship(
        "MarketSnapshot", back_populates="price_points"
    )

    __table_args__ = (
        UniqueConstraint("token_id", "timestamp", name="uq_price_points_token_timestamp"),
        Index("ix_price_points_token_id_timestamp", "token_id", "timestamp"),
    )

    def __repr__(self) -> str:
        """Return string representation of the price point."""
        return (
            f"<PricePoint(id={self.id}, token_id={self.token_id!r}, "
            f"price={self.price}, timestamp={self.timestamp})>"
        )


class CollectionRun(Base):
    """Metadata for a data collection job execution.

    Tracks when collection jobs run, their status, and statistics
    about the data collected. Useful for monitoring data pipeline
    health and debugging collection issues.

    Attributes:
        id: Auto-incrementing primary key.
        started_at: When the collection job started.
        completed_at: When the collection job finished.
        status: Job status (e.g., "running", "completed", "failed").
        markets_collected: Number of markets collected in this run.
        events_collected: Number of events collected in this run.
        price_points_collected: Number of price points collected.
        error_message: Error details if the job failed.

    Example:
        >>> run = CollectionRun(
        ...     started_at=datetime.utcnow(),
        ...     status="running",
        ... )
        >>> # After completion
        >>> run.completed_at = datetime.utcnow()
        >>> run.status = "completed"
        >>> run.markets_collected = 150
    """

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)

    markets_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_collected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_points_collected: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return string representation of the collection run."""
        return (
            f"<CollectionRun(id={self.id}, status={self.status!r}, "
            f"started_at={self.started_at})>"
        )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate the duration of the collection run in seconds.

        Returns:
            Duration in seconds, or None if not yet completed.
        """
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()
