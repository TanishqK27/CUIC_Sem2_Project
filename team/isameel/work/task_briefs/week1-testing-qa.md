# Week 1: Testing & QA

**Owner:** Isameel
**Deadline:** Thursday Feb 12
**Priority:** MEDIUM — ensures things actually work

---

## Your Role

You are the **tester**. When James builds the backtester and Ben builds metrics, YOU verify they work correctly. You find bugs before they cause problems.

**MINIMAL CODING** — mostly running other people's code and documenting results.

---

## ⚠️ DO NOT WAIT FOR JAMES OR BEN — START MONDAY

**You have zero dependencies. Create test cases and dummy data on Day 1.**

### Dummy Backtester Input (7 columns)

| Column | Type | Example |
|--------|------|---------|
| timestamp | datetime | 2026-01-01 |
| game | str | "Lakers vs Celtics" |
| home_team | str | "Lakers" |
| away_team | str | "Celtics" |
| home_odds | float | 2.0 |
| away_odds | float | 2.0 |
| home_win | int | 1 or 0 |

**Save as:** `data/test_backtest_input.csv` (10 rows, alternating home_win 1/0)

### Dummy Backtester Output (9 columns)

| Column | Type | Example |
|--------|------|---------|
| timestamp | datetime | 2026-01-01 |
| game | str | "Lakers vs Celtics" |
| action | str | "BUY_HOME" or "BUY_AWAY" |
| bet_size | float | 100.0 |
| odds | float | 2.0 |
| outcome | str | "WIN" or "LOSS" |
| pnl | float | 100.0 or -100.0 |
| cumulative_pnl | float | running total |
| bankroll | float | 10000 + cumulative_pnl |

**Save as:** `data/test_backtest_output.csv` (10 rows matching input)

**Create both files Monday-Tuesday.** When James/Ben deliver, their code must match these formats exactly — any mismatch is a bug.

---

## This Week's Deliverables

### 1. Test James's Backtester

Run these tests as soon as James has code (don't wait for "done"):

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

**Required Reading:**
- File structure: `docs/SOPs/file-structure.md`
- Modularity: `docs/SOPs/modularity-upgrades.md`
- Team SOPs: `docs/SOPs/team-sops.md`


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
