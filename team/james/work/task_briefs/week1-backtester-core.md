# Week 1: Backtester Core Engine

**Owner:** James
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL — all strategies run through this

---

## Your Role

Build THE backtester. This is the most important piece of infrastructure. Every model and strategy will be evaluated using your code.

---

## This Week's Deliverables

### 1. Backtester Notebook

Create `tools/backtester.ipynb`:

```python
# Cell 1: Imports
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
import os

# Cell 2: Load Data Function
def load_backtest_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Load historical data for backtesting.

    Returns DataFrame with columns:
    - timestamp, game, home_team, away_team
    - home_odds, away_odds (decimal)
    - home_win (1 or 0, actual outcome)
    """
    engine = create_engine(os.environ['DATABASE_URL'])

    query = f"""
        SELECT
            m.commence_time as timestamp,
            m.home_team || ' vs ' || m.away_team as game,
            m.home_team,
            m.away_team,
            AVG(o.home_odds) as home_odds,
            AVG(o.away_odds) as away_odds
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
        WHERE m.commence_time BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY m.id, m.commence_time, m.home_team, m.away_team
        ORDER BY m.commence_time
    """
    return pd.read_sql(query, engine)

# Cell 3: Strategy Interface
def example_strategy(row: pd.Series, context: dict = None) -> dict:
    """
    Example strategy function.

    Args:
        row: Single game data
        context: Persistent state (optional)

    Returns:
        {
            'action': 'BUY_HOME' | 'BUY_AWAY' | 'SKIP',
            'confidence': float 0-1,
            'size': float (dollars),
            'reason': str (optional)
        }
    """
    # Simple example: always bet home $100
    return {
        'action': 'BUY_HOME',
        'confidence': 0.5,
        'size': 100,
        'reason': 'Example strategy'
    }

# Cell 4: Core Backtest Function
def backtest(
    data: pd.DataFrame,
    strategy_fn,
    initial_bankroll: float = 10000
) -> pd.DataFrame:
    """
    Run backtest on historical data.

    Returns DataFrame with columns:
    - timestamp, game, action, bet_size
    - outcome ('WIN' or 'LOSS')
    - pnl (profit/loss for this trade)
    - cumulative_pnl
    - bankroll
    """
    if len(data) == 0:
        return pd.DataFrame()

    trades = []
    bankroll = initial_bankroll
    cumulative_pnl = 0
    context = {}

    for idx, row in data.iterrows():
        signal = strategy_fn(row, context)

        if signal['action'] == 'SKIP':
            continue

        # Cap bet size at current bankroll
        bet_size = min(signal['size'], bankroll)
        if bet_size <= 0:
            continue

        # Determine outcome
        if signal['action'] == 'BUY_HOME':
            won = row.get('home_win', 0) == 1
            odds = row['home_odds']
        else:  # BUY_AWAY
            won = row.get('home_win', 0) == 0
            odds = row['away_odds']

        # Calculate P&L
        if won:
            pnl = bet_size * (odds - 1)
            outcome = 'WIN'
        else:
            pnl = -bet_size
            outcome = 'LOSS'

        cumulative_pnl += pnl
        bankroll += pnl

        trades.append({
            'timestamp': row['timestamp'],
            'game': row['game'],
            'action': signal['action'],
            'bet_size': bet_size,
            'odds': odds,
            'outcome': outcome,
            'pnl': pnl,
            'cumulative_pnl': cumulative_pnl,
            'bankroll': bankroll
        })

    return pd.DataFrame(trades)

# Cell 5: Run Example
data = load_backtest_data('2026-01-01', '2026-02-01')
results = backtest(data, example_strategy)

print(f"Total trades: {len(results)}")
print(f"Win rate: {(results['outcome'] == 'WIN').mean():.1%}")
print(f"Total P&L: ${results['pnl'].sum():,.2f}")
```

### 2. Strategy Interface Spec

Create `docs/reference/strategy-interface.md`:

```markdown
# Strategy Interface Specification

## Function Signature

```python
def my_strategy(row: pd.Series, context: dict = None) -> dict:
    pass
```

## Input: row

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Game time |
| game | str | "Home vs Away" |
| home_team | str | Home team name |
| away_team | str | Away team name |
| home_odds | float | Decimal odds |
| away_odds | float | Decimal odds |

## Output: dict

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| action | str | YES | 'BUY_HOME', 'BUY_AWAY', or 'SKIP' |
| confidence | float | YES | 0.0 to 1.0 |
| size | float | YES | Bet size in dollars |
| reason | str | NO | Explanation for logging |

## Example

```python
def gap_strategy(row, context=None):
    gap = row.get('gap', 0)
    if gap > 0.05:
        return {'action': 'BUY_HOME', 'confidence': 0.6, 'size': 100}
    return {'action': 'SKIP', 'confidence': 0, 'size': 0}
```
```

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Ben | He builds metrics, needs your results DataFrame format | Coordinate daily |
| Isameel | He tests your backtester, reports bugs | Give him access Wed |
| Mya | She creates test data for you | Get test data Tue |

---

## Resources

**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/

**Reference Code:**
- sports-betting library: https://github.com/georgedouzas/sports-betting
- Backtrader (general backtesting): https://www.backtrader.com/docu/

**Internal Docs:**
- Database connection: `docs/guides/connecting-to-database.md`
- CSV formats: `docs/reference/csv-formats.md` (from Dietrich)

**AI Tools:**
- Use Claude/ChatGPT for pandas questions
- Prompt: "Write a pandas function that..."

---

## Done Checklist

- [ ] `tools/backtester.ipynb` created and runs
- [ ] `load_backtest_data()` connects to Railway
- [ ] `backtest()` function works with example strategy
- [ ] Strategy interface documented
- [ ] Ben can import and use results DataFrame
- [ ] Isameel has run basic tests

---

## Thursday Presentation (2 min)

1. Run backtester end-to-end
2. Show results DataFrame
3. Show P&L and win rate output
4. Explain how to plug in a custom strategy
