"""CUIC Quant Fund - Quantitative Research for Prediction Markets & Sports Betting.

This package provides tools for:
- API clients for prediction markets (Kalshi) and sports betting odds
- Statistical models for probability estimation
- Trading strategies (arbitrage, mean reversion, Kelly criterion)
- Backtesting framework for strategy validation

Example:
    >>> from cuic_quant.data import KalshiClient, OddsAPIClient
    >>> from cuic_quant.strategies import calculate_kelly_fraction
    >>> fraction = calculate_kelly_fraction(0.55, 2.0)
"""

__version__ = "0.1.0"
__author__ = "Cardiff University Investment Club Quant Team"

# Convenience imports (optional in lightweight environments like notebook tests)
__all__ = []

try:
    from cuic_quant.data import KalshiClient, OddsAPIClient

    __all__.extend([
        "KalshiClient",
        "OddsAPIClient",
    ])
except Exception:
    # Allow importing subpackages (e.g., cuic_quant.metrics) even when
    # optional runtime deps for API clients are unavailable.
    pass

try:
    from cuic_quant.strategies import (
        calculate_kelly_fraction,
        find_arbitrage,
        mean_reversion_signal,
    )

    __all__.extend([
        "calculate_kelly_fraction",
        "find_arbitrage",
        "mean_reversion_signal",
    ])
except Exception:
    # Same rationale as above: keep package import non-fatal for metrics workflows.
    pass
