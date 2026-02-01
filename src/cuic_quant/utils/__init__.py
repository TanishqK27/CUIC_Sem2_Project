"""Utility functions for the CUIC Quant Fund project.

This module provides common utilities for:
- Odds conversion between formats
- Date/time handling
- Data validation
- Logging configuration
"""

from cuic_quant.utils.odds import (
    american_to_decimal,
    decimal_to_american,
    decimal_to_implied_prob,
    implied_prob_to_decimal,
)

__all__ = [
    "american_to_decimal",
    "decimal_to_american",
    "decimal_to_implied_prob",
    "implied_prob_to_decimal",
]
