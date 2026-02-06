# Strategy Interface Specification

**Owner:** James
**Version:** 1.0

All strategies evaluated by the backtester must conform to this interface.

---

## Function Signature

```python
def strategy_fn(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
```

---

## Input: `row`

A pandas Series representing one game, with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Game start time |
| game | str | "Home vs Away" |
| home_team | str | Home team name |
| away_team | str | Away team name |
| home_odds | float | Decimal odds for home win |
| away_odds | float | Decimal odds for away win |

**Note:** `home_win` (actual outcome) is NOT passed to the strategy. The strategy must make decisions without knowing the result.

---

## Input: `context` (optional)

A dict provided by the backtester with the current state:

| Key | Type | Description |
|-----|------|-------------|
| initial_bankroll | float | Starting bankroll |
| bankroll | float | Current bankroll |
| trade_count | int | Number of trades executed so far |
| cumulative_pnl | float | Running total profit/loss |

---

## Output: Signal Dict

The strategy must return a dict with these keys:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | Yes | `'BUY_HOME'`, `'BUY_AWAY'`, or `'SKIP'` |
| confidence | float | Yes | Confidence level between 0 and 1 |
| size | float | Yes | Bet size in dollars |
| reason | str | No | Human-readable explanation |

**Rules:**
- If `action` is `'SKIP'`, the game is ignored (no trade).
- `size` is capped at the current bankroll by the backtester.
- If `size` is 0 or negative, the game is skipped.

---

## Example Implementation

```python
def always_bet_home(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Always bet $100 on the home team."""
    return {
        "action": "BUY_HOME",
        "confidence": 0.5,
        "size": 100.0,
        "reason": "Always bet home (test strategy)",
    }
```

```python
def favourite_strategy(
    row: pd.Series,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bet on the favourite (lower odds = higher implied probability)."""
    if row["home_odds"] < row["away_odds"]:
        action = "BUY_HOME"
        odds = row["home_odds"]
    else:
        action = "BUY_AWAY"
        odds = row["away_odds"]

    return {
        "action": action,
        "confidence": 1.0 / odds,
        "size": 100.0,
        "reason": f"Backing favourite at {odds:.2f}",
    }
```

---

## Backtester Output Format

When the backtester runs a strategy, it produces a DataFrame with exactly these 9 columns:

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | When trade happened |
| game | str | "Home vs Away" |
| action | str | 'BUY_HOME' or 'BUY_AWAY' |
| bet_size | float | Dollars bet |
| odds | float | Decimal odds used |
| outcome | str | 'WIN' or 'LOSS' |
| pnl | float | Profit/loss for this trade |
| cumulative_pnl | float | Running total P&L |
| bankroll | float | Current bankroll after trade |

---

## Changelog

- **v1.0 (Feb 6, 2026):** Initial version — strategy interface and backtester output format.
