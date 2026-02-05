# Week 1: Backtester Core Engine

**Owner:** James
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL — all strategies run through this

---

## Your Role

Build THE backtester. Every model and strategy will be evaluated using your code.

---

## ⚠️ DO NOT WAIT FOR DATABASE — START FRIDAY

**You have zero dependencies. Build and test your entire backtester against dummy data.**

Create this dummy input DataFrame on Friday and develop against it:

| Column | Example Values |
|--------|----------------|
| timestamp | 2026-01-01, 2026-01-02, ... |
| game | "Lakers vs Celtics", ... |
| home_team | "Lakers", "Warriors", ... |
| away_team | "Celtics", "Heat", ... |
| home_odds | 1.95, 2.10, ... |
| away_odds | 2.05, 1.90, ... |
| home_win | 1, 0, 1, 0, ... |

**Save as:** `data/dummy_backtest_input.csv` (20+ rows)

Mya is also creating `data/test_games.csv` with the same format — get it from her Saturday and verify your code works with both files.

---

## Output Format (Ben Depends On This)

Your `backtest()` function MUST return a DataFrame with EXACTLY these columns:

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | When trade happened |
| game | str | "Home vs Away" |
| action | str | 'BUY_HOME' or 'BUY_AWAY' |
| bet_size | float | Dollars bet |
| odds | float | Decimal odds used |
| outcome | str | 'WIN' or 'LOSS' |
| pnl | float | Profit/loss for this trade |
| cumulative_pnl | float | Running total P&L |
| bankroll | float | Current bankroll after trade |

---

## Required Functions

### 1. `load_backtest_data(start_date, end_date) -> pd.DataFrame`

**Location:** `tools/backtester.ipynb`

**Parameters:**
- `start_date`: str, format "YYYY-MM-DD"
- `end_date`: str, format "YYYY-MM-DD"

**Returns:** DataFrame with columns:
- `timestamp`, `game`, `home_team`, `away_team`
- `home_odds`, `away_odds` (decimal)
- `home_win` (1 or 0, actual outcome)

**Flow:**
1. Connect to Railway using `DATABASE_URL`
2. Query sportsbook_matches JOIN sportsbook_odds
3. Return sorted by timestamp

---

### 2. `backtest(data, strategy_fn, initial_bankroll=10000) -> pd.DataFrame`

**Location:** `tools/backtester.ipynb`

**Parameters:**
- `data`: DataFrame from `load_backtest_data()`
- `strategy_fn`: Function matching strategy interface
- `initial_bankroll`: float, starting dollars

**Returns:** DataFrame with 9 columns (see Output Format above)

**Flow:**
1. Initialize: `bankroll = initial_bankroll`, `cumulative_pnl = 0`, `trades = []`
2. For each row in data:
   - Call `signal = strategy_fn(row)`
   - If SKIP, continue
   - Cap bet_size at current bankroll
   - Determine outcome based on action vs home_win
   - Calculate pnl (win: `bet_size * (odds - 1)`, loss: `-bet_size`)
   - Update cumulative_pnl, bankroll
   - Append trade dict to trades
3. Return `pd.DataFrame(trades)`

---

### 3. Strategy Interface (document in `docs/reference/strategy-interface.md`)

**Function signature:**
```
strategy_fn(row: pd.Series, context: dict = None) -> dict
```

**Input row columns:** timestamp, game, home_team, away_team, home_odds, away_odds

**Output dict keys:**
- `action`: 'BUY_HOME' | 'BUY_AWAY' | 'SKIP'
- `confidence`: float 0-1
- `size`: float (dollars)
- `reason`: str (optional)

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Ben | He builds metrics against your output format | Coordinate daily |
| Isameel | He tests your backtester | Give him access Tue |
| Mya | She creates test data for you | Get test data Sat |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`

**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/

**Reference:**
- sports-betting library: https://github.com/georgedouzas/sports-betting
- Backtrader: https://www.backtrader.com/docu/

---

## Done Checklist

- [ ] `tools/backtester.ipynb` created
- [ ] `load_backtest_data()` connects to Railway
- [ ] `backtest()` returns correct 9-column DataFrame
- [ ] Strategy interface documented
- [ ] Tested with example strategy

---

## Thursday Presentation (2 min)

1. Run backtester end-to-end
2. Show results DataFrame columns match spec
3. Show P&L and win rate
