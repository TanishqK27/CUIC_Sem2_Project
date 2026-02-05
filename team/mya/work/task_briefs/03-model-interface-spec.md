# Task: Model Interface Specification

**Owner:** Mya
**Deadline:** Feb 12 (Week 1)
**Priority:** High — Isameel needs this to test models

---

## What You're Building

A specification document that defines exactly how ML models must be structured to work with the backtester. This ensures everyone's models are compatible.

---

## Why This Matters

Dietrich builds a Markov model, you build logistic regression, Isameel builds XGBoost — they all need to plug into the same backtester. This spec defines the contract.

---

## Exactly What You Must Deliver

### 1. Specification Document

Create `docs/reference/model-interface.md`:

```markdown
# Model Interface Specification

## Overview

All ML models in CUIC Quant must follow this interface to work with the backtester and strategy framework.

## Base Class

All models should inherit from or implement this interface:

```python
from abc import ABC, abstractmethod
import pandas as pd

class BaseModel(ABC):
    """Base class for all prediction models."""

    @abstractmethod
    def predict_proba(self, row: pd.Series) -> float:
        """
        Predict probability of home team winning.

        Args:
            row: Single game data with features

        Returns:
            Probability between 0 and 1
        """
        pass

    @abstractmethod
    def to_strategy(self, **kwargs):
        """
        Convert model to backtester-compatible strategy function.

        Returns:
            Function with signature: (row, context) -> dict
        """
        pass

    def save(self, path: str) -> None:
        """Save model to disk."""
        pass

    @classmethod
    def load(cls, path: str) -> 'BaseModel':
        """Load model from disk."""
        pass
```

## predict_proba() Specification

### Input: row (pd.Series)

The row passed to `predict_proba` contains one game's data:

| Column | Type | Description |
|--------|------|-------------|
| game_date | datetime | When the game is played |
| home_team | str | Home team name |
| away_team | str | Away team name |
| pm_home_prob | float | Polymarket probability (0-1) |
| sb_home_prob | float | Sportsbook probability (0-1) |
| gap | float | sb_home_prob - pm_home_prob |
| [additional features] | varies | Team stats, etc. |

### Output: float

Return value must be:
- A single float
- Between 0.0 and 1.0 (inclusive)
- Represents P(home team wins)

### Example

```python
def predict_proba(self, row: pd.Series) -> float:
    features = [row['pm_home_prob'], row['gap']]
    return self.model.predict_proba([features])[0][1]
```

## to_strategy() Specification

### Purpose

Convert the model into a function that works with James's backtester.

### Output

Returns a function with this signature:

```python
def strategy(row: pd.Series, context: dict = None) -> dict:
    """
    Returns:
        dict with keys:
        - action: 'BUY_HOME', 'BUY_AWAY', or 'SKIP'
        - confidence: float 0-1
        - size: float (bet size in dollars)
        - reason: str (optional explanation)
    """
    pass
```

### Example Implementation

```python
def to_strategy(self, threshold: float = 0.55, bet_size: float = 100):
    """Convert model to strategy with configurable threshold."""

    def strategy(row, context=None):
        prob = self.predict_proba(row)

        if prob > threshold:
            return {
                'action': 'BUY_HOME',
                'confidence': prob,
                'size': bet_size,
                'reason': f'Model: {prob:.1%} home win'
            }
        elif prob < (1 - threshold):
            return {
                'action': 'BUY_AWAY',
                'confidence': 1 - prob,
                'size': bet_size,
                'reason': f'Model: {1-prob:.1%} away win'
            }
        return {
            'action': 'SKIP',
            'confidence': 0,
            'size': 0,
            'reason': f'Prob {prob:.1%} below threshold'
        }

    return strategy
```

## Model File Structure

Models should be saved with their feature configuration:

```
outputs/
├── logistic_baseline.pkl      # Trained model
├── logistic_baseline_features.json  # Feature list
└── logistic_baseline_config.json    # Hyperparameters
```

### Feature Config Example

```json
{
    "features": ["pm_home_prob", "sb_home_prob", "gap"],
    "trained_on": "2025-01-01 to 2026-01-31",
    "accuracy": 0.58,
    "auc_roc": 0.62
}
```

## Validation Function

Use this to verify your model follows the spec:

```python
def validate_model(model: BaseModel, sample_row: pd.Series) -> bool:
    """
    Validate that a model follows the interface spec.

    Returns True if valid, raises ValueError if not.
    """
    # Test predict_proba
    prob = model.predict_proba(sample_row)
    if not isinstance(prob, (int, float)):
        raise ValueError(f"predict_proba must return float, got {type(prob)}")
    if not 0 <= prob <= 1:
        raise ValueError(f"predict_proba must return 0-1, got {prob}")

    # Test to_strategy
    strategy = model.to_strategy()
    if not callable(strategy):
        raise ValueError("to_strategy must return callable")

    result = strategy(sample_row)
    required_keys = {'action', 'confidence', 'size'}
    if not required_keys.issubset(result.keys()):
        raise ValueError(f"Strategy must return {required_keys}, got {result.keys()}")

    if result['action'] not in ['BUY_HOME', 'BUY_AWAY', 'SKIP']:
        raise ValueError(f"Invalid action: {result['action']}")

    return True
```

## Existing Models

| Model | Location | Status |
|-------|----------|--------|
| LogisticBaseline | `src/cuic_quant/models/logistic_baseline.py` | Mya - Week 2 |
| MarkovGap | `src/cuic_quant/models/markov_gap.py` | Dietrich - Week 2 |
| XGBoostNBA | `src/cuic_quant/models/xgboost_nba.py` | Isameel - Week 3 |

## Testing Your Model

```python
# 1. Create sample data
sample_row = pd.Series({
    'game_date': '2026-01-15',
    'home_team': 'Lakers',
    'away_team': 'Celtics',
    'pm_home_prob': 0.45,
    'sb_home_prob': 0.50,
    'gap': 0.05
})

# 2. Load your model
model = LogisticBaseline.load('outputs/logistic_baseline.pkl')

# 3. Validate
validate_model(model, sample_row)

# 4. Use in backtest
strategy = model.to_strategy(threshold=0.55)
signal = strategy(sample_row)
print(signal)
# {'action': 'SKIP', 'confidence': 0, 'size': 0, 'reason': '...'}
```
```

### 2. Base Class Implementation

Create `src/cuic_quant/models/__init__.py`:

```python
"""Machine learning models for prediction."""

from abc import ABC, abstractmethod
import pandas as pd

class BaseModel(ABC):
    """Base class for all prediction models."""

    @abstractmethod
    def predict_proba(self, row: pd.Series) -> float:
        """Predict probability of home team winning."""
        pass

    @abstractmethod
    def to_strategy(self, **kwargs):
        """Convert model to strategy function."""
        pass


def validate_model(model: BaseModel, sample_row: pd.Series) -> bool:
    """Validate model follows the interface spec."""
    # Test predict_proba
    prob = model.predict_proba(sample_row)
    if not isinstance(prob, (int, float)):
        raise ValueError(f"predict_proba must return float, got {type(prob)}")
    if not 0 <= prob <= 1:
        raise ValueError(f"predict_proba must return 0-1, got {prob}")

    # Test to_strategy
    strategy = model.to_strategy()
    if not callable(strategy):
        raise ValueError("to_strategy must return callable")

    result = strategy(sample_row)
    required_keys = {'action', 'confidence', 'size'}
    if not required_keys.issubset(result.keys()):
        raise ValueError(f"Strategy must return {required_keys}")

    if result['action'] not in ['BUY_HOME', 'BUY_AWAY', 'SKIP']:
        raise ValueError(f"Invalid action: {result['action']}")

    return True


__all__ = ['BaseModel', 'validate_model']
```

---

## Done Checklist

- [ ] Spec document created at `docs/reference/model-interface.md`
- [ ] `predict_proba()` interface documented with examples
- [ ] `to_strategy()` interface documented with examples
- [ ] Validation function included
- [ ] Base class created at `src/cuic_quant/models/__init__.py`
- [ ] Shared with Dietrich and Isameel

---

## What You Will Present (Thursday Feb 12)

**Walk through the spec:**
1. Show the `predict_proba` interface (30 sec)
2. Show the `to_strategy` interface (30 sec)
3. Run the validation function on a sample model (30 sec)
4. Confirm Dietrich and Isameel understand it

**Duration:** 2 minutes max

---

## Who To Ask If Stuck

1. James — how his strategy interface works (coordinate!)
2. Dietrich — what his Markov model needs
3. Tan — final approval on interface
