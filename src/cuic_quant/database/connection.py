"""Database connection manager for Polymarket data storage.

This module provides SQLAlchemy engine and session management utilities
for connecting to the database that stores prediction market data.

Supports both SQLite (local development) and PostgreSQL/CockroachDB (production).
Set DATABASE_URL environment variable for cloud database, or leave unset for SQLite.

Example:
    >>> from cuic_quant.database.connection import get_engine, get_session, init_db
    >>>
    >>> # Initialize database with custom path
    >>> engine = get_engine("data/my_database.db")
    >>> init_db(engine)
    >>>
    >>> # Use session context manager for queries
    >>> with get_session(engine) as session:
    ...     from cuic_quant.database import Event
    ...     events = session.query(Event).all()
    ...     print(f"Found {len(events)} events")
    >>>
    >>> # Or use the default singleton engine
    >>> from cuic_quant.database.connection import get_default_engine
    >>> engine = get_default_engine()  # Auto-initializes database

Functions:
    - get_database_url: Build database connection URL
    - get_engine: Create SQLAlchemy engine instance
    - get_session_factory: Create session factory for engine
    - init_db: Initialize database schema
    - get_session: Context manager for database sessions
    - get_default_engine: Singleton engine with auto-initialization
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from cuic_quant.database.models import Base

# Module-level singleton for the default engine
_default_engine: Engine | None = None
_default_engine_lock = threading.Lock()

# Default database path relative to project root (for SQLite fallback)
DEFAULT_DB_PATH = "data/polymarket.db"


def get_database_url(db_path: str | Path | None = None) -> str:
    """Build database connection URL.

    Priority:
    1. DATABASE_URL environment variable (for CockroachDB/PostgreSQL)
    2. db_path argument (for SQLite)
    3. POLYMARKET_DB_PATH environment variable (for SQLite)
    4. Default SQLite path (data/polymarket.db)

    Args:
        db_path: Path to SQLite database file. Ignored if DATABASE_URL is set.

    Returns:
        Database connection URL.

    Example:
        >>> # With DATABASE_URL set, returns that URL
        >>> # Without DATABASE_URL, returns SQLite URL
        >>> get_database_url("data/test.db")
        'sqlite:///data/test.db'
    """
    # Check for cloud database URL first (CockroachDB/PostgreSQL)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Convert postgresql:// to cockroachdb:// for CockroachDB hosts
        if "cockroachlabs.cloud" in database_url or "cockroachdb" in database_url.lower():
            database_url = database_url.replace("postgresql://", "cockroachdb://", 1)
        return database_url

    # Fall back to SQLite
    if db_path is None:
        db_path = os.environ.get("POLYMARKET_DB_PATH", DEFAULT_DB_PATH)

    # Convert to Path for directory creation
    path = Path(db_path)

    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{path}"


def get_engine(db_path: str | Path | None = None, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for the database.

    Automatically detects whether to use SQLite or PostgreSQL/CockroachDB
    based on the DATABASE_URL environment variable.

    Args:
        db_path: Path to SQLite database file. Ignored if DATABASE_URL is set.
        echo: If True, logs all SQL statements to stdout.

    Returns:
        SQLAlchemy Engine instance configured for the database.

    Example:
        >>> engine = get_engine("data/test.db")
        >>> engine = get_engine(echo=True)  # Logs SQL statements
    """
    url = get_database_url(db_path)

    # Configure based on database type
    if url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL/CockroachDB configuration
        engine = create_engine(
            url,
            echo=echo,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before use
        )

    return engine


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to an engine.

    Creates a sessionmaker instance configured for the given engine.
    Sessions created by this factory have `expire_on_commit=False`,
    which allows accessing object attributes after the session commits
    without triggering additional database queries.

    Args:
        engine: SQLAlchemy Engine to bind sessions to.

    Returns:
        Session factory that can be called to create new sessions.

    Example:
        >>> engine = get_engine("data/test.db")
        >>> SessionFactory = get_session_factory(engine)
        >>> session = SessionFactory()
        >>> # Use session for queries...
        >>> session.close()
    """
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,  # Allow detached object access
    )


def init_db(engine: Engine) -> None:
    """Initialize the database schema.

    Creates all tables defined in the ORM models if they don't exist.
    Safe to call multiple times - existing tables are not modified.

    Args:
        engine: SQLAlchemy Engine connected to the database.

    Example:
        >>> engine = get_engine("data/test.db")
        >>> init_db(engine)  # Creates tables
        >>> init_db(engine)  # Safe to call again
    """
    Base.metadata.create_all(engine)


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Provides a transactional scope for database operations. Automatically
    commits the transaction on successful completion, rolls back on
    exception, and closes the session in all cases.

    Args:
        engine: SQLAlchemy Engine to create the session from.

    Yields:
        SQLAlchemy Session for database operations.

    Raises:
        Exception: Re-raises any exception after rolling back the transaction.

    Example:
        >>> engine = get_engine("data/test.db")
        >>> init_db(engine)
        >>> with get_session(engine) as session:
        ...     from cuic_quant.database import Event
        ...     event = Event(polymarket_id="test123", title="Test Event")
        ...     session.add(event)
        ...     # Commits automatically on exit
        >>> # Session is closed here
    """
    session_factory = get_session_factory(engine)
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_default_engine() -> Engine:
    """Get the singleton default engine instance.

    Returns a shared engine instance, creating it on first access.
    The database is automatically initialized (tables created) when
    the engine is first created.

    This function implements the singleton pattern to avoid creating
    multiple engine instances for the default database, which is
    more efficient for resource management. Thread-safe via double-checked
    locking.

    Returns:
        The default SQLAlchemy Engine instance.

    Example:
        >>> engine1 = get_default_engine()
        >>> engine2 = get_default_engine()
        >>> engine1 is engine2  # Same instance
        True
        >>> # Database tables are automatically created
    """
    global _default_engine

    if _default_engine is None:
        with _default_engine_lock:
            if _default_engine is None:  # Double-check inside lock
                _default_engine = get_engine()
                init_db(_default_engine)

    return _default_engine
