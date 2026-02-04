"""FastAPI application for Polymarket data API.

This module provides the main FastAPI application setup including
CORS middleware, lifespan management, and route configuration.

Example:
    >>> from cuic_quant.api import app
    >>> # Run with uvicorn
    >>> import uvicorn
    >>> uvicorn.run(app, host="0.0.0.0", port=8000)

    Or from command line:
    >>> uvicorn cuic_quant.api:app --reload

Environment Variables:
    - ENABLE_COLLECTION: Set to "true" to enable automatic collection
      scheduler on startup. Default is disabled.
    - POLYMARKET_DB_PATH: Path to the SQLite database file.
      Default is "data/polymarket.db".
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cuic_quant.api.routes import markets_router
from cuic_quant.collector import CollectionScheduler
from cuic_quant.database import get_default_engine, init_db

logger = logging.getLogger(__name__)

# Module-level scheduler reference for lifespan management
_scheduler: CollectionScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI application.

    Handles startup and shutdown events for the application:

    Startup:
        - Initializes the database schema (creates tables if needed)
        - Optionally starts the CollectionScheduler if ENABLE_COLLECTION
          environment variable is set to "true"

    Shutdown:
        - Stops the CollectionScheduler if it was started

    Args:
        app: The FastAPI application instance.

    Yields:
        None - control returns to the application during runtime.

    Example:
        >>> app = FastAPI(lifespan=lifespan)
        >>> # ENABLE_COLLECTION=true uvicorn cuic_quant.api:app
    """
    global _scheduler

    # Startup
    logger.info("Starting Polymarket API server...")

    # Initialize database
    engine = get_default_engine()
    init_db(engine)
    logger.info("Database initialized")

    # Optionally start collection scheduler
    enable_collection = os.environ.get("ENABLE_COLLECTION", "").lower() == "true"

    if enable_collection:
        logger.info("Starting collection scheduler...")
        _scheduler = CollectionScheduler()
        _scheduler.start()
        logger.info("Collection scheduler started")
    else:
        logger.info("Collection scheduler disabled (set ENABLE_COLLECTION=true to enable)")

    yield

    # Shutdown
    logger.info("Shutting down Polymarket API server...")

    if _scheduler is not None and _scheduler.is_running:
        logger.info("Stopping collection scheduler...")
        _scheduler.stop()
        _scheduler = None
        logger.info("Collection scheduler stopped")


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application.

    Creates and configures a FastAPI application with:
        - Title, description, and version metadata
        - CORS middleware with configurable origins via CORS_ORIGINS env var
        - Markets API router at /api/v1 prefix
        - Root endpoint with API information
        - Health check endpoint

    Returns:
        Configured FastAPI application instance.

    Environment Variables:
        - CORS_ORIGINS: Comma-separated list of allowed origins.
          Defaults to "http://localhost:3000,http://localhost:8000" for development.

    Example:
        >>> app = create_app()
        >>> # Customize settings if needed
        >>> app.title = "My Custom API"
        >>>
        >>> # Run with uvicorn
        >>> import uvicorn
        >>> uvicorn.run(app)
    """
    application = FastAPI(
        title="Polymarket Data API",
        description=(
            "REST API for accessing collected Polymarket prediction market data. "
            "Provides endpoints for market snapshots, price history, search, "
            "and collection statistics."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # Get CORS origins from environment variable for security
    # Default to localhost origins for development
    cors_origins_str = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
    )
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

    # Add CORS middleware with configured origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    application.include_router(markets_router, prefix="/api/v1")

    # Root endpoint
    @application.get("/", tags=["root"])
    def root() -> dict[str, str]:
        """Root endpoint with API information.

        Returns:
            Dictionary with API name, version, and documentation URL.
        """
        return {
            "name": "Polymarket Data API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    # Health check endpoint
    @application.get("/health", tags=["root"])
    def health() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Dictionary with status "ok" if the API is running.
        """
        return {"status": "ok"}

    return application


# Create the application instance at module level
app = create_app()
