"""Trading and betting strategies for prediction markets and sports betting.

This module provides strategies including:
- Kelly Criterion: Optimal bet sizing
- Arbitrage: Cross-market opportunity detection
- Mean Reversion: Statistical mean reversion strategies

Example:
    >>> from cuic_quant.strategies import calculate_kelly_fraction, find_arbitrage
    >>>
    >>> # Optimal bet sizing
    >>> fraction = calculate_kelly_fraction(0.55, 2.0)
    >>> print(f"Bet {fraction:.1%} of bankroll")
    >>>
    >>> # Find arbitrage
    >>> opportunities = find_arbitrage([1.91, 2.10], [1.95, 2.05])
"""

from cuic_quant.strategies.arbitrage import find_arbitrage
from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction
from cuic_quant.strategies.mean_reversion import mean_reversion_signal

__all__ = [
    "calculate_kelly_fraction",
    "find_arbitrage",
    "mean_reversion_signal",
]
