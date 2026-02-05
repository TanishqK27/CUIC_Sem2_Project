# Task: Logistic Regression Baseline Model

**Owner:** Mya
**Deadline:** Feb 19 (Week 2) — research in Week 1, build in Week 2
**Priority:** High — first real predictive model

---

## What You're Building

A logistic regression model that predicts NBA game outcomes using basic features. This is our baseline — every future model must beat this.

---

## Why This Matters

You never start with a complex model. You start simple, get it working, then improve. Logistic regression is fast, interpretable, and often surprisingly good. If we can't beat a logistic regression baseline, our fancy models are overfitting.

---

## Exactly What You Must Deliver

### 1. Baseline Model Notebook

Create `research/notebooks/models/logistic_baseline.ipynb`:

```python
# Cell 1: Introduction
"""
# Logistic Regression Baseline for NBA Prediction

**Goal:** Predict home team win probability using basic features.

**Why logistic regression?**
- Fast to train
- Easy to interpret (coefficient = feature importance)
- Resistant to overfitting
- Sets baseline for comparison
"""

# Cell 2: Imports
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import matplotlib.pyplot as plt

# Cell 3: Load Data
"""
## Load NBA Game Data

Get historical games with outcomes from Railway DB.
"""

# Connect to Railway and load data
# (Use the same connection pattern as other notebooks)

# Expected columns after loading:
# - game_date
# - home_team
# - away_team
# - home_win (1 or 0) — TARGET
# - pm_home_prob (Polymarket probability)
# - sb_home_prob (Sportsbook implied probability)
# - gap (sb_home_prob - pm_home_prob)

# Cell 4: Feature Engineering
"""
## Basic Features

Start simple. We can add more features later.
"""

features = [
    'pm_home_prob',      # Polymarket's view
    'sb_home_prob',      # Sportsbook's view
    'gap',               # Disagreement between markets
]

X = df[features]
y = df['home_win']

print(f"Features shape: {X.shape}")
print(f"Target distribution: {y.value_counts(normalize=True)}")

# Cell 5: Train/Test Split
"""
## Split Data

IMPORTANT: Use time-based split, not random.
Training on future data to predict past = cheating.
"""

# Sort by date
df = df.sort_values('game_date')

# Use first 80% for training, last 20% for testing
split_idx = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

print(f"Training: {len(X_train)} games")
print(f"Testing: {len(X_test)} games")

# Cell 6: Train Model
"""
## Train Logistic Regression
"""

model = LogisticRegression(random_state=42)
model.fit(X_train, y_train)

# Show coefficients
for feature, coef in zip(features, model.coef_[0]):
    print(f"{feature}: {coef:.3f}")

# Cell 7: Evaluate
"""
## Model Performance
"""

# Predictions
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

# Metrics
print(f"Accuracy: {accuracy_score(y_test, y_pred):.1%}")
print(f"AUC-ROC: {roc_auc_score(y_test, y_prob):.3f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Cell 8: Compare to Baseline
"""
## Comparison to Market Odds

Is our model better than just using Polymarket/Sportsbook probability?
"""

# Polymarket as predictor
pm_pred = (df.loc[X_test.index, 'pm_home_prob'] > 0.5).astype(int)
pm_acc = accuracy_score(y_test, pm_pred)

# Sportsbook as predictor
sb_pred = (df.loc[X_test.index, 'sb_home_prob'] > 0.5).astype(int)
sb_acc = accuracy_score(y_test, sb_pred)

print(f"Our Model Accuracy: {accuracy_score(y_test, y_pred):.1%}")
print(f"Polymarket Accuracy: {pm_acc:.1%}")
print(f"Sportsbook Accuracy: {sb_acc:.1%}")

# Cell 9: Save Model
"""
## Save for Backtesting
"""

import joblib
joblib.dump(model, 'outputs/logistic_baseline.pkl')

# Also save feature list
with open('outputs/logistic_features.txt', 'w') as f:
    f.write('\n'.join(features))

# Cell 10: Conclusion
"""
## Results Summary

| Metric | Value |
|--------|-------|
| Training samples | X |
| Test samples | X |
| Accuracy | X% |
| AUC-ROC | X |
| Beat Polymarket? | Yes/No |
| Beat Sportsbook? | Yes/No |

**Next steps:**
1. Add more features (team stats, player data)
2. Try XGBoost for non-linear relationships
3. Test on more recent data
"""
```

### 2. Model Function for Backtester

Create `src/cuic_quant/models/logistic_baseline.py`:

```python
"""Logistic regression baseline model for NBA prediction."""

import joblib
import pandas as pd
from pathlib import Path

class LogisticBaseline:
    """Simple logistic regression model for game prediction."""

    def __init__(self, model_path: str = None):
        """Load trained model from disk."""
        if model_path:
            self.model = joblib.load(model_path)
        else:
            self.model = None
        self.features = ['pm_home_prob', 'sb_home_prob', 'gap']

    def predict_proba(self, row: pd.Series) -> float:
        """
        Predict home win probability.

        Args:
            row: Series with pm_home_prob, sb_home_prob, gap

        Returns:
            Probability of home team winning (0-1)
        """
        if self.model is None:
            raise ValueError("Model not loaded")

        X = [[row[f] for f in self.features]]
        return self.model.predict_proba(X)[0][1]

    def to_strategy(self, threshold: float = 0.55):
        """
        Convert model to strategy function for backtester.

        Args:
            threshold: Minimum probability to trigger bet

        Returns:
            Strategy function compatible with backtester
        """
        def strategy(row, context=None):
            prob = self.predict_proba(row)

            if prob > threshold:
                return {
                    'action': 'BUY_HOME',
                    'confidence': prob,
                    'size': 100,
                    'reason': f'Model predicts {prob:.1%} home win'
                }
            elif prob < (1 - threshold):
                return {
                    'action': 'BUY_AWAY',
                    'confidence': 1 - prob,
                    'size': 100,
                    'reason': f'Model predicts {1-prob:.1%} away win'
                }
            return {'action': 'SKIP', 'confidence': 0, 'size': 0, 'reason': 'Below threshold'}

        return strategy
```

---

## Done Checklist

- [ ] Notebook created at `research/notebooks/models/logistic_baseline.ipynb`
- [ ] Model trained on real data
- [ ] Time-based train/test split (not random!)
- [ ] Accuracy, AUC-ROC metrics calculated
- [ ] Compared to Polymarket/Sportsbook baseline
- [ ] Model saved to file
- [ ] Module created at `src/cuic_quant/models/logistic_baseline.py`
- [ ] `to_strategy()` method works with backtester interface

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the notebook, show training output
2. Show accuracy vs. Polymarket baseline
3. Demonstrate `to_strategy()` integration

**Duration:** 3 minutes max

---

## Resources

- scikit-learn LogisticRegression: https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
- Railway DB connection: `docs/guides/connecting-to-database.md`
- Strategy interface: `docs/reference/strategy-interface.md` (from James)

---

## Who To Ask If Stuck

1. Google "sklearn logistic regression NBA prediction"
2. Dietrich — getting data from Railway
3. James — how strategy interface works
4. Tan — model evaluation questions
