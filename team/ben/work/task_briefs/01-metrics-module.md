# Task: Backtester Metrics Module

**Owner:** Ben
**Deadline:** Feb 12 (Week 1)
**Priority:** High — James needs this for the backtester

---

## What You're Building

A Python module that calculates performance metrics from backtest results. Given a DataFrame of trades, compute Sharpe ratio, max drawdown, win rate, etc.

---

## Why This Matters

Raw P&L isn't enough — we need standardized metrics to compare strategies. Every quant fund uses these metrics. Without them, we can't tell if a strategy is actually good.

---

## Exactly What You Must Deliver

### 1. Metrics Module

Create `src/cuic_quant/metrics/performance.py` with these functions:

```python
import pandas as pd
import numpy as np

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.

    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate (default 0)
        periods_per_year: Trading periods per year (252 for daily)

    Returns:
        Annualized Sharpe ratio

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, 0.01])
        >>> calculate_sharpe_ratio(returns)
        1.23  # example output
    """
    pass

def calculate_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """
    Calculate maximum drawdown as a decimal.

    Args:
        cumulative_pnl: Series of cumulative P&L values

    Returns:
        Maximum drawdown (0.15 means 15% drawdown)

    Example:
        >>> pnl = pd.Series([100, 120, 90, 110])
        >>> calculate_max_drawdown(pnl)
        0.25  # dropped from 120 to 90 = 25%
    """
    pass

def calculate_win_rate(outcomes: pd.Series) -> float:
    """
    Calculate win rate from outcomes.

    Args:
        outcomes: Series of 'WIN' or 'LOSS' strings

    Returns:
        Win rate as decimal (0.6 = 60%)
    """
    pass

def calculate_profit_factor(pnl: pd.Series) -> float:
    """
    Calculate profit factor (gross profit / gross loss).

    Args:
        pnl: Series of individual trade P&Ls

    Returns:
        Profit factor (>1 is profitable)
    """
    pass

def calculate_all_metrics(trades_df: pd.DataFrame) -> dict:
    """
    Calculate all metrics from a trades DataFrame.

    Args:
        trades_df: DataFrame with columns:
            - pnl: individual trade P&L
            - cumulative_pnl: running total
            - outcome: 'WIN' or 'LOSS'

    Returns:
        dict with keys:
            - sharpe_ratio
            - max_drawdown
            - win_rate
            - profit_factor
            - total_trades
            - total_pnl
    """
    pass
```

### 2. Module Init File

Create `src/cuic_quant/metrics/__init__.py`:

```python
"""Performance metrics for backtesting."""

from cuic_quant.metrics.performance import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_all_metrics,
)

__all__ = [
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_all_metrics",
]
```

---

## Done Checklist

- [ ] Module created at `src/cuic_quant/metrics/performance.py`
- [ ] All 5 functions implemented
- [ ] Each function has docstring with example
- [ ] `__init__.py` exports all functions
- [ ] Functions work with sample data (test manually)
- [ ] No crashes on edge cases (empty data, all wins, all losses)

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Import the module: `from cuic_quant.metrics import calculate_all_metrics`
2. Run on sample trades DataFrame
3. Show output dict with all metrics
4. Explain what each metric means

**Duration:** 2 minutes max

---

## Formulas Reference

**Sharpe Ratio:**
```
sharpe = (mean_return - risk_free) / std_return * sqrt(periods_per_year)
```

**Max Drawdown:**
```
peak = cumulative_max(pnl)
drawdown = (peak - pnl) / peak
max_drawdown = max(drawdown)
```

**Profit Factor:**
```
profit_factor = sum(winning_trades) / abs(sum(losing_trades))
```

---

## Who To Ask If Stuck

1. Google "Python Sharpe ratio calculation"
2. James — how the backtester output looks
3. Tan — clarification on formulas
