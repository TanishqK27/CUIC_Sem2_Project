# Task: Strategy Interface Specification

**Owner:** James
**Deadline:** Feb 12 (Week 1)
**Priority:** High — Models team needs this to build compatible strategies

---

## What You're Building

A clear specification document that defines exactly how strategy functions must be written to work with the backtester.

---

## Why This Matters

Mya, Dietrich, and others will build models that output trading signals. If everyone uses a different format, nothing integrates. This spec is the contract.

---

## Exactly What You Must Deliver

### 1. Specification Document

Create `docs/reference/strategy-interface.md` with:

```markdown
# Strategy Interface Specification

## Overview

All strategies must follow this interface to work with the backtester.

## Function Signature

```python
def my_strategy(row: pd.Series, context: dict = None) -> dict:
    """
    Generate trading signal for a single game.

    Parameters
    ----------
    row : pd.Series
        Single row from the backtest data with columns:
        - timestamp: datetime
        - game: str (e.g., "Lakers @ Celtics")
        - pm_home_prob: float (Polymarket probability, 0-1)
        - sb_home_prob: float (Sportsbook probability, 0-1)
        - gap: float (sb_home_prob - pm_home_prob)
        - [additional columns as available]

    context : dict, optional
        Persistent state across calls. Use for:
        - Tracking open positions
        - Rolling calculations
        - Any state that spans multiple games

    Returns
    -------
    dict with keys:
        - action: str, one of ['BUY_HOME', 'BUY_AWAY', 'SKIP']
        - confidence: float, 0.0 to 1.0 (how confident in the signal)
        - size: float, recommended bet size in dollars
        - reason: str, optional explanation for logging
    """
    pass
```

## Example Strategies

### Simple Gap Strategy
```python
def gap_strategy(row, context=None):
    if row['gap'] > 0.05:
        return {
            'action': 'BUY_HOME',
            'confidence': min(row['gap'] * 10, 1.0),
            'size': 100,
            'reason': f"Gap of {row['gap']:.1%} exceeds threshold"
        }
    return {'action': 'SKIP', 'confidence': 0, 'size': 0, 'reason': 'Gap too small'}
```

### Model-Based Strategy
```python
def model_strategy(row, context=None):
    # Assume model is loaded in context
    model = context.get('model')
    features = [row['gap'], row['pm_home_prob'], ...]
    prob = model.predict_proba([features])[0][1]

    if prob > 0.6:
        return {
            'action': 'BUY_HOME',
            'confidence': prob,
            'size': calculate_kelly(prob, row['sb_home_odds']),
            'reason': f"Model predicts {prob:.1%} home win"
        }
    return {'action': 'SKIP', 'confidence': 0, 'size': 0}
```

## Required Columns

Strategies can expect these columns in `row`:
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | When this snapshot was taken |
| game | str | Game identifier |
| pm_home_prob | float | Polymarket home win probability |
| sb_home_prob | float | Sportsbook home win probability |
| gap | float | sb_home_prob - pm_home_prob |

## Testing Your Strategy

```python
# Validate your strategy works
from backtester import validate_strategy

validate_strategy(my_strategy)  # Raises error if interface wrong
```
```

---

## Done Checklist

- [ ] Spec document created at `docs/reference/strategy-interface.md`
- [ ] Function signature clearly defined
- [ ] Input (row) columns documented
- [ ] Output (dict) keys documented
- [ ] At least 2 example strategies included
- [ ] Shared with Models team (Mya, Dietrich)

---

## What You Will Present (Thursday Feb 12)

**Walk through the spec:**
1. Show the function signature (30 sec)
2. Show one example strategy (30 sec)
3. Confirm Mya and Dietrich understand the interface (30 sec)

**Duration:** 2 minutes max

---

## Who To Ask If Stuck

1. Mya — what outputs do her models produce?
2. Dietrich — what does his Markov model output?
3. Tan — final approval on interface
