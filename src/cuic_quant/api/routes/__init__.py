"""API route modules for Polymarket data endpoints.

This package contains FastAPI router modules that define the REST API
endpoints for accessing market data.

Routers:
    - markets: Endpoints for market snapshots, search, and price history
"""

from cuic_quant.api.routes.markets import router as markets_router

__all__ = ["markets_router"]
