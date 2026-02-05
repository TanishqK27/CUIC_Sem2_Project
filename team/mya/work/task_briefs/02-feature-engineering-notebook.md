# Task: Feature Engineering Notebook

**Owner:** Mya
**Deadline:** Feb 26 (Week 3)
**Priority:** Medium — improves model performance

---

## What You're Building

A notebook that explores and creates features for NBA prediction models. Document which features help, which don't, and why.

---

## Why This Matters

Models are only as good as their features. "Garbage in, garbage out." This notebook will be the reference for anyone building models — they'll know exactly what features to use and how to create them.

---

## Exactly What You Must Deliver

### 1. Feature Engineering Notebook

Create `research/notebooks/models/feature_engineering.ipynb`:

```python
# Cell 1: Introduction
"""
# Feature Engineering for NBA Prediction

**Goal:** Identify and create features that predict NBA game outcomes.

**Categories:**
1. Market features (Polymarket, Sportsbook probabilities)
2. Team statistics (win rate, points per game)
3. Historical performance (last N games)
4. Derived features (gaps, ratios, momentum)
"""

# Cell 2: Load All Available Data
"""
## Data Sources

Load from Railway DB:
- price_snapshots (Polymarket)
- sportsbook_odds
- nba_team_stats
"""

# Connection code here...

# Cell 3: Market Features
"""
## Market Features

These come directly from Polymarket and sportsbooks.
"""

market_features = {
    'pm_home_prob': 'Polymarket home win probability',
    'sb_home_prob': 'Sportsbook implied probability',
    'gap': 'sb_home_prob - pm_home_prob',
    'abs_gap': 'Absolute value of gap',
    'gap_percentile': 'How extreme is this gap historically?',
}

# Calculate each
df['abs_gap'] = df['gap'].abs()
df['gap_percentile'] = df['gap'].rank(pct=True)

# Show correlation with home_win
for feature in market_features:
    corr = df[feature].corr(df['home_win'])
    print(f"{feature}: {corr:.3f}")

# Cell 4: Team Statistics Features
"""
## Team Statistics

Recent performance metrics for home and away teams.
"""

team_features = {
    'home_win_pct': 'Home team season win percentage',
    'away_win_pct': 'Away team season win percentage',
    'home_ppg': 'Home team points per game',
    'away_ppg': 'Away team points per game',
    'home_opp_ppg': 'Points allowed by home team per game',
    'away_opp_ppg': 'Points allowed by away team per game',
}

# Calculate derived features
df['win_pct_diff'] = df['home_win_pct'] - df['away_win_pct']
df['ppg_diff'] = df['home_ppg'] - df['away_ppg']
df['net_rating_home'] = df['home_ppg'] - df['home_opp_ppg']
df['net_rating_away'] = df['away_ppg'] - df['away_opp_ppg']
df['net_rating_diff'] = df['net_rating_home'] - df['net_rating_away']

# Correlation analysis
# ...

# Cell 5: Momentum Features
"""
## Momentum / Recent Form

How teams have performed in their last 5 games.
"""

def calculate_recent_form(team_games: pd.DataFrame, n_games: int = 5) -> float:
    """Calculate win rate over last N games."""
    recent = team_games.tail(n_games)
    return recent['win'].mean()

# Apply to each game
df['home_recent_form'] = ...  # Last 5 game win rate
df['away_recent_form'] = ...
df['form_diff'] = df['home_recent_form'] - df['away_recent_form']

# Cell 6: Feature Importance Analysis
"""
## Which Features Matter Most?

Use logistic regression coefficients and random forest importance.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Logistic regression coefficients
lr = LogisticRegression()
lr.fit(X, y)

importance_df = pd.DataFrame({
    'feature': feature_names,
    'lr_coef': np.abs(lr.coef_[0]),
})

# Random forest importance
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X, y)
importance_df['rf_importance'] = rf.feature_importances_

# Plot
importance_df.sort_values('rf_importance', ascending=True).plot(
    kind='barh', x='feature', y='rf_importance', figsize=(10, 8)
)
plt.title('Feature Importance')

# Cell 7: Correlation Matrix
"""
## Feature Correlations

Check for multicollinearity — highly correlated features may be redundant.
"""

import seaborn as sns

corr_matrix = df[all_features].corr()
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Feature Correlation Matrix')

# Cell 8: Feature Selection
"""
## Final Feature Set

Based on importance and correlation analysis:
"""

selected_features = [
    # Market features
    'pm_home_prob',
    'gap',

    # Team stats (keep uncorrelated ones)
    'net_rating_diff',

    # Momentum
    'form_diff',
]

print("Selected features and their predictive power:")
for f in selected_features:
    corr = df[f].corr(df['home_win'])
    print(f"  {f}: correlation = {corr:.3f}")

# Cell 9: Test on Model
"""
## Validation: Does adding features help?

Compare logistic regression with:
1. Market features only
2. Market + team stats
3. All features
"""

from sklearn.model_selection import cross_val_score

feature_sets = {
    'Market only': ['pm_home_prob', 'sb_home_prob', 'gap'],
    'Market + Team': ['pm_home_prob', 'gap', 'net_rating_diff'],
    'All features': selected_features,
}

for name, features in feature_sets.items():
    X = df[features]
    scores = cross_val_score(LogisticRegression(), X, y, cv=5, scoring='accuracy')
    print(f"{name}: {scores.mean():.1%} (+/- {scores.std()*2:.1%})")

# Cell 10: Conclusion
"""
## Summary

| Feature Category | Best Features | Impact |
|-----------------|---------------|--------|
| Market | pm_home_prob, gap | High |
| Team Stats | net_rating_diff | Medium |
| Momentum | form_diff | Low |

**Key findings:**
1. Market probabilities are already very good predictors
2. Adding team stats provides marginal improvement
3. [Other findings...]

**Recommended feature set for models:**
```python
features = ['pm_home_prob', 'gap', 'net_rating_diff', 'form_diff']
```
"""
```

---

## Done Checklist

- [ ] Notebook created at `research/notebooks/models/feature_engineering.ipynb`
- [ ] Market features documented with correlations
- [ ] Team stat features calculated and tested
- [ ] Momentum features created
- [ ] Feature importance analysis (logistic + random forest)
- [ ] Correlation matrix visualization
- [ ] Final feature set selected with justification
- [ ] Validated that features improve model

---

## What You Will Present (Thursday Feb 26)

**Live demo showing:**
1. Feature importance chart
2. Correlation matrix
3. Accuracy improvement with added features
4. Recommended feature set

**Duration:** 3 minutes max

---

## Resources

- scikit-learn feature selection: https://scikit-learn.org/stable/modules/feature_selection.html
- Your logistic baseline notebook from Week 2
- NBA stats from Miran/Vansheeka

---

## Who To Ask If Stuck

1. Google "feature engineering sports prediction"
2. Miran/Vansheeka — what NBA stats are available
3. Dietrich — data joins in Railway
4. Tan — which features make theoretical sense
