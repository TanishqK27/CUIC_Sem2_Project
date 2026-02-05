# Task: Polymarket vs Sportsbook Gap Analysis

**Owner:** Max
**Deadline:** Feb 26 (Week 3)
**Priority:** Medium — validates core hypothesis

---

## What You're Building

A Jupyter notebook that analyzes the gaps between Polymarket probabilities and sportsbook odds. This tests our core hypothesis: are there profitable differences?

---

## Why This Matters

Our entire strategy is based on finding gaps between Polymarket and sportsbooks. If gaps don't exist or are too small, our strategy won't work. This analysis tells us if the opportunity is real.

---

## Exactly What You Must Deliver

### 1. Gap Analysis Notebook

Create `research/notebooks/analysis/gap_analysis.ipynb`:

```python
# Cell 1: Introduction
"""
# Polymarket vs Sportsbook Gap Analysis

**Hypothesis:** Polymarket prices sometimes diverge from sportsbook odds,
creating arbitrage or statistical edge opportunities.

**Questions we're answering:**
1. How big are the gaps?
2. How often do gaps occur?
3. Do gaps predict outcomes? (i.e., when PM and SB disagree, who's right?)
4. Are gaps profitable to trade?
"""

# Cell 2: Setup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])

# Cell 3: Load Data
"""
## Load and Prepare Data

Get matched data: games with both Polymarket and Sportsbook prices.
"""

# This query joins PM and SB data
# Adjust based on actual table names and columns
query = """
SELECT
    m.id,
    m.home_team,
    m.away_team,
    m.commence_time,
    -- Sportsbook probability (pick one bookmaker for consistency)
    1.0 / o.home_odds / (1.0/o.home_odds + 1.0/o.away_odds) as sb_home_prob,
    -- Polymarket probability (from price_snapshots or similar)
    -- pm.home_prob as pm_home_prob,
    -- Actual outcome
    -- g.home_win
FROM sportsbook_matches m
JOIN sportsbook_odds o ON m.id = o.match_id
-- JOIN polymarket_data pm ON m.external_id = pm.game_id
-- JOIN game_outcomes g ON m.external_id = g.game_id
WHERE o.bookmaker = 'fanduel'
  AND m.commence_time < NOW()
ORDER BY m.commence_time
"""

df = pd.read_sql(query, engine)
print(f"Loaded {len(df)} games with matched data")

# Cell 4: Calculate Gaps
"""
## Calculate Probability Gaps

Gap = Sportsbook probability - Polymarket probability

Positive gap: Sportsbook thinks home is MORE likely than PM
Negative gap: Sportsbook thinks home is LESS likely than PM
"""

df['gap'] = df['sb_home_prob'] - df['pm_home_prob']
df['abs_gap'] = df['gap'].abs()

print(f"Mean gap: {df['gap'].mean():.3f}")
print(f"Median gap: {df['gap'].median():.3f}")
print(f"Std gap: {df['gap'].std():.3f}")
print(f"Max gap: {df['gap'].max():.3f}")
print(f"Min gap: {df['gap'].min():.3f}")

# Cell 5: Gap Distribution
"""
## Gap Distribution

How are gaps distributed?
"""

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(df['gap'], bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(x=0, color='red', linestyle='--', linewidth=2)
axes[0].set_xlabel('Gap (SB - PM)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Distribution of Probability Gaps')

# Box plot
axes[1].boxplot(df['gap'])
axes[1].set_ylabel('Gap')
axes[1].set_title('Gap Spread')

plt.tight_layout()

# Cell 6: Large Gaps
"""
## When Do Large Gaps Occur?

Look at games with gaps > 5%
"""

large_gaps = df[df['abs_gap'] > 0.05].copy()
print(f"Games with >5% gap: {len(large_gaps)} ({len(large_gaps)/len(df):.1%})")

# Analyze large gap games
large_gaps[['home_team', 'away_team', 'pm_home_prob', 'sb_home_prob', 'gap']].head(20)

# Cell 7: Gap vs Outcome
"""
## Do Gaps Predict Outcomes?

Key question: When PM and SB disagree, who is more accurate?
"""

# Only games with known outcomes
games_with_outcome = df[df['home_win'].notna()].copy()

# Bin gaps into categories
bins = [-1, -0.05, -0.02, 0.02, 0.05, 1]
labels = ['Large -', 'Small -', 'Neutral', 'Small +', 'Large +']
games_with_outcome['gap_category'] = pd.cut(games_with_outcome['gap'], bins=bins, labels=labels)

# Win rate by gap category
gap_accuracy = games_with_outcome.groupby('gap_category').agg({
    'home_win': ['mean', 'count']
}).round(3)

print("Home Win Rate by Gap Category:")
print(gap_accuracy)

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
gap_stats = games_with_outcome.groupby('gap_category')['home_win'].agg(['mean', 'count'])
ax.bar(gap_stats.index, gap_stats['mean'], color=['red', 'orange', 'gray', 'lightgreen', 'green'])
ax.axhline(y=0.5, color='black', linestyle='--')
ax.set_xlabel('Gap Category')
ax.set_ylabel('Home Win Rate')
ax.set_title('Home Win Rate by Gap Category')

# Cell 8: Who's More Accurate?
"""
## Accuracy Comparison

When PM and SB disagree, who predicts better?
"""

def get_predicted_winner(prob):
    """Returns 1 if predicts home, 0 if predicts away."""
    return (prob > 0.5).astype(int)

games_with_outcome['pm_prediction'] = get_predicted_winner(games_with_outcome['pm_home_prob'])
games_with_outcome['sb_prediction'] = get_predicted_winner(games_with_outcome['sb_home_prob'])
games_with_outcome['home_win_int'] = games_with_outcome['home_win'].astype(int)

# Accuracy
pm_accuracy = (games_with_outcome['pm_prediction'] == games_with_outcome['home_win_int']).mean()
sb_accuracy = (games_with_outcome['sb_prediction'] == games_with_outcome['home_win_int']).mean()

print(f"Polymarket accuracy: {pm_accuracy:.1%}")
print(f"Sportsbook accuracy: {sb_accuracy:.1%}")

# When they disagree
disagree = games_with_outcome[games_with_outcome['pm_prediction'] != games_with_outcome['sb_prediction']]
print(f"\nGames where PM and SB disagree: {len(disagree)}")

pm_right_when_disagree = (disagree['pm_prediction'] == disagree['home_win_int']).mean()
print(f"When they disagree, PM is right: {pm_right_when_disagree:.1%}")
print(f"When they disagree, SB is right: {1-pm_right_when_disagree:.1%}")

# Cell 9: Trading Simulation
"""
## Simple Trading Simulation

If we bet on gaps closing, would we make money?

Strategy: When gap > 5%, bet that PM is right.
"""

# Simple strategy: bet PM when gap > 5%
trades = games_with_outcome[games_with_outcome['abs_gap'] > 0.05].copy()

def simulate_trade(row):
    """Simulate betting $100 that PM is right."""
    pm_says_home = row['pm_home_prob'] > 0.5
    sb_odds = 1/row['sb_home_prob'] if pm_says_home else 1/(1-row['sb_home_prob'])

    if pm_says_home:
        won = row['home_win'] == 1
    else:
        won = row['home_win'] == 0

    if won:
        return 100 * (sb_odds - 1)  # Profit
    else:
        return -100  # Loss

trades['pnl'] = trades.apply(simulate_trade, axis=1)
trades['cumulative_pnl'] = trades['pnl'].cumsum()

print(f"Total trades: {len(trades)}")
print(f"Win rate: {(trades['pnl'] > 0).mean():.1%}")
print(f"Total P&L: ${trades['pnl'].sum():,.2f}")
print(f"Average P&L per trade: ${trades['pnl'].mean():.2f}")

# Plot cumulative P&L
plt.figure(figsize=(12, 5))
plt.plot(trades['cumulative_pnl'])
plt.axhline(y=0, color='red', linestyle='--')
plt.xlabel('Trade Number')
plt.ylabel('Cumulative P&L ($)')
plt.title('Gap Trading Strategy Performance')

# Cell 10: Conclusion
"""
## Summary and Conclusions

### Key Findings

1. **Gap Size:**
   - Average gap: X%
   - X% of games have gap > 5%

2. **Gap Predictability:**
   - When PM and SB disagree, [PM/SB] is right X% of the time

3. **Trading Potential:**
   - Simple gap strategy: $X P&L on X trades
   - [Profitable/Unprofitable]

### Recommendations

1. [Based on findings, is gap trading viable?]
2. [What threshold should we use?]
3. [Should we trust PM or SB more?]

### Next Steps

- [ ] Test with more data
- [ ] Refine strategy
- [ ] Add Kelly sizing
"""
```

---

## Done Checklist

- [ ] Notebook created at `research/notebooks/analysis/gap_analysis.ipynb`
- [ ] Gap distribution visualized
- [ ] Large gaps identified and analyzed
- [ ] Gap vs outcome relationship tested
- [ ] PM vs SB accuracy compared
- [ ] Simple trading simulation run
- [ ] Conclusions documented with recommendations

---

## What You Will Present (Thursday Feb 26)

**Live demo showing:**
1. Gap distribution histogram
2. Key finding: how often do big gaps occur?
3. Who's more accurate when they disagree?
4. Simple trading simulation results

**Duration:** 3 minutes max

---

## Resources

- Your schema documentation from Week 2
- Alfie's query examples notebook
- matplotlib/seaborn for plots

---

## Who To Ask If Stuck

1. Dietrich — data joins between PM and SB
2. Ben — statistical interpretation
3. Tan — trading strategy logic
