# Task: Backtester Core Engine

**Owner:** James
**Deadline:** Feb 19 (Week 2) — design in Week 1, build in Week 2
**Priority:** Critical — everything depends on this

---

## What You're Building

A Jupyter notebook that backtests trading strategies on historical data. Given a strategy function and a date range, it simulates trading and outputs P&L.

---

## Why This Matters

This is THE core deliverable. Without a backtester, we can't evaluate any strategy. Every model we build needs to run through this.

---

## Exactly What You Must Deliver

### 1. Backtester Notebook

Create `tools/backtester.ipynb` with this structure:

```python
# Cell 1: Setup and imports
import pandas as pd
import numpy as np
from datetime import datetime

# Cell 2: Load data from Railway DB
def load_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Load price snapshots and odds data for backtesting."""
    pass

# Cell 3: Strategy interface
def example_strategy(row: pd.Series) -> dict:
    """
    Example strategy function.

    Input: row with columns [game, pm_home_prob, sb_home_prob, gap, ...]
    Output: {
        'action': 'BUY_HOME' | 'BUY_AWAY' | 'SKIP',
        'confidence': float between 0 and 1,
        'size': float (bet size in $)
    }
    """
    # Simple example: bet home if gap > 5%
    if row['gap'] > 0.05:
        return {'action': 'BUY_HOME', 'confidence': 0.6, 'size': 100}
    return {'action': 'SKIP', 'confidence': 0, 'size': 0}

# Cell 4: Backtester core loop
def backtest(
    data: pd.DataFrame,
    strategy_fn,
    initial_bankroll: float = 10000
) -> pd.DataFrame:
    """
    Run backtest.

    Returns DataFrame with columns:
    - date
    - game
    - action
    - bet_size
    - outcome (win/loss)
    - pnl
    - cumulative_pnl
    - bankroll
    """
    trades = []

    for idx, row in data.iterrows():
        signal = strategy_fn(row)

        if signal['action'] == 'SKIP':
            continue

        # Simulate the trade
        # ... determine if bet won based on actual result
        # ... calculate pnl

        trades.append({
            'date': row['timestamp'],
            'game': row['game'],
            'action': signal['action'],
            'bet_size': signal['size'],
            'outcome': outcome,  # 'WIN' or 'LOSS'
            'pnl': pnl,
            'cumulative_pnl': running_total,
            'bankroll': current_bankroll
        })

    return pd.DataFrame(trades)

# Cell 5: Run backtest
data = load_data('2026-01-01', '2026-02-01')
results = backtest(data, example_strategy)

# Cell 6: Display results
print(f"Total trades: {len(results)}")
print(f"Win rate: {(results['outcome'] == 'WIN').mean():.1%}")
print(f"Total P&L: ${results['pnl'].sum():,.2f}")
```

### 2. Features Required

- **Handles game outcomes:** Knows who won each game to determine bet results
- **Tracks bankroll:** Running balance, can't bet more than you have
- **Outputs trade log:** Every trade with full details
- **Works with any strategy:** Strategy is a pluggable function

### 3. Dummy Strategy Test

Prove it works with a brain-dead strategy:
- "Always bet home team, $100 per game"
- Show results make sense (should be ~50% win rate)

---

## Done Checklist

- [ ] Notebook created at `tools/backtester.ipynb`
- [ ] Loads data from Railway DB
- [ ] Strategy function interface documented
- [ ] Core backtest loop working
- [ ] Tracks all trades with P&L
- [ ] Tested with dummy "always bet home" strategy
- [ ] Results make sense (verified manually for a few games)
- [ ] Clear markdown cells explaining each section

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the notebook end-to-end
2. Show the trades DataFrame
3. Show total P&L and win rate
4. Explain how someone plugs in their own strategy

**Duration:** 3 minutes max

---

## Resources

- Existing Polymarket data: `tools/polymarket_data_exploration.ipynb`
- sports-betting library (reference): https://github.com/georgedouzas/sports-betting
- Connection guide: `docs/guides/connecting-to-database.md`

---

## Who To Ask If Stuck

1. Ben — coordinating on metrics integration
2. Dietrich — data questions
3. Tan — architecture decisions
