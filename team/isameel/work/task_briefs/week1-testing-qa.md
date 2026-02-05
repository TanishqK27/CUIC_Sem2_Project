# Week 1: Testing & QA

**Owner:** Isameel
**Deadline:** Thursday Feb 12
**Priority:** MEDIUM — ensures things actually work

---

## Your Role

You are the **tester**. When James builds the backtester and Ben builds metrics, YOU verify they work correctly. You find bugs before they cause problems.

**MINIMAL CODING** — mostly running other people's code and documenting results.

---

## DON'T WAIT - Create Test Data Now

You can prepare your test cases before James/Ben deliver. Create dummy data matching the expected formats.

### Dummy Backtester Input (what James expects)
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# This is what goes INTO the backtester
test_input = pd.DataFrame({
    'timestamp': [datetime(2026, 1, 1) + timedelta(days=i) for i in range(10)],
    'game': [f"Team{i*2} vs Team{i*2+1}" for i in range(10)],
    'home_team': [f"Team{i*2}" for i in range(10)],
    'away_team': [f"Team{i*2+1}" for i in range(10)],
    'home_odds': [2.0] * 10,
    'away_odds': [2.0] * 10,
    'home_win': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],  # Alternating for easy testing
})
```

### Dummy Backtester Output (what James produces / Ben consumes)
```python
# This is what comes OUT of the backtester
test_output = pd.DataFrame({
    'timestamp': [...],
    'game': [...],
    'action': ['BUY_HOME', 'BUY_AWAY', ...],
    'bet_size': [100.0, 100.0, ...],
    'odds': [2.0, 2.0, ...],
    'outcome': ['WIN', 'LOSS', ...],
    'pnl': [100.0, -100.0, ...],
    'cumulative_pnl': [100.0, 0.0, ...],
    'bankroll': [10100.0, 10000.0, ...],
})
```

**When James/Ben deliver, their code should work with these formats. If it doesn't, that's a bug.**

---

## This Week's Deliverables

### 1. Test James's Backtester

Once James gives you access (Wed), run these tests:

**Test 1: Basic Run**
```python
# In tools/backtester.ipynb or a test notebook

# Load test data from Mya
test_data = pd.read_csv('data/test_games.csv')

# Run with simple strategy
def always_home(row, context=None):
    return {'action': 'BUY_HOME', 'confidence': 0.5, 'size': 100}

results = backtest(test_data, always_home)

# Check output
print(f"Trades: {len(results)}")
print(f"Columns: {results.columns.tolist()}")
print(results.head())
```

**Test 2: Does it calculate correctly?**
- Count trades: should match number of games (since always betting)
- Win rate: should be ~55% (matches test data home win rate)
- P&L: wins should be positive, losses negative

**Test 3: Edge Cases**
```python
# Empty data
results = backtest(pd.DataFrame(), always_home)
# Should return empty DataFrame, NOT crash

# Skip strategy
def always_skip(row, context=None):
    return {'action': 'SKIP', 'confidence': 0, 'size': 0}

results = backtest(test_data, always_skip)
# Should have 0 trades
```

### 2. Test Ben's Metrics

Once Ben gives you access (Wed), test:

```python
from cuic_quant.metrics import calculate_all_metrics

# Use James's results
metrics = calculate_all_metrics(results)
print(metrics)

# Check values make sense:
# - total_trades > 0
# - win_rate between 0 and 1
# - sharpe_ratio is a number (not NaN)
# - max_drawdown between 0 and 1
```

### 3. Document All Bugs

Create `team/isameel/work/notes/bug-report.md`:

```markdown
# Bug Report - Week 1

## Backtester Bugs

### Bug 1: [Title]
- **Found:** [date]
- **Severity:** High/Medium/Low
- **Steps to reproduce:**
  1. ...
  2. ...
- **Expected:** ...
- **Actual:** ...
- **Reported to:** James
- **Status:** Open/Fixed

### Bug 2: ...

## Metrics Bugs

### Bug 1: ...

## Passed Tests

| Test | Component | Result |
|------|-----------|--------|
| Basic run | Backtester | ✓ Pass |
| Empty data | Backtester | ✓ Pass |
| ... | ... | ... |
```

### 4. Test Checklist

Track what you've tested:

```markdown
# Testing Checklist

## Backtester Tests
- [ ] Can import backtester
- [ ] Can load test data
- [ ] Basic strategy runs
- [ ] Results DataFrame has correct columns
- [ ] Trade count is correct
- [ ] P&L calculation looks right
- [ ] Empty data doesn't crash
- [ ] Skip strategy produces 0 trades
- [ ] Bankroll tracking works

## Metrics Tests
- [ ] Can import metrics module
- [ ] calculate_all_metrics() runs
- [ ] Returns correct keys
- [ ] Values are reasonable
- [ ] Empty data returns zeros (not crash)
```

---

## Who You Work With

| Person | Your Job | When |
|--------|----------|------|
| James | Test his backtester, report bugs | Wed-Thu |
| Ben | Test his metrics, report bugs | Wed-Thu |
| Mya | Get test data from her | Tue-Wed |

---

## Resources

**How to Run Notebooks:**
```bash
cd /path/to/project
jupyter lab
# Open tools/backtester.ipynb
```

**How to Report Bugs:**
1. Write exact steps to reproduce
2. Show expected vs actual
3. Tell the owner immediately

**AI Tools:**
- Use Claude: "Is this output correct for a 55% win rate strategy?"

---

## Done Checklist

- [ ] Got test data from Mya
- [ ] Ran basic backtester tests
- [ ] Ran edge case tests
- [ ] Tested metrics module
- [ ] Documented all bugs found
- [ ] Reported bugs to owners
- [ ] Testing checklist completed

---

## Thursday Presentation (1 min)

1. How many tests run
2. How many bugs found (if any)
3. Confirm backtester and metrics are working
