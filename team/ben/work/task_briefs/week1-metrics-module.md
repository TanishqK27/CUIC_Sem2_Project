# Week 1: Metrics Module

**Owner:** Ben
**Deadline:** Thursday Feb 12
**Priority:** HIGH — needed to evaluate any strategy

---

## Your Role

Build the metrics module. When James's backtester outputs trades, your code calculates Sharpe ratio, max drawdown, win rate, etc.

---

## DON'T WAIT FOR JAMES - Use Dummy Data

James is building the backtester in parallel. **Create dummy data matching his output format and build against that.** When James delivers, it will match this format.

### Create This Dummy Data First

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_dummy_backtest_results(n_trades: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    Create dummy backtester output matching James's EXACT format.
    Use this to build and test your metrics module.
    """
    np.random.seed(seed)

    # Generate realistic trades
    start = datetime(2026, 1, 1, 19, 0)
    pnls = np.random.normal(5, 50, n_trades)  # Slight positive edge

    cumulative = 0
    bankroll = 10000
    trades = []

    for i, pnl in enumerate(pnls):
        cumulative += pnl
        bankroll += pnl
        trades.append({
            'timestamp': start + timedelta(days=i),
            'game': f"Team{i*2} vs Team{i*2+1}",
            'action': np.random.choice(['BUY_HOME', 'BUY_AWAY']),
            'bet_size': 100.0,
            'odds': np.random.uniform(1.8, 2.2),
            'outcome': 'WIN' if pnl > 0 else 'LOSS',
            'pnl': pnl,
            'cumulative_pnl': cumulative,
            'bankroll': bankroll,
        })

    return pd.DataFrame(trades)

# USE THIS FOR ALL YOUR TESTING
dummy_results = create_dummy_backtest_results()
```

**James's real output will have these EXACT columns. Build your metrics against this.**

---

## This Week's Deliverables

### 1. Metrics Module

Create `src/cuic_quant/metrics/__init__.py`:

```python
"""Performance metrics for backtesting."""

import pandas as pd
import numpy as np

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252
) -> float:
    """
    Annualized Sharpe ratio.

    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year

    Returns:
        Annualized Sharpe ratio
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    excess_returns = returns - risk_free_rate / periods_per_year
    return np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()

def calculate_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """
    Maximum drawdown as decimal (0.15 = 15% drawdown).

    Args:
        cumulative_pnl: Series of cumulative P&L

    Returns:
        Max drawdown (0 to 1)
    """
    if len(cumulative_pnl) == 0:
        return 0.0

    peak = cumulative_pnl.expanding().max()
    drawdown = (peak - cumulative_pnl) / peak
    return drawdown.max() if not drawdown.isna().all() else 0.0

def calculate_win_rate(outcomes: pd.Series) -> float:
    """
    Win rate from outcomes.

    Args:
        outcomes: Series of 'WIN' or 'LOSS'

    Returns:
        Win rate (0 to 1)
    """
    if len(outcomes) == 0:
        return 0.0
    return (outcomes == 'WIN').mean()

def calculate_profit_factor(pnl: pd.Series) -> float:
    """
    Profit factor = gross profit / gross loss.

    Args:
        pnl: Series of trade P&Ls

    Returns:
        Profit factor (>1 is profitable)
    """
    wins = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl < 0].sum())

    if losses == 0:
        return float('inf') if wins > 0 else 0.0
    return wins / losses

def calculate_all_metrics(trades_df: pd.DataFrame) -> dict:
    """
    Calculate all metrics from backtester output.

    Args:
        trades_df: DataFrame with columns: pnl, cumulative_pnl, outcome

    Returns:
        dict with all metrics
    """
    if len(trades_df) == 0:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'profit_factor': 0,
        }

    # Calculate returns from P&L
    returns = trades_df['pnl'] / 10000  # Assume $10k base

    return {
        'total_trades': len(trades_df),
        'win_rate': calculate_win_rate(trades_df['outcome']),
        'total_pnl': trades_df['pnl'].sum(),
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'max_drawdown': calculate_max_drawdown(trades_df['cumulative_pnl']),
        'profit_factor': calculate_profit_factor(trades_df['pnl']),
    }

__all__ = [
    'calculate_sharpe_ratio',
    'calculate_max_drawdown',
    'calculate_win_rate',
    'calculate_profit_factor',
    'calculate_all_metrics',
]
```

### 2. Test Your Module

Create `tools/test_metrics.ipynb`:

```python
# Cell 1: Test with fake data
import pandas as pd
import numpy as np
from cuic_quant.metrics import calculate_all_metrics

# Create fake trades
np.random.seed(42)
fake_trades = pd.DataFrame({
    'pnl': np.random.normal(5, 50, 100),  # Slight positive edge
    'outcome': np.random.choice(['WIN', 'LOSS'], 100, p=[0.55, 0.45])
})
fake_trades['cumulative_pnl'] = fake_trades['pnl'].cumsum() + 10000

# Calculate metrics
metrics = calculate_all_metrics(fake_trades)
for k, v in metrics.items():
    print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")

# Cell 2: Test edge cases
# Empty DataFrame
empty_metrics = calculate_all_metrics(pd.DataFrame())
assert empty_metrics['total_trades'] == 0

# All wins
all_wins = pd.DataFrame({
    'pnl': [100, 100, 100],
    'outcome': ['WIN', 'WIN', 'WIN'],
    'cumulative_pnl': [100, 200, 300]
})
print(f"All wins profit factor: {calculate_all_metrics(all_wins)['profit_factor']}")

print("All tests passed!")
```

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| James | Get his results DataFrame format | Mon-Tue |
| James | Test metrics with real backtester output | Wed-Thu |
| Isameel | He tests your metrics too | Thu |

---

## Resources

**Required Reading:**
- File structure: `docs/SOPs/file-structure.md`
- Modularity: `docs/SOPs/modularity-upgrades.md`
- Team SOPs: `docs/SOPs/team-sops.md`


**Formulas:**
- Sharpe: `(mean_return - rf) / std_return * sqrt(252)`
- Max Drawdown: `max((peak - value) / peak)`
- Profit Factor: `sum(wins) / abs(sum(losses))`

**Libraries:**
- numpy: https://numpy.org/doc/
- pandas: https://pandas.pydata.org/docs/

**Reference:**
- Quantopian metrics: https://github.com/quantopian/empyrical
- PyFolio: https://github.com/quantopian/pyfolio

**AI Tools:**
- Use Claude for formula verification: "Is this Sharpe ratio calculation correct?"

---

## Done Checklist

- [ ] Module at `src/cuic_quant/metrics/__init__.py`
- [ ] All 5 functions implemented
- [ ] Test notebook passes
- [ ] Edge cases handled (empty data, all wins, all losses)
- [ ] Works with James's backtester output

---

## Thursday Presentation (2 min)

1. Import module: `from cuic_quant.metrics import calculate_all_metrics`
2. Run on James's backtester output
3. Show metrics dict
4. Explain what each metric means
