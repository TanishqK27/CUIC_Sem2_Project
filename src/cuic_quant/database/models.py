"""SQLAlchemy ORM base class for database models.

This module provides the declarative base for all SQLAlchemy models.
Platform-specific models should be defined in their respective modules.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models inherit from this class to share common metadata
    and configuration settings.
    """

    pass
