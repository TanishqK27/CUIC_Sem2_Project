"""Database module for Polymarket data storage.

This module provides SQLAlchemy ORM models and database utilities for
persisting prediction market data including events, market snapshots,
and price time series.

Example:
    >>> from cuic_quant.database import get_engine, get_session, init_db, Event
    >>>
    >>> # Initialize database
    >>> engine = get_engine("data/polymarket.db")
    >>> init_db(engine)
    >>>
    >>> # Use session for queries
    >>> with get_session(engine) as session:
    ...     events = session.query(Event).all()
    >>>
    >>> # Or use the default singleton engine
    >>> from cuic_quant.database import get_default_engine
    >>> engine = get_default_engine()  # Auto-initializes

Models:
    - Base: SQLAlchemy declarative base
    - Event: Polymarket event (group of related markets)
    - MarketSnapshot: Point-in-time market state
    - PricePoint: Time series price data
    - CollectionRun: Data collection job metadata

Connection Functions:
    - get_engine: Create SQLAlchemy engine instance
    - get_session: Context manager for database sessions
    - init_db: Initialize database with schema
    - get_default_engine: Singleton engine with auto-initialization
"""

from cuic_quant.database.connection import (
    get_default_engine,
    get_engine,
    get_session,
    init_db,
)
from cuic_quant.database.models import (
    Base,
    CollectionRun,
    Event,
    MarketSnapshot,
    PricePoint,
)

__all__ = [
    # Base class
    "Base",
    # Models
    "Event",
    "MarketSnapshot",
    "PricePoint",
    "CollectionRun",
    # Connection functions
    "get_engine",
    "get_session",
    "init_db",
    "get_default_engine",
]
