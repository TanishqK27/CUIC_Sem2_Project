"""Kelly Criterion for optimal bet sizing.

The Kelly Criterion determines the optimal fraction of bankroll to wager
to maximize long-term growth rate while avoiding ruin.

Example:
    >>> from cuic_quant.strategies import calculate_kelly_fraction
    >>>
    >>> # You estimate 55% win probability, odds are 2.0 (even money)
    >>> fraction = calculate_kelly_fraction(0.55, 2.0)
    >>> print(f"Optimal bet: {fraction:.1%} of bankroll")  # 10%
    >>>
    >>> # Use fractional Kelly for more conservative sizing
    >>> fraction = calculate_kelly_fraction(0.55, 2.0, kelly_fraction=0.5)
    >>> print(f"Half Kelly: {fraction:.1%} of bankroll")  # 5%

References:
    - Kelly, J.L. (1956). "A New Interpretation of Information Rate"
    - Thorp, E.O. (2006). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
"""

from __future__ import annotations


def calculate_kelly_fraction(
    win_probability: float,
    decimal_odds: float,
    kelly_fraction: float = 1.0,
    max_fraction: float = 0.25,
) -> float:
    """Calculate the optimal Kelly Criterion bet size.

    The Kelly Criterion formula:
        f* = (bp - q) / b

    Where:
        f* = fraction of bankroll to bet
        b = decimal odds - 1 (net odds received on win)
        p = probability of winning
        q = probability of losing (1 - p)

    Args:
        win_probability: Your estimated probability of winning (0-1).
        decimal_odds: The decimal odds offered (e.g., 2.0 for even money).
        kelly_fraction: Fraction of Kelly to use (default 1.0 = full Kelly).
            Common values: 0.25 (quarter), 0.5 (half).
        max_fraction: Maximum bet as fraction of bankroll (default 25%).

    Returns:
        Optimal fraction of bankroll to bet (0 to max_fraction).

    Raises:
        ValueError: If win_probability not in [0, 1] or decimal_odds <= 1.

    Example:
        >>> # 60% edge at 2:1 odds
        >>> calculate_kelly_fraction(0.6, 2.0)
        0.2

        >>> # Same with half Kelly (more conservative)
        >>> calculate_kelly_fraction(0.6, 2.0, kelly_fraction=0.5)
        0.1

        >>> # No edge - don't bet
        >>> calculate_kelly_fraction(0.5, 2.0)
        0.0

        >>> # Negative edge - don't bet
        >>> calculate_kelly_fraction(0.4, 2.0)
        0.0
    """
    # Validate inputs
    if not 0 <= win_probability <= 1:
        raise ValueError(
            f"win_probability must be between 0 and 1, got {win_probability}"
        )

    if decimal_odds <= 1:
        raise ValueError(f"decimal_odds must be greater than 1, got {decimal_odds}")

    if not 0 < kelly_fraction <= 1:
        raise ValueError(
            f"kelly_fraction must be between 0 and 1, got {kelly_fraction}"
        )

    # Calculate Kelly
    b = decimal_odds - 1  # Net odds (profit per unit wagered)
    p = win_probability
    q = 1 - p

    kelly = (b * p - q) / b

    # Apply fractional Kelly
    kelly = kelly * kelly_fraction

    # Clamp to valid range
    kelly = max(0, min(max_fraction, kelly))

    return kelly


def calculate_kelly_for_multiple_bets(
    bets: list[tuple[float, float]],
    kelly_fraction: float = 0.5,
) -> list[float]:
    """Calculate Kelly fractions for multiple simultaneous bets.

    For multiple correlated bets, this uses an approximation where
    individual Kelly fractions are scaled down if their sum exceeds 1.

    Note:
        True multi-outcome Kelly requires optimization. This is a
        simplified approximation suitable for uncorrelated bets.

    Args:
        bets: List of (win_probability, decimal_odds) tuples.
        kelly_fraction: Fraction of Kelly to use for each bet.

    Returns:
        List of bet fractions corresponding to each input bet.

    Example:
        >>> bets = [(0.55, 2.0), (0.60, 1.9), (0.52, 2.1)]
        >>> fractions = calculate_kelly_for_multiple_bets(bets)
        >>> for (p, odds), f in zip(bets, fractions):
        ...     print(f"P={p}, Odds={odds}: Bet {f:.1%}")
    """
    # Calculate individual Kelly fractions
    fractions = []
    for prob, odds in bets:
        try:
            f = calculate_kelly_fraction(prob, odds, kelly_fraction)
        except ValueError:
            f = 0.0
        fractions.append(f)

    # Scale down if total exceeds 1
    total = sum(fractions)
    if total > 1:
        fractions = [f / total for f in fractions]

    return fractions


def expected_growth_rate(
    win_probability: float,
    decimal_odds: float,
    bet_fraction: float,
) -> float:
    """Calculate expected logarithmic growth rate for a bet.

    The Kelly Criterion maximizes this value.

    Args:
        win_probability: Probability of winning.
        decimal_odds: Decimal odds offered.
        bet_fraction: Fraction of bankroll to bet.

    Returns:
        Expected log growth rate per bet.

    Example:
        >>> # Full Kelly maximizes growth
        >>> kelly = calculate_kelly_fraction(0.55, 2.0)
        >>> growth = expected_growth_rate(0.55, 2.0, kelly)
        >>> print(f"Expected growth: {growth:.4f}")
    """
    import math

    if bet_fraction <= 0:
        return 0.0

    if bet_fraction >= 1:
        # Betting everything - if we lose, we're ruined
        if win_probability < 1:
            return float("-inf")
        return math.log(decimal_odds)

    p = win_probability
    q = 1 - p

    # E[log(wealth_ratio)] = p * log(1 + b*f) + q * log(1 - f)
    # where b = decimal_odds - 1, f = bet_fraction
    b = decimal_odds - 1

    win_term = p * math.log(1 + b * bet_fraction)
    lose_term = q * math.log(1 - bet_fraction)

    return win_term + lose_term


def kelly_from_american_odds(
    win_probability: float,
    american_odds: int,
    kelly_fraction: float = 1.0,
) -> float:
    """Calculate Kelly fraction from American odds.

    Args:
        win_probability: Your estimated probability of winning.
        american_odds: American-style odds (e.g., +150 or -150).
        kelly_fraction: Fraction of Kelly to use.

    Returns:
        Optimal fraction of bankroll to bet.

    Example:
        >>> kelly_from_american_odds(0.55, -110)  # Typical spread bet
        0.05
    """
    # Convert American to decimal
    if american_odds > 0:
        decimal_odds = (american_odds / 100) + 1
    elif american_odds < 0:
        decimal_odds = (100 / abs(american_odds)) + 1
    else:
        # american_odds == 0 is undefined; treat as even money
        decimal_odds = 2.0

    return calculate_kelly_fraction(win_probability, decimal_odds, kelly_fraction)
