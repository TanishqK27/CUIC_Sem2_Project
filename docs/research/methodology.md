# Research Methodology Guide

Standards and best practices for conducting quantitative research in the CUIC Quant Fund project.

---

## Table of Contents

1. [Research Philosophy](#research-philosophy)
2. [Research Workflow](#research-workflow)
3. [Notebook Standards](#notebook-standards)
4. [Statistical Rigor](#statistical-rigor)
5. [Backtesting Guidelines](#backtesting-guidelines)
6. [Documentation Standards](#documentation-standards)
7. [Peer Review Process](#peer-review-process)
8. [From Research to Production](#from-research-to-production)

---

## Research Philosophy

### Core Principles

1. **Skepticism First**: Assume every finding is spurious until proven otherwise
2. **Reproducibility**: Every result must be reproducible by another team member
3. **Simplicity**: Prefer simple explanations over complex ones (Occam's Razor)
4. **Out-of-Sample Testing**: Never evaluate performance only on data used for development
5. **Documentation**: Document everything—future you will thank present you

### Common Pitfalls to Avoid

| Pitfall | Description | Prevention |
|---------|-------------|------------|
| **Overfitting** | Model fits noise, not signal | Use cross-validation, out-of-sample testing |
| **Look-ahead Bias** | Using future information | Strict temporal ordering of data |
| **Survivorship Bias** | Only analyzing surviving entities | Include delisted/closed markets |
| **Data Snooping** | Testing many hypotheses, reporting winners | Pre-register hypotheses |
| **P-hacking** | Manipulating analysis until p < 0.05 | Use multiple testing corrections |

---

## Research Workflow

### 1. Hypothesis Formation

Every research project starts with a clear hypothesis:

```markdown
## Hypothesis

**Statement**: Polymarket prices for political events revert to the mean
after large moves (>5%) within 24 hours.

**Reasoning**: Large moves often driven by news overreaction, which
corrects as more information is processed.

**Falsifiable Prediction**: Mean reversion strategy should generate
positive returns net of transaction costs on out-of-sample data.
```

### 2. Data Collection

```python
"""Data collection phase example."""

import pandas as pd
from datetime import datetime, timedelta
from cuic_quant.data import PolymarketClient

# Define data requirements
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)
MARKETS = ["political"]  # Market categories

# Collect data
client = PolymarketClient()
raw_data = client.get_historical_prices(
    categories=MARKETS,
    start_date=START_DATE,
    end_date=END_DATE,
)

# Save raw data with metadata
raw_data.to_parquet(
    "data/raw/polymarket_political_2024.parquet",
    index=False,
)

# Document data collection
metadata = {
    "collection_date": datetime.now().isoformat(),
    "source": "Polymarket API",
    "date_range": f"{START_DATE} to {END_DATE}",
    "markets": MARKETS,
    "rows": len(raw_data),
}
```

### 3. Exploratory Analysis

```python
"""Exploratory Data Analysis."""

import matplotlib.pyplot as plt
import seaborn as sns

# Basic statistics
print(df.describe())

# Distribution of returns
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Returns distribution
df["returns"].hist(ax=axes[0], bins=50)
axes[0].set_title("Return Distribution")
axes[0].axvline(0, color="red", linestyle="--")

# Q-Q plot
from scipy import stats
stats.probplot(df["returns"].dropna(), plot=axes[1])
axes[1].set_title("Q-Q Plot vs Normal")

plt.tight_layout()
plt.savefig("research/notebooks/exploratory/returns_dist.png")
```

### 4. Strategy Development

```python
"""Strategy development with proper train/test split."""

from sklearn.model_selection import TimeSeriesSplit

# IMPORTANT: Time series split, not random
tscv = TimeSeriesSplit(n_splits=5)

# Never use future data
train_end = "2024-09-30"
test_start = "2024-10-01"

train_data = df[df["date"] <= train_end]
test_data = df[df["date"] >= test_start]

print(f"Train: {len(train_data)} rows, {train_data['date'].min()} to {train_data['date'].max()}")
print(f"Test: {len(test_data)} rows, {test_data['date'].min()} to {test_data['date'].max()}")
```

### 5. Validation

```python
"""Statistical validation of results."""

from scipy import stats

# Test if returns are significantly different from zero
returns = strategy_returns["return"]

# t-test
t_stat, p_value = stats.ttest_1samp(returns, 0)
print(f"t-statistic: {t_stat:.3f}")
print(f"p-value: {p_value:.4f}")

# Bootstrap confidence interval
n_bootstrap = 10000
bootstrap_means = [
    returns.sample(len(returns), replace=True).mean()
    for _ in range(n_bootstrap)
]
ci_lower = np.percentile(bootstrap_means, 2.5)
ci_upper = np.percentile(bootstrap_means, 97.5)
print(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

# Effect size (Sharpe ratio)
sharpe = returns.mean() / returns.std() * np.sqrt(252)
print(f"Annualized Sharpe: {sharpe:.2f}")
```

### 6. Documentation & Communication

```markdown
## Results Summary

### Key Findings
1. Mean reversion effect exists (p < 0.01)
2. Effect size: 1.2% average return per trade
3. Sharpe ratio: 1.5 (annualized)

### Limitations
1. Transaction costs not fully modeled
2. Limited to 2024 data
3. Capacity constraints unknown

### Next Steps
1. Implement transaction cost model
2. Extend to other market categories
3. Paper trade for 1 month
```

---

## Notebook Standards

### Structure

Every research notebook should follow this structure:

```
1. Title & Metadata
2. Abstract/Summary (TL;DR)
3. Hypothesis
4. Data Description
5. Methodology
6. Results
7. Discussion
8. Conclusions
9. Next Steps
10. Appendix (optional)
```

### Template Usage

Use the research template:

```
/research-template polymarket mean-reversion
```

This creates a properly structured notebook at:
`research/notebooks/polymarket/mean-reversion.ipynb`

### Code Standards in Notebooks

```python
# Cell 1: Imports (always first)
"""
Mean Reversion Strategy Analysis
Author: Your Name
Date: 2025-01-15
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

# Project imports
from cuic_quant.data import PolymarketClient
from cuic_quant.strategies import MeanReversionStrategy

# Cell 2: Configuration
CONFIG = {
    "lookback_period": 24,  # hours
    "threshold": 0.05,      # 5% move
    "holding_period": 24,   # hours
}

# Cell 3+: Analysis with clear markdown explanations
```

### Documentation in Cells

```python
# Good: Explain the "why"
# We use a 24-hour lookback because political news cycles
# typically resolve within this timeframe (see Smith et al., 2023)
lookback = 24

# Bad: State the obvious
# Set lookback to 24
lookback = 24
```

---

## Statistical Rigor

### Multiple Testing Correction

When testing multiple hypotheses, adjust p-values:

```python
from statsmodels.stats.multitest import multipletests

# Original p-values from multiple tests
p_values = [0.03, 0.01, 0.04, 0.001, 0.08]

# Bonferroni correction (conservative)
bonferroni_corrected = [min(p * len(p_values), 1.0) for p in p_values]

# Benjamini-Hochberg (less conservative, controls FDR)
rejected, bh_corrected, _, _ = multipletests(p_values, method="fdr_bh")

print("Original:", p_values)
print("Bonferroni:", bonferroni_corrected)
print("BH-corrected:", bh_corrected)
```

### Effect Size Reporting

Always report effect sizes, not just p-values:

```python
def calculate_effect_sizes(returns: pd.Series) -> dict:
    """Calculate multiple effect size measures."""
    return {
        "mean_return": returns.mean(),
        "sharpe_ratio": returns.mean() / returns.std() * np.sqrt(252),
        "sortino_ratio": returns.mean() / returns[returns < 0].std() * np.sqrt(252),
        "win_rate": (returns > 0).mean(),
        "profit_factor": returns[returns > 0].sum() / abs(returns[returns < 0].sum()),
    }
```

### Confidence Intervals

Report confidence intervals for all key metrics:

```python
def bootstrap_metric(
    data: np.ndarray,
    metric_func: callable,
    n_bootstrap: int = 10000,
    ci: float = 0.95,
) -> dict:
    """Calculate metric with bootstrap confidence interval."""
    point_estimate = metric_func(data)

    bootstrap_estimates = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_estimates.append(metric_func(sample))

    alpha = 1 - ci
    lower = np.percentile(bootstrap_estimates, alpha / 2 * 100)
    upper = np.percentile(bootstrap_estimates, (1 - alpha / 2) * 100)

    return {
        "estimate": point_estimate,
        "ci_lower": lower,
        "ci_upper": upper,
        "ci_level": ci,
    }
```

---

## Backtesting Guidelines

### Walk-Forward Analysis

```python
def walk_forward_backtest(
    data: pd.DataFrame,
    strategy: callable,
    train_window: int,
    test_window: int,
) -> pd.DataFrame:
    """Perform walk-forward backtesting.

    This simulates realistic strategy deployment where
    the model is periodically retrained on new data.

    Args:
        data: Full dataset with datetime index
        strategy: Strategy function(train_data) -> model
        train_window: Days of training data
        test_window: Days to test before retraining

    Returns:
        DataFrame of out-of-sample returns
    """
    results = []

    for train_end in pd.date_range(
        data.index[train_window],
        data.index[-test_window],
        freq=f"{test_window}D",
    ):
        train_start = train_end - pd.Timedelta(days=train_window)
        test_end = train_end + pd.Timedelta(days=test_window)

        train = data[train_start:train_end]
        test = data[train_end:test_end]

        # Train model
        model = strategy(train)

        # Generate out-of-sample predictions
        predictions = model.predict(test)

        results.append({
            "train_end": train_end,
            "test_start": train_end,
            "test_end": test_end,
            "return": predictions["return"].sum(),
            "n_trades": len(predictions),
        })

    return pd.DataFrame(results)
```

### Transaction Costs

Always model realistic transaction costs:

```python
def apply_transaction_costs(
    returns: pd.Series,
    spread: float = 0.02,       # 2% spread
    slippage: float = 0.005,    # 0.5% slippage
    commission: float = 0.001,  # 0.1% commission
) -> pd.Series:
    """Apply realistic transaction costs to returns.

    Args:
        returns: Raw strategy returns
        spread: Bid-ask spread as decimal
        slippage: Expected slippage as decimal
        commission: Commission per trade as decimal

    Returns:
        Returns net of transaction costs
    """
    # Total cost per round-trip trade
    cost_per_trade = spread + (2 * slippage) + (2 * commission)

    # Assume each return represents a trade
    net_returns = returns - cost_per_trade

    return net_returns
```

### Capacity Analysis

```python
def estimate_capacity(
    market_volume: float,
    participation_rate: float = 0.05,
    avg_trade_size: float = 1000,
) -> dict:
    """Estimate strategy capacity constraints.

    Args:
        market_volume: Average daily market volume ($)
        participation_rate: Max % of volume to participate
        avg_trade_size: Average trade size ($)

    Returns:
        Capacity estimates
    """
    daily_capacity = market_volume * participation_rate
    max_trades_per_day = daily_capacity / avg_trade_size

    return {
        "daily_capacity_usd": daily_capacity,
        "max_trades_per_day": max_trades_per_day,
        "max_portfolio_size": daily_capacity * 10,  # Assume 10-day holding
    }
```

---

## Documentation Standards

### Research Log Entry

When completing research, update your log:

```
/update-log tan Completed mean reversion analysis - Sharpe 1.5, see notebooks/polymarket/mean-reversion.ipynb
```

### Idea Submission

Add to `research/ideas/README.md`:

```markdown
## [IDEA] Cross-Market Arbitrage Between Kalshi and Polymarket

**Submitted by:** Your Name
**Date:** 2025-01-15
**Status:** Proposed

### Hypothesis
Identical events on Kalshi and Polymarket may have price discrepancies
that can be arbitraged.

### Data Required
- Polymarket real-time prices
- Kalshi real-time prices
- Mapping between equivalent markets

### Initial Analysis
- Identified 50+ potentially matched markets
- Preliminary data shows 2-5% price differences

### Next Steps
1. Build market matching algorithm
2. Analyze historical price divergence
3. Model transaction costs and execution risk
```

### Paper References

Add to `research/papers/README.md`:

```markdown
## Prediction Markets

### [Prediction Markets: Practical Experiments in Small Markets and Behaviors Observed](https://example.com/paper1)
- **Authors:** Smith, J., & Johnson, A. (2023)
- **Key Finding:** Markets with <$10k volume show higher inefficiency
- **Relevance:** Supports focus on smaller Polymarket markets

### [The Wisdom of Crowds Revisited](https://example.com/paper2)
- **Authors:** Surowiecki, J. (2024)
- **Key Finding:** Prediction market accuracy degrades with polarization
- **Relevance:** Political markets may be less efficient
```

---

## Peer Review Process

### Before Submitting for Review

- [ ] Notebook runs from top to bottom without errors
- [ ] All data sources documented
- [ ] Statistical tests properly applied
- [ ] Results include confidence intervals
- [ ] Transaction costs modeled
- [ ] Out-of-sample testing performed
- [ ] Limitations clearly stated

### Review Checklist

Reviewers should verify:

1. **Reproducibility**: Can you run the notebook and get same results?
2. **Statistical Validity**: Are the tests appropriate?
3. **Data Integrity**: Any look-ahead bias?
4. **Practical Viability**: Is this tradeable?
5. **Documentation**: Is it understandable?

### Review Feedback Format

```markdown
## Review: Mean Reversion Analysis

**Reviewer:** Reviewer Name
**Date:** 2025-01-20

### Summary
Good initial analysis, needs more robust statistical testing.

### Strengths
- Clear hypothesis
- Good visualization
- Proper train/test split

### Areas for Improvement
1. Need to correct for multiple testing (testing 5 thresholds)
2. Transaction cost model assumes constant spread
3. Should add bootstrap confidence intervals

### Recommendation
Minor revisions required before proceeding to paper trading.
```

---

## From Research to Production

### Promotion Criteria

Research can be promoted to `src/cuic_quant/` when:

1. **Statistical Significance**: p < 0.01 after multiple testing correction
2. **Economic Significance**: Sharpe > 1.0 after realistic costs
3. **Robustness**: Consistent across multiple time periods
4. **Peer Review**: Approved by at least one other team member
5. **Documentation**: Full methodology documented

### Promotion Process

1. Create PR moving code from notebook to `src/`
2. Add unit tests
3. Add integration tests
4. Update documentation
5. Request review

### Example Promotion

```python
# From: research/notebooks/polymarket/mean-reversion.ipynb
# To: src/cuic_quant/strategies/mean_reversion.py

"""Mean reversion strategy for prediction markets."""

from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class MeanReversionConfig:
    """Configuration for mean reversion strategy."""

    lookback_hours: int = 24
    threshold: float = 0.05
    holding_hours: int = 24


class MeanReversionStrategy:
    """Mean reversion strategy for prediction markets.

    Based on research documented in:
    research/notebooks/polymarket/mean-reversion.ipynb

    Key findings:
    - Sharpe: 1.5 (out-of-sample)
    - Win rate: 58%
    - Avg holding period: 18 hours
    """

    def __init__(self, config: MeanReversionConfig | None = None):
        self.config = config or MeanReversionConfig()

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals."""
        # Implementation based on validated research
        ...
```

---

## Resources

### Books

- *Advances in Financial Machine Learning* by Marcos López de Prado
- *Evidence-Based Technical Analysis* by David Aronson
- *Quantitative Trading* by Ernest Chan

### Papers

- "Pseudo-Mathematics and Financial Charlatanism" - López de Prado
- "The Probability of Backtest Overfitting" - Bailey et al.
- "Evaluating Trading Strategies" - Harvey et al.

### Tools

- [Zipline](https://github.com/quantopian/zipline) - Backtesting library
- [Backtrader](https://www.backtrader.com/) - Python backtesting
- [QuantStats](https://github.com/ranaroussi/quantstats) - Portfolio analytics

---

## Next Steps

1. Create your first research notebook with `/research-template`
2. Document your hypothesis clearly
3. Follow the workflow outlined above
4. Submit for peer review when ready
