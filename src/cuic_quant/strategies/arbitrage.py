"""Arbitrage detection for sports betting and prediction markets.

Arbitrage opportunities exist when the combined implied probability
across bookmakers/markets is less than 100%, guaranteeing a profit.

Example:
    >>> from cuic_quant.strategies import find_arbitrage
    >>>
    >>> # Bookmaker A: Team 1 at 2.10, Team 2 at 1.80
    >>> # Bookmaker B: Team 1 at 1.95, Team 2 at 2.00
    >>> result = find_arbitrage([2.10, 1.80], [1.95, 2.00])
    >>> if result:
    ...     print(f"Arbitrage found: {result['profit_pct']:.2f}% profit")

Note:
    - Real arbitrage opportunities are rare and short-lived
    - Transaction costs and betting limits reduce profitability
    - See docs/platforms/sports-betting-basics.md for more details
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity."""

    profit_pct: float
    stakes: list[float]
    odds: list[float]
    bookmakers: list[str]
    total_stake: float
    guaranteed_return: float

    @property
    def roi(self) -> float:
        """Return on investment as a decimal."""
        return self.profit_pct / 100


def find_arbitrage(
    odds_book_a: list[float],
    odds_book_b: list[float],
    book_a_name: str = "Book A",
    book_b_name: str = "Book B",
    total_stake: float = 100.0,
    min_profit_pct: float = 0.0,
) -> dict[str, Any] | None:
    """Find arbitrage opportunity between two bookmakers.

    For a two-outcome event, arbitrage exists when:
        (1/best_odds_1) + (1/best_odds_2) < 1

    Args:
        odds_book_a: [outcome_1_odds, outcome_2_odds] from bookmaker A.
        odds_book_b: [outcome_1_odds, outcome_2_odds] from bookmaker B.
        book_a_name: Name/identifier for bookmaker A.
        book_b_name: Name/identifier for bookmaker B.
        total_stake: Total amount to stake across all bets.
        min_profit_pct: Minimum profit percentage to report (default 0).

    Returns:
        Dictionary with arbitrage details, or None if no opportunity.

    Example:
        >>> # Book A has better Team 1 odds, Book B has better Team 2 odds
        >>> result = find_arbitrage([2.15, 1.85], [2.00, 2.05])
        >>> if result:
        ...     print(f"Profit: {result['profit_pct']:.2f}%")
        ...     print(f"Stakes: {result['stakes']}")
    """
    if len(odds_book_a) != 2 or len(odds_book_b) != 2:
        raise ValueError("Must provide exactly 2 outcomes per bookmaker")

    # Find best odds for each outcome across both books
    best_outcome_1 = max(odds_book_a[0], odds_book_b[0])
    best_outcome_2 = max(odds_book_a[1], odds_book_b[1])

    book_outcome_1 = book_a_name if odds_book_a[0] >= odds_book_b[0] else book_b_name
    book_outcome_2 = book_a_name if odds_book_a[1] >= odds_book_b[1] else book_b_name

    # Calculate implied probability sum
    implied_sum = (1 / best_outcome_1) + (1 / best_outcome_2)

    # No arbitrage if sum >= 1
    if implied_sum >= 1:
        return None

    # Calculate profit percentage
    profit_pct = ((1 / implied_sum) - 1) * 100

    if profit_pct < min_profit_pct:
        return None

    # Calculate optimal stakes
    stake_1 = total_stake * (1 / best_outcome_1) / implied_sum
    stake_2 = total_stake * (1 / best_outcome_2) / implied_sum

    # Guaranteed return is the same regardless of outcome
    guaranteed_return = stake_1 * best_outcome_1  # = stake_2 * best_outcome_2
    profit = guaranteed_return - total_stake

    return {
        "profit_pct": profit_pct,
        "profit": profit,
        "stakes": [stake_1, stake_2],
        "odds": [best_outcome_1, best_outcome_2],
        "bookmakers": [book_outcome_1, book_outcome_2],
        "total_stake": total_stake,
        "guaranteed_return": guaranteed_return,
        "implied_probability_sum": implied_sum,
    }


def find_arbitrage_multi_book(
    all_odds: dict[str, list[float]],
    total_stake: float = 100.0,
    min_profit_pct: float = 0.0,
) -> dict[str, Any] | None:
    """Find arbitrage across multiple bookmakers.

    Args:
        all_odds: Dict mapping bookmaker name to [odds_1, odds_2].
        total_stake: Total amount to stake.
        min_profit_pct: Minimum profit to report.

    Returns:
        Arbitrage details or None.

    Example:
        >>> odds = {
        ...     "Pinnacle": [2.10, 1.85],
        ...     "Bet365": [2.05, 1.90],
        ...     "DraftKings": [2.15, 1.80],
        ... }
        >>> result = find_arbitrage_multi_book(odds)
    """
    if not all_odds:
        return None

    # Validate all have 2 outcomes
    for book, odds in all_odds.items():
        if len(odds) != 2:
            raise ValueError(f"Bookmaker {book} must have exactly 2 outcomes")

    # Find best odds and their sources
    best_1 = 0.0
    best_1_book = ""
    best_2 = 0.0
    best_2_book = ""

    for book, odds in all_odds.items():
        if odds[0] > best_1:
            best_1 = odds[0]
            best_1_book = book
        if odds[1] > best_2:
            best_2 = odds[1]
            best_2_book = book

    # Use the two-book function with best odds
    return find_arbitrage(
        [best_1, 0.0],  # Best odds for outcome 1
        [0.0, best_2],  # Best odds for outcome 2
        book_a_name=best_1_book,
        book_b_name=best_2_book,
        total_stake=total_stake,
        min_profit_pct=min_profit_pct,
    )


def find_arbitrage_three_way(
    all_odds: dict[str, list[float]],
    total_stake: float = 100.0,
    min_profit_pct: float = 0.0,
) -> dict[str, Any] | None:
    """Find arbitrage in three-outcome markets (e.g., soccer: home/draw/away).

    Args:
        all_odds: Dict mapping bookmaker to [home, draw, away] odds.
        total_stake: Total amount to stake.
        min_profit_pct: Minimum profit to report.

    Returns:
        Arbitrage details or None.

    Example:
        >>> odds = {
        ...     "Pinnacle": [2.50, 3.40, 2.80],
        ...     "Bet365": [2.45, 3.50, 2.85],
        ... }
        >>> result = find_arbitrage_three_way(odds)
    """
    if not all_odds:
        return None

    # Find best odds for each of 3 outcomes
    best_odds = [0.0, 0.0, 0.0]
    best_books = ["", "", ""]

    for book, odds in all_odds.items():
        if len(odds) != 3:
            raise ValueError(f"Bookmaker {book} must have exactly 3 outcomes")

        for i in range(3):
            if odds[i] > best_odds[i]:
                best_odds[i] = odds[i]
                best_books[i] = book

    # Calculate implied probability sum
    implied_sum = sum(1 / o for o in best_odds)

    if implied_sum >= 1:
        return None

    profit_pct = ((1 / implied_sum) - 1) * 100

    if profit_pct < min_profit_pct:
        return None

    # Calculate stakes
    stakes = [
        total_stake * (1 / o) / implied_sum
        for o in best_odds
    ]

    guaranteed_return = stakes[0] * best_odds[0]
    profit = guaranteed_return - total_stake

    return {
        "profit_pct": profit_pct,
        "profit": profit,
        "stakes": stakes,
        "odds": best_odds,
        "bookmakers": best_books,
        "total_stake": total_stake,
        "guaranteed_return": guaranteed_return,
        "implied_probability_sum": implied_sum,
    }


def calculate_vig(odds: list[float]) -> float:
    """Calculate the bookmaker's vig (vigorish) from odds.

    The vig is the bookmaker's margin, calculated as:
        vig = (sum of implied probabilities) - 1

    Args:
        odds: List of decimal odds for all outcomes.

    Returns:
        Vig as a decimal (e.g., 0.05 for 5% vig).

    Example:
        >>> calculate_vig([1.91, 1.91])  # Standard -110/-110
        0.0476  # About 4.76% vig
    """
    implied_sum = sum(1 / o for o in odds)
    return implied_sum - 1


def remove_vig(odds: list[float]) -> list[float]:
    """Calculate fair odds by removing the vig.

    Args:
        odds: List of decimal odds for all outcomes.

    Returns:
        List of fair (no-vig) decimal odds.

    Example:
        >>> remove_vig([1.91, 1.91])
        [2.0, 2.0]  # Fair 50/50 odds
    """
    implied_probs = [1 / o for o in odds]
    total = sum(implied_probs)

    fair_probs = [p / total for p in implied_probs]
    fair_odds = [1 / p for p in fair_probs]

    return fair_odds
