"""Database module for Polymarket data storage.

This module provides SQLAlchemy ORM models and database utilities for
persisting prediction market data including events, market snapshots,
and price time series.

Example:
    >>> from cuic_quant.database import Base, MarketSnapshot, init_db
    >>>
    >>> # Initialize database
    >>> engine = init_db("sqlite:///polymarket.db")
    >>>
    >>> # Use session for queries
    >>> with get_session() as session:
    ...     snapshots = session.query(MarketSnapshot).all()

Models:
    - Base: SQLAlchemy declarative base
    - Event: Polymarket event (group of related markets)
    - MarketSnapshot: Point-in-time market state
    - PricePoint: Time series price data
    - CollectionRun: Data collection job metadata

Connection Functions (implemented in Task 3):
    - get_engine: Get SQLAlchemy engine instance
    - get_session: Get database session context manager
    - init_db: Initialize database with schema
"""

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
    # Connection functions (to be implemented in Task 3)
    # "get_engine",
    # "get_session",
    # "init_db",
]
