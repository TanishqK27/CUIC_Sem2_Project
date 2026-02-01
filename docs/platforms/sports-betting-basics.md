# Sports Betting Basics

A comprehensive guide to sports betting fundamentals, odds formats, and quantitative concepts essential for algorithmic betting strategies.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Odds Formats](#odds-formats)
3. [Types of Bets](#types-of-bets)
4. [Key Concepts](#key-concepts)
5. [Expected Value](#expected-value)
6. [Kelly Criterion](#kelly-criterion)
7. [Arbitrage](#arbitrage)
8. [Data Sources](#data-sources)
9. [Python Examples](#python-examples)

---

## Introduction

Sports betting is a multi-billion dollar industry that offers opportunities for quantitative analysis. Unlike casino games with fixed house edges, sports betting lines are set by human oddsmakers and can contain inefficiencies that systematic approaches can exploit.

### Why Sports Betting for Quant Research?

| Factor | Advantage |
|--------|-----------|
| **Market Inefficiency** | Lines are set by humans, not perfect models |
| **Data Availability** | Rich historical data for backtesting |
| **Frequent Events** | Thousands of games per week globally |
| **Diverse Markets** | Moneylines, spreads, totals, props |
| **API Access** | Multiple data providers with real-time odds |

---

## Odds Formats

Three primary formats are used globally. Understanding conversion between them is essential.

### American Odds (Moneyline)

Used primarily in the United States.

```
Positive (+150): Profit on a $100 bet
  - Bet $100, win $150 profit (total return $250)

Negative (-150): Amount to bet to win $100
  - Bet $150, win $100 profit (total return $250)
```

### Decimal Odds

Used in Europe, Australia, and most online platforms.

```
Decimal odds = Total return per $1 wagered

2.50 decimal odds:
  - Bet $100, total return $250 (profit $150)

1.67 decimal odds:
  - Bet $100, total return $167 (profit $67)
```

### Fractional Odds

Traditional format used in UK horse racing.

```
3/2 (three-to-two):
  - For every $2 wagered, win $3 profit
  - Bet $100, win $150 profit

2/3 (two-to-three):
  - For every $3 wagered, win $2 profit
  - Bet $100, win $66.67 profit
```

### Conversion Formulas

```python
def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal.

    Args:
        american: American odds (e.g., +150 or -150)

    Returns:
        Decimal odds

    Examples:
        >>> american_to_decimal(150)
        2.5
        >>> american_to_decimal(-150)
        1.6667
    """
    if american > 0:
        return (american / 100) + 1
    else:
        return (100 / abs(american)) + 1


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American.

    Args:
        decimal: Decimal odds (e.g., 2.5)

    Returns:
        American odds

    Examples:
        >>> decimal_to_american(2.5)
        150
        >>> decimal_to_american(1.5)
        -200
    """
    if decimal >= 2.0:
        return int((decimal - 1) * 100)
    else:
        return int(-100 / (decimal - 1))


def decimal_to_implied_prob(decimal: float) -> float:
    """Convert decimal odds to implied probability.

    Args:
        decimal: Decimal odds

    Returns:
        Implied probability (0-1)

    Example:
        >>> decimal_to_implied_prob(2.0)
        0.5
    """
    return 1 / decimal


def implied_prob_to_decimal(prob: float) -> float:
    """Convert implied probability to decimal odds.

    Args:
        prob: Probability (0-1)

    Returns:
        Decimal odds

    Example:
        >>> implied_prob_to_decimal(0.6)
        1.667
    """
    return 1 / prob
```

---

## Types of Bets

### Moneyline

Bet on which team wins outright.

```
Lakers vs Celtics
Lakers: -150 (favorite)
Celtics: +130 (underdog)

Implied probabilities:
  Lakers: 60% (includes vig)
  Celtics: 43% (includes vig)
  Total: 103% (3% is the vig/juice)
```

### Point Spread

Bet on margin of victory.

```
Lakers -5.5 (-110)
Celtics +5.5 (-110)

Lakers must win by 6+ points to cover
Celtics must lose by 5 or fewer (or win) to cover
```

### Totals (Over/Under)

Bet on combined score.

```
Total: 215.5
Over 215.5 (-110)
Under 215.5 (-110)

If final score is Lakers 112, Celtics 105 (Total: 217)
  - Over wins
```

### Parlays

Combine multiple bets; all must win.

```
Parlay: Lakers ML + Over 215.5

Lakers ML decimal: 1.67
Over 215.5 decimal: 1.91

Parlay odds: 1.67 × 1.91 = 3.19
$100 bet returns $319 if both hit
```

### Props (Proposition Bets)

Bet on specific occurrences.

```
LeBron James Points: Over/Under 27.5
Lakers to score first: Yes/No
Total 3-pointers made: Over/Under 24.5
```

---

## Key Concepts

### Vigorish (Vig/Juice)

The bookmaker's commission built into the odds.

```python
def calculate_vig(odds_a: float, odds_b: float) -> float:
    """Calculate the bookmaker's vig from decimal odds.

    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B

    Returns:
        Vig as a percentage

    Example:
        >>> calculate_vig(1.91, 1.91)  # Standard -110/-110
        0.0476  # 4.76% vig
    """
    prob_a = 1 / odds_a
    prob_b = 1 / odds_b
    total_prob = prob_a + prob_b
    return total_prob - 1


def remove_vig(odds_a: float, odds_b: float) -> tuple[float, float]:
    """Calculate fair odds by removing the vig.

    Args:
        odds_a: Decimal odds for outcome A
        odds_b: Decimal odds for outcome B

    Returns:
        Tuple of fair decimal odds (odds_a, odds_b)

    Example:
        >>> remove_vig(1.91, 1.91)
        (2.0, 2.0)  # Fair 50/50 odds
    """
    prob_a = 1 / odds_a
    prob_b = 1 / odds_b
    total = prob_a + prob_b

    fair_prob_a = prob_a / total
    fair_prob_b = prob_b / total

    return (1 / fair_prob_a, 1 / fair_prob_b)
```

### Line Movement

Odds change based on betting action and new information.

```
Opening line: Lakers -3.5
Current line: Lakers -5.5

The line moved 2 points toward Lakers, indicating:
  - Sharp money on Lakers
  - Public betting Lakers
  - New information favoring Lakers
```

### Closing Line Value (CLV)

Beating the closing line is the gold standard for measuring edge.

```python
def calculate_clv(
    bet_odds: float,
    closing_odds: float,
) -> float:
    """Calculate Closing Line Value.

    CLV measures if you got better odds than the market's final price.

    Args:
        bet_odds: Decimal odds when you placed bet
        closing_odds: Decimal odds at game start

    Returns:
        CLV as a percentage (positive = good)

    Example:
        >>> calculate_clv(2.10, 1.95)  # Bet at 2.10, closed at 1.95
        0.0714  # 7.14% CLV (excellent)
    """
    bet_prob = 1 / bet_odds
    closing_prob = 1 / closing_odds
    return closing_prob - bet_prob
```

---

## Expected Value

Expected Value (EV) is the average profit per bet over the long run.

### Formula

```
EV = (Probability of Win × Profit if Win) - (Probability of Loss × Loss if Loss)

Or equivalently:
EV = (p × (odds - 1)) - ((1 - p) × 1)

Where:
  p = true probability of winning
  odds = decimal odds
```

### Python Implementation

```python
def calculate_ev(
    true_probability: float,
    decimal_odds: float,
    stake: float = 1.0,
) -> float:
    """Calculate expected value of a bet.

    Args:
        true_probability: Your estimated win probability (0-1)
        decimal_odds: Decimal odds offered
        stake: Amount wagered

    Returns:
        Expected value (profit per bet)

    Example:
        >>> calculate_ev(0.55, 2.0, 100)
        10.0  # +$10 EV per $100 bet
    """
    profit_if_win = stake * (decimal_odds - 1)
    loss_if_lose = stake

    ev = (true_probability * profit_if_win) - ((1 - true_probability) * loss_if_lose)
    return ev


def calculate_edge(true_probability: float, decimal_odds: float) -> float:
    """Calculate betting edge as a percentage.

    Args:
        true_probability: Your estimated win probability
        decimal_odds: Decimal odds offered

    Returns:
        Edge as a percentage

    Example:
        >>> calculate_edge(0.55, 2.0)
        0.10  # 10% edge
    """
    implied_prob = 1 / decimal_odds
    return true_probability - implied_prob


def is_positive_ev(true_probability: float, decimal_odds: float) -> bool:
    """Check if a bet has positive expected value.

    Args:
        true_probability: Your estimated win probability
        decimal_odds: Decimal odds offered

    Returns:
        True if bet has positive EV

    Example:
        >>> is_positive_ev(0.55, 2.0)
        True  # +EV bet
        >>> is_positive_ev(0.45, 2.0)
        False  # -EV bet
    """
    break_even_prob = 1 / decimal_odds
    return true_probability > break_even_prob
```

---

## Kelly Criterion

The Kelly Criterion determines optimal bet sizing to maximize long-term growth.

### Formula

```
Kelly % = (bp - q) / b

Where:
  b = decimal odds - 1 (net odds)
  p = probability of winning
  q = probability of losing (1 - p)
```

### Python Implementation

```python
def kelly_criterion(
    win_probability: float,
    decimal_odds: float,
    kelly_fraction: float = 1.0,
) -> float:
    """Calculate optimal bet size using Kelly Criterion.

    Args:
        win_probability: Estimated probability of winning (0-1)
        decimal_odds: Decimal odds offered
        kelly_fraction: Fraction of Kelly to use (0.25-0.5 recommended)

    Returns:
        Fraction of bankroll to bet (0-1)

    Example:
        >>> kelly_criterion(0.55, 2.0)
        0.10  # Bet 10% of bankroll
        >>> kelly_criterion(0.55, 2.0, kelly_fraction=0.5)
        0.05  # Half Kelly: bet 5% of bankroll
    """
    if win_probability <= 0 or win_probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")

    b = decimal_odds - 1  # Net odds
    p = win_probability
    q = 1 - p

    kelly = (b * p - q) / b

    # Never bet negative (no edge) or more than 100%
    kelly = max(0, min(1, kelly))

    return kelly * kelly_fraction


def kelly_with_multiple_outcomes(
    probabilities: list[float],
    odds: list[float],
    kelly_fraction: float = 1.0,
) -> list[float]:
    """Calculate Kelly fractions for multiple simultaneous bets.

    For multiple correlated bets, this is an approximation.
    True multi-outcome Kelly requires optimization.

    Args:
        probabilities: List of win probabilities
        odds: List of decimal odds
        kelly_fraction: Fraction of Kelly to use

    Returns:
        List of fractions to bet on each outcome
    """
    fractions = []
    for p, o in zip(probabilities, odds):
        k = kelly_criterion(p, o, kelly_fraction)
        fractions.append(k)

    # Scale down if total exceeds 1
    total = sum(fractions)
    if total > 1:
        fractions = [f / total for f in fractions]

    return fractions
```

### Fractional Kelly

Full Kelly is aggressive and can lead to large drawdowns. Most professionals use fractional Kelly:

| Fraction | Risk Level | Use Case |
|----------|------------|----------|
| Full Kelly (1.0) | Very High | Theoretical maximum growth |
| Half Kelly (0.5) | Moderate | Most common professional choice |
| Quarter Kelly (0.25) | Conservative | Recommended for beginners |
| Tenth Kelly (0.1) | Very Low | Highly uncertain edges |

---

## Arbitrage

Arbitrage (arbing) exploits price differences between bookmakers for guaranteed profit.

### Example

```
Book A: Lakers -150 (1.67 decimal)
Book B: Celtics +160 (2.60 decimal)

Implied probabilities:
  Lakers: 1/1.67 = 59.9%
  Celtics: 1/2.60 = 38.5%
  Total: 98.4%

Since total < 100%, arbitrage exists!
```

### Python Implementation

```python
def find_arbitrage(
    odds_a: list[float],
    odds_b: list[float],
) -> dict | None:
    """Find arbitrage opportunity between two bookmakers.

    Args:
        odds_a: [team1_odds, team2_odds] from bookmaker A
        odds_b: [team1_odds, team2_odds] from bookmaker B

    Returns:
        Arbitrage details or None if no opportunity

    Example:
        >>> find_arbitrage([1.67, 2.40], [1.80, 2.60])
        {'profit_pct': 1.6, 'stakes': [60.0, 40.0], ...}
    """
    # Find best odds for each outcome across books
    best_team1 = max(odds_a[0], odds_b[0])
    best_team2 = max(odds_a[1], odds_b[1])

    # Calculate implied probability sum
    implied_sum = (1 / best_team1) + (1 / best_team2)

    if implied_sum >= 1:
        return None  # No arbitrage

    # Calculate optimal stakes (assuming $100 total)
    total_stake = 100
    stake_team1 = total_stake * (1 / best_team1) / implied_sum
    stake_team2 = total_stake * (1 / best_team2) / implied_sum

    # Calculate guaranteed profit
    payout = stake_team1 * best_team1  # Same as stake_team2 * best_team2
    profit = payout - total_stake
    profit_pct = (profit / total_stake) * 100

    return {
        "profit_pct": profit_pct,
        "stakes": [stake_team1, stake_team2],
        "best_odds": [best_team1, best_team2],
        "guaranteed_payout": payout,
        "profit": profit,
    }


def calculate_arbitrage_stakes(
    odds: list[float],
    total_stake: float = 100.0,
) -> list[float]:
    """Calculate stakes for an arbitrage opportunity.

    Args:
        odds: Best decimal odds for each outcome
        total_stake: Total amount to stake

    Returns:
        List of stakes for each outcome

    Example:
        >>> calculate_arbitrage_stakes([2.10, 2.05], 1000)
        [494.0, 506.0]  # Stakes that guarantee same payout
    """
    implied_probs = [1 / o for o in odds]
    total_implied = sum(implied_probs)

    stakes = [(p / total_implied) * total_stake for p in implied_probs]
    return stakes
```

### Arbitrage Considerations

| Factor | Description |
|--------|-------------|
| **Speed** | Opportunities disappear quickly (seconds to minutes) |
| **Limits** | Bookmakers limit winning accounts |
| **Errors** | Palp (palpable errors) may be voided |
| **Correlations** | Multi-leg arbs have execution risk |
| **Margins** | Typical profit: 1-3% per opportunity |

---

## Data Sources

### The Odds API

Primary source for odds data across multiple bookmakers.

```python
import requests

def get_odds_from_api(
    api_key: str,
    sport: str = "basketball_nba",
    markets: str = "h2h,spreads,totals",
) -> dict:
    """Fetch odds from The Odds API.

    Args:
        api_key: Your API key
        sport: Sport key (e.g., "basketball_nba", "soccer_epl")
        markets: Comma-separated market types

    Returns:
        API response with odds data
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"

    params = {
        "apiKey": api_key,
        "regions": "us,uk,eu",
        "markets": markets,
        "oddsFormat": "decimal",
    }

    response = requests.get(url, params=params)
    return response.json()
```

### Other Data Sources

| Source | Data Type | Cost |
|--------|-----------|------|
| [The Odds API](https://the-odds-api.com/) | Real-time odds | Free tier + paid |
| [Sportradar](https://sportradar.com/) | Historical + live | Enterprise |
| [ESPN API](http://site.api.espn.com/apis/site/v2/sports/) | Scores, schedules | Free |
| [Basketball Reference](https://www.basketball-reference.com/) | Historical stats | Free |
| [FBref](https://fbref.com/) | Soccer statistics | Free |

---

## Python Examples

### Complete Betting Analysis

```python
"""Complete sports betting analysis example."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BettingOpportunity:
    """Represents a betting opportunity with analysis."""

    event: str
    selection: str
    decimal_odds: float
    implied_prob: float
    model_prob: float
    edge: float
    ev_per_unit: float
    kelly_fraction: float
    recommended_stake: float
    is_positive_ev: bool


def analyze_opportunity(
    event: str,
    selection: str,
    decimal_odds: float,
    model_probability: float,
    bankroll: float = 1000.0,
    kelly_fraction: float = 0.25,
) -> BettingOpportunity:
    """Perform complete analysis of a betting opportunity.

    Args:
        event: Event name
        selection: What you're betting on
        decimal_odds: Decimal odds offered
        model_probability: Your model's win probability
        bankroll: Current bankroll
        kelly_fraction: Kelly fraction to use

    Returns:
        Complete analysis of the opportunity
    """
    implied_prob = 1 / decimal_odds
    edge = model_probability - implied_prob

    # Expected value per $1 bet
    ev_per_unit = (model_probability * (decimal_odds - 1)) - (1 - model_probability)

    # Kelly calculation
    if edge > 0:
        b = decimal_odds - 1
        kelly = (b * model_probability - (1 - model_probability)) / b
        kelly = kelly * kelly_fraction
    else:
        kelly = 0

    recommended_stake = bankroll * kelly

    return BettingOpportunity(
        event=event,
        selection=selection,
        decimal_odds=decimal_odds,
        implied_prob=implied_prob,
        model_prob=model_probability,
        edge=edge,
        ev_per_unit=ev_per_unit,
        kelly_fraction=kelly,
        recommended_stake=recommended_stake,
        is_positive_ev=edge > 0,
    )


# Example usage
if __name__ == "__main__":
    opp = analyze_opportunity(
        event="Lakers vs Celtics",
        selection="Lakers ML",
        decimal_odds=1.91,  # -110 American
        model_probability=0.58,  # Your model says 58%
        bankroll=10000,
        kelly_fraction=0.25,
    )

    print(f"Event: {opp.event}")
    print(f"Selection: {opp.selection}")
    print(f"Odds: {opp.decimal_odds:.2f} ({int((opp.decimal_odds - 1) * 100):+d})")
    print(f"Implied Prob: {opp.implied_prob:.1%}")
    print(f"Model Prob: {opp.model_prob:.1%}")
    print(f"Edge: {opp.edge:.1%}")
    print(f"EV per unit: ${opp.ev_per_unit:.3f}")
    print(f"Kelly %: {opp.kelly_fraction:.1%}")
    print(f"Recommended Stake: ${opp.recommended_stake:.2f}")
    print(f"Positive EV: {opp.is_positive_ev}")
```

---

## Resources

### Books

- *Trading Bases* by Joe Peta
- *The Signal and the Noise* by Nate Silver
- *Fortune's Formula* by William Poundstone
- *Weighing the Odds in Sports Betting* by King Yao

### Online Resources

- [Pinnacle Sports Betting Resources](https://www.pinnacle.com/en/betting-resources)
- [BetLabs Sports Analytics](https://www.betlabssports.com/)
- [Sports Insights](https://www.sportsinsights.com/)

### Academic Papers

- "Prediction Markets: What Works and What Doesn't"
- "The Efficient Market Hypothesis and Sports Betting"
- "Kelly Criterion in Practice: A Guide for Sports Bettors"

---

## Next Steps

1. Review [The Odds API setup](../setup/api-keys.md)
2. Explore `src/cuic_quant/data/odds_api.py` client
3. Check out `src/cuic_quant/strategies/kelly_criterion.py`
4. Start with paper trading before risking real money
