"""Odds conversion utilities.

This module provides functions to convert between different odds formats:
- American (moneyline): +150, -110
- Decimal: 2.50, 1.91
- Fractional: 3/2, 10/11
- Implied probability: 0.40, 0.52

Example:
    >>> from cuic_quant.utils import american_to_decimal, decimal_to_implied_prob
    >>>
    >>> decimal_odds = american_to_decimal(150)  # +150
    >>> print(f"Decimal: {decimal_odds}")  # 2.5
    >>>
    >>> prob = decimal_to_implied_prob(decimal_odds)
    >>> print(f"Implied probability: {prob:.1%}")  # 40%
"""

from __future__ import annotations


def american_to_decimal(american: int | float) -> float:
    """Convert American odds to decimal odds.

    American odds indicate:
    - Positive: Profit on $100 stake
    - Negative: Stake needed to profit $100

    Args:
        american: American-style odds (e.g., 150 or -150).

    Returns:
        Equivalent decimal odds.

    Example:
        >>> american_to_decimal(150)   # +150
        2.5
        >>> american_to_decimal(-150)  # -150
        1.6666666666666667
        >>> american_to_decimal(-110)  # Standard vig line
        1.9090909090909092
    """
    if american > 0:
        return (american / 100) + 1
    elif american < 0:
        return (100 / abs(american)) + 1
    else:
        raise ValueError("American odds cannot be zero")


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American odds.

    Args:
        decimal: Decimal odds (e.g., 2.5, 1.91).

    Returns:
        Equivalent American odds (rounded to int).

    Example:
        >>> decimal_to_american(2.5)
        150
        >>> decimal_to_american(1.5)
        -200
        >>> decimal_to_american(1.91)
        -110
    """
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")

    if decimal >= 2.0:
        return int(round((decimal - 1) * 100))
    else:
        return int(round(-100 / (decimal - 1)))


def decimal_to_implied_prob(decimal: float) -> float:
    """Convert decimal odds to implied probability.

    Args:
        decimal: Decimal odds.

    Returns:
        Implied probability (0-1).

    Example:
        >>> decimal_to_implied_prob(2.0)
        0.5
        >>> decimal_to_implied_prob(1.5)
        0.6666666666666666
    """
    if decimal <= 0:
        raise ValueError("Decimal odds must be positive")

    return 1 / decimal


def implied_prob_to_decimal(prob: float) -> float:
    """Convert implied probability to decimal odds.

    Args:
        prob: Probability (0-1).

    Returns:
        Decimal odds.

    Raises:
        ValueError: If probability not in (0, 1].

    Example:
        >>> implied_prob_to_decimal(0.5)
        2.0
        >>> implied_prob_to_decimal(0.6)
        1.6666666666666667
    """
    if prob <= 0 or prob > 1:
        raise ValueError("Probability must be between 0 and 1")

    return 1 / prob


def american_to_implied_prob(american: int | float) -> float:
    """Convert American odds directly to implied probability.

    Args:
        american: American-style odds.

    Returns:
        Implied probability (0-1).

    Example:
        >>> american_to_implied_prob(-110)
        0.5238095238095238
        >>> american_to_implied_prob(100)
        0.5
    """
    decimal = american_to_decimal(american)
    return decimal_to_implied_prob(decimal)


def implied_prob_to_american(prob: float) -> int:
    """Convert implied probability directly to American odds.

    Args:
        prob: Probability (0-1).

    Returns:
        American odds.

    Example:
        >>> implied_prob_to_american(0.5)
        100
        >>> implied_prob_to_american(0.6)
        -150
    """
    decimal = implied_prob_to_decimal(prob)
    return decimal_to_american(decimal)


def fractional_to_decimal(numerator: int, denominator: int) -> float:
    """Convert fractional odds to decimal odds.

    Args:
        numerator: Fractional odds numerator.
        denominator: Fractional odds denominator.

    Returns:
        Decimal odds.

    Example:
        >>> fractional_to_decimal(3, 2)  # 3/2
        2.5
        >>> fractional_to_decimal(1, 2)  # 1/2
        1.5
    """
    if denominator == 0:
        raise ValueError("Denominator cannot be zero")

    return (numerator / denominator) + 1


def decimal_to_fractional(decimal: float) -> tuple[int, int]:
    """Convert decimal odds to fractional odds.

    Note: Returns simplified fraction, may lose precision.

    Args:
        decimal: Decimal odds.

    Returns:
        Tuple of (numerator, denominator).

    Example:
        >>> decimal_to_fractional(2.5)
        (3, 2)
        >>> decimal_to_fractional(1.5)
        (1, 2)
    """
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")

    from math import gcd

    # Convert to fraction
    profit = decimal - 1

    # Find reasonable denominator (try common ones)
    for denom in [1, 2, 4, 5, 8, 10, 11, 13, 20, 100]:
        numer = profit * denom
        if abs(numer - round(numer)) < 0.01:
            numer = int(round(numer))
            common = gcd(numer, denom)
            return (numer // common, denom // common)

    # Fallback: use 100 as denominator
    numer = int(round(profit * 100))
    common = gcd(numer, 100)
    return (numer // common, 100 // common)


def calculate_vig_from_odds(
    odds_a: float,
    odds_b: float,
    odds_format: str = "decimal",
) -> float:
    """Calculate bookmaker's vig (margin) from a two-way market.

    Args:
        odds_a: Odds for outcome A.
        odds_b: Odds for outcome B.
        odds_format: "decimal" or "american".

    Returns:
        Vig as a percentage (e.g., 4.76 for 4.76% vig).

    Example:
        >>> calculate_vig_from_odds(1.91, 1.91)  # Standard -110/-110
        4.761904761904766
        >>> calculate_vig_from_odds(-110, -110, "american")
        4.761904761904766
    """
    if odds_format == "american":
        odds_a = american_to_decimal(odds_a)
        odds_b = american_to_decimal(odds_b)

    prob_a = decimal_to_implied_prob(odds_a)
    prob_b = decimal_to_implied_prob(odds_b)

    vig = (prob_a + prob_b - 1) * 100
    return vig


def remove_vig_equal(
    odds_a: float,
    odds_b: float,
) -> tuple[float, float]:
    """Remove vig assuming equal distribution between outcomes.

    Args:
        odds_a: Decimal odds for outcome A.
        odds_b: Decimal odds for outcome B.

    Returns:
        Tuple of fair (no-vig) decimal odds for each outcome.

    Example:
        >>> remove_vig_equal(1.91, 1.91)
        (2.0, 2.0)
    """
    prob_a = decimal_to_implied_prob(odds_a)
    prob_b = decimal_to_implied_prob(odds_b)

    total = prob_a + prob_b

    fair_prob_a = prob_a / total
    fair_prob_b = prob_b / total

    return (
        implied_prob_to_decimal(fair_prob_a),
        implied_prob_to_decimal(fair_prob_b),
    )
