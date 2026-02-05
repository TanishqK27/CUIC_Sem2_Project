# Task: Metrics Test Notebook

**Owner:** Ben
**Deadline:** Feb 26 (Week 3)
**Priority:** Medium — documentation and validation

---

## What You're Building

A Jupyter notebook that demonstrates how to use the metrics module and visualizations with James's backtester output.

---

## Why This Matters

This notebook is the "user manual" for your metrics code. Anyone on the team should be able to open it and understand how to calculate metrics and create charts from backtest results.

---

## Exactly What You Must Deliver

### 1. Test Notebook

Create `tools/metrics_example.ipynb` with this structure:

```python
# Cell 1: Title and Introduction
"""
# Metrics Module Example

This notebook demonstrates how to use the metrics module to analyze backtest results.

**What you'll learn:**
1. Calculate performance metrics (Sharpe, drawdown, win rate)
2. Create visualizations (equity curve, drawdown chart)
3. Generate a full backtest report
"""

# Cell 2: Imports
import pandas as pd
import numpy as np
from cuic_quant.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_all_metrics,
    plot_equity_curve,
    plot_drawdown,
    plot_trade_distribution,
    create_backtest_report,
)

# Cell 3: Create Sample Data
"""
## Sample Backtest Data

Let's create some fake trades to test the metrics.
In practice, this comes from James's backtester.
"""

# Generate 50 trades over 2 months
np.random.seed(42)
n_trades = 50
dates = pd.date_range('2026-01-01', periods=n_trades, freq='D')

# Random P&L with slight positive edge
pnl = np.random.normal(loc=5, scale=50, size=n_trades)

trades_df = pd.DataFrame({
    'date': dates,
    'game': [f'Game {i}' for i in range(n_trades)],
    'action': np.random.choice(['BUY_HOME', 'BUY_AWAY'], n_trades),
    'bet_size': 100,
    'pnl': pnl,
    'outcome': ['WIN' if p > 0 else 'LOSS' for p in pnl],
})
trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum() + 10000  # Start with $10k

trades_df.head(10)

# Cell 4: Individual Metrics
"""
## Calculating Individual Metrics
"""

# Calculate returns from P&L
returns = trades_df['pnl'] / 10000  # As fraction of starting bankroll

print(f"Sharpe Ratio: {calculate_sharpe_ratio(returns):.2f}")
print(f"Max Drawdown: {calculate_max_drawdown(trades_df['cumulative_pnl']):.1%}")
print(f"Win Rate: {calculate_win_rate(trades_df['outcome']):.1%}")
print(f"Profit Factor: {calculate_profit_factor(trades_df['pnl']):.2f}")

# Cell 5: All Metrics at Once
"""
## Getting All Metrics

Use `calculate_all_metrics()` to get everything in one call.
"""

metrics = calculate_all_metrics(trades_df)

for key, value in metrics.items():
    if isinstance(value, float):
        print(f"{key}: {value:.2f}")
    else:
        print(f"{key}: {value}")

# Cell 6: Equity Curve
"""
## Visualizations

### Equity Curve
Shows how the portfolio value changed over time.
"""

fig = plot_equity_curve(
    trades_df.set_index('date')['cumulative_pnl'],
    title="Strategy Equity Curve"
)

# Cell 7: Drawdown
"""
### Drawdown Chart
Shows how far the strategy fell from its peak at each point.
Lower (more negative) is worse.
"""

fig = plot_drawdown(
    trades_df.set_index('date')['cumulative_pnl'],
    title="Strategy Drawdown"
)

# Cell 8: Trade Distribution
"""
### Trade P&L Distribution
Shows the distribution of individual trade profits and losses.
"""

fig = plot_trade_distribution(
    trades_df['pnl'],
    title="Individual Trade P&L"
)

# Cell 9: Full Report
"""
## Full Backtest Report

Generate a complete report with all charts and metrics.
"""

fig = create_backtest_report(trades_df, metrics)

# Cell 10: Using with Real Backtester Output
"""
## Using with the Real Backtester

Here's how you'd use this with James's backtester output:

```python
# Run backtest
from backtester import backtest, load_data

data = load_data('2026-01-01', '2026-02-01')
trades = backtest(data, my_strategy)

# Calculate metrics
metrics = calculate_all_metrics(trades)
print(metrics)

# Create report
fig = create_backtest_report(trades, metrics, save_dir='outputs/')
```
"""

# Cell 11: Interpreting Results
"""
## How to Interpret These Metrics

| Metric | Good | Bad | Our Result |
|--------|------|-----|------------|
| Sharpe Ratio | > 1.0 | < 0.5 | Check output above |
| Max Drawdown | < 10% | > 25% | Check output above |
| Win Rate | > 55% | < 45% | Check output above |
| Profit Factor | > 1.5 | < 1.0 | Check output above |

**Key insights:**
- Sharpe > 2 is excellent, but watch for overfitting
- Max drawdown tells you the worst pain you'd experience
- Win rate alone doesn't matter — a 30% win rate can be profitable with big wins
- Profit factor > 1 means you're making money overall
"""
```

---

## Done Checklist

- [ ] Notebook created at `tools/metrics_example.ipynb`
- [ ] All cells run without errors
- [ ] Each section has clear markdown explanation
- [ ] Shows both individual metrics and combined report
- [ ] Includes interpretation guide
- [ ] Works with sample data
- [ ] Shows how to integrate with real backtester

---

## What You Will Present (Thursday Feb 26)

**Live demo showing:**
1. Run the notebook top to bottom
2. Show the final combined report
3. Explain what the metrics tell us about strategy quality

**Duration:** 2 minutes max

---

## Resources

- Your metrics module from Week 1
- Your visualization functions from Week 2
- James's backtester notebook for integration

---

## Who To Ask If Stuck

1. Run James's backtester first to understand output format
2. James — trades DataFrame structure
3. Tan — which metrics matter most
