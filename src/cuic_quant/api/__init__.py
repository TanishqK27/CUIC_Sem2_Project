"""FastAPI application for Polymarket data API.

This module provides a REST API for accessing collected Polymarket data,
including market snapshots, price history, and collection statistics.

Example:
    >>> from cuic_quant.api import app
    >>> # Run with uvicorn
    >>> import uvicorn
    >>> uvicorn.run(app, host="0.0.0.0", port=8000)

    Or from command line:
    >>> uvicorn cuic_quant.api:app --reload

Exports:
    - app: FastAPI application instance
    - create_app: Factory function to create the FastAPI app
"""

from cuic_quant.api.main import app, create_app

__all__ = ["app", "create_app"]
