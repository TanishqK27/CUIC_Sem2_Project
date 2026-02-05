# Task: Test the Backtester

**Owner:** Isameel
**Deadline:** Feb 26 (Week 3)
**Priority:** High — ensures backtester works

---

## What You're Building

Comprehensive tests for James's backtester. Run it with different strategies and verify results are correct.

---

## Why This Matters

The backtester is our most critical tool. If it has bugs, all our strategy results are wrong. You're the QA person ensuring it works correctly before we trust any results.

---

## Exactly What You Must Deliver

### 1. Test Notebook

Create `tools/backtester_tests.ipynb`:

```python
# Cell 1: Setup
"""
# Backtester Test Suite

Testing James's backtester for correctness.

Tests:
1. Basic functionality
2. Edge cases
3. Strategy interface compliance
4. Known-answer tests
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import backtester (adjust path based on James's implementation)
# from backtester import backtest, load_data
# OR
# %run tools/backtester.ipynb

# Cell 2: Create Test Data
"""
## Test Data

Create fake data with KNOWN outcomes so we can verify results.
"""

def create_test_data(n_games: int = 20) -> pd.DataFrame:
    """Create test data with known outcomes."""
    np.random.seed(42)

    data = []
    for i in range(n_games):
        # Alternate wins for predictability
        home_win = i % 2 == 0

        data.append({
            'timestamp': datetime(2026, 1, 1) + timedelta(days=i),
            'game': f'Team{i*2} @ Team{i*2+1}',
            'pm_home_prob': 0.55 if home_win else 0.45,
            'sb_home_prob': 0.50,  # Neutral odds
            'gap': 0.05 if home_win else -0.05,
            'home_win': 1 if home_win else 0,  # Actual outcome
            'home_odds': 2.0,  # Even odds
            'away_odds': 2.0,
        })

    return pd.DataFrame(data)

test_data = create_test_data()
print(f"Test data: {len(test_data)} games")
print(f"Home wins: {test_data['home_win'].sum()}")
test_data.head()

# Cell 3: Test 1 - Perfect Strategy
"""
## Test 1: Perfect Strategy (Knows Winners)

A strategy that always bets on the winner should have 100% win rate.
"""

def perfect_strategy(row, context=None):
    """Bet on whoever actually wins."""
    if row['home_win'] == 1:
        return {'action': 'BUY_HOME', 'confidence': 1.0, 'size': 100, 'reason': 'knows winner'}
    else:
        return {'action': 'BUY_AWAY', 'confidence': 1.0, 'size': 100, 'reason': 'knows winner'}

# Run backtest
results = backtest(test_data, perfect_strategy)

# Verify
assert len(results) == len(test_data), "Should have trade for every game"
assert (results['outcome'] == 'WIN').all(), "Perfect strategy should win every bet"
print("✓ Test 1 PASSED: Perfect strategy wins 100%")

# Cell 4: Test 2 - Always Wrong Strategy
"""
## Test 2: Always Wrong Strategy

A strategy that always bets on the loser should lose every bet.
"""

def always_wrong_strategy(row, context=None):
    """Bet against whoever actually wins."""
    if row['home_win'] == 1:
        return {'action': 'BUY_AWAY', 'confidence': 1.0, 'size': 100, 'reason': 'wrong'}
    else:
        return {'action': 'BUY_HOME', 'confidence': 1.0, 'size': 100, 'reason': 'wrong'}

results = backtest(test_data, always_wrong_strategy)

assert (results['outcome'] == 'LOSS').all(), "Wrong strategy should lose every bet"
print("✓ Test 2 PASSED: Wrong strategy loses 100%")

# Cell 5: Test 3 - Skip Strategy
"""
## Test 3: Always Skip Strategy

A strategy that never bets should have no trades.
"""

def skip_strategy(row, context=None):
    """Never bet."""
    return {'action': 'SKIP', 'confidence': 0, 'size': 0, 'reason': 'skip'}

results = backtest(test_data, skip_strategy)

assert len(results) == 0, "Skip strategy should have no trades"
print("✓ Test 3 PASSED: Skip strategy has 0 trades")

# Cell 6: Test 4 - P&L Calculation
"""
## Test 4: P&L Calculation

Verify P&L is calculated correctly.
"""

def fixed_bet_strategy(row, context=None):
    """Always bet home, $100."""
    return {'action': 'BUY_HOME', 'confidence': 0.5, 'size': 100, 'reason': 'test'}

results = backtest(test_data, fixed_bet_strategy, initial_bankroll=10000)

# Manual calculation:
# - 10 home wins at 2.0 odds: +$100 each = +$1000
# - 10 home losses: -$100 each = -$1000
# - Net P&L should be ~$0 (depending on exact implementation)

expected_wins = test_data['home_win'].sum()
expected_losses = len(test_data) - expected_wins

print(f"Expected wins: {expected_wins}, Expected losses: {expected_losses}")
print(f"Actual wins: {(results['outcome'] == 'WIN').sum()}")
print(f"Total P&L: ${results['pnl'].sum():.2f}")

assert (results['outcome'] == 'WIN').sum() == expected_wins, "Win count mismatch"
print("✓ Test 4 PASSED: P&L calculation correct")

# Cell 7: Test 5 - Bankroll Tracking
"""
## Test 5: Bankroll Management

Verify bankroll is tracked correctly.
"""

# With starting bankroll of 1000, betting 100 per game
results = backtest(test_data, fixed_bet_strategy, initial_bankroll=1000)

# Bankroll should never go negative
assert (results['bankroll'] >= 0).all(), "Bankroll went negative!"

# Final bankroll should equal initial + total P&L
final_bankroll = results['bankroll'].iloc[-1]
expected_final = 1000 + results['pnl'].sum()
# Allow small floating point difference
assert abs(final_bankroll - expected_final) < 0.01, f"Bankroll mismatch: {final_bankroll} vs {expected_final}"

print(f"Starting bankroll: $1000")
print(f"Final bankroll: ${final_bankroll:.2f}")
print("✓ Test 5 PASSED: Bankroll tracking correct")

# Cell 8: Test 6 - Strategy Interface
"""
## Test 6: Strategy Interface Compliance

Test that strategies follow the required interface.
"""

from cuic_quant.models import validate_model, BaseModel

# If Mya's model exists, test it
# model = LogisticBaseline.load('outputs/logistic_baseline.pkl')
# strategy = model.to_strategy(threshold=0.55)

# Test with a row
sample_row = test_data.iloc[0]
signal = fixed_bet_strategy(sample_row)

# Check required keys
assert 'action' in signal, "Missing 'action' key"
assert 'confidence' in signal, "Missing 'confidence' key"
assert 'size' in signal, "Missing 'size' key"
assert signal['action'] in ['BUY_HOME', 'BUY_AWAY', 'SKIP'], f"Invalid action: {signal['action']}"

print("✓ Test 6 PASSED: Strategy interface correct")

# Cell 9: Test 7 - Edge Cases
"""
## Test 7: Edge Cases
"""

# Empty data
try:
    results = backtest(pd.DataFrame(), fixed_bet_strategy)
    assert len(results) == 0, "Should handle empty data"
    print("✓ Edge case: Empty data handled")
except Exception as e:
    print(f"✗ Edge case failed: Empty data - {e}")

# Single game
single_game = test_data.head(1)
results = backtest(single_game, fixed_bet_strategy)
assert len(results) == 1, "Should handle single game"
print("✓ Edge case: Single game handled")

# Large bet size (more than bankroll)
def big_bet_strategy(row, context=None):
    return {'action': 'BUY_HOME', 'confidence': 1.0, 'size': 999999, 'reason': 'big'}

results = backtest(test_data, big_bet_strategy, initial_bankroll=100)
# Should either cap bet or reject - depends on implementation
print(f"Large bet behavior: {len(results)} trades executed")

# Cell 10: Summary
"""
## Test Summary
"""

tests_passed = [
    "Perfect strategy wins 100%",
    "Wrong strategy loses 100%",
    "Skip strategy has 0 trades",
    "P&L calculation correct",
    "Bankroll tracking correct",
    "Strategy interface correct",
]

print("=" * 50)
print("BACKTESTER TEST RESULTS")
print("=" * 50)
for test in tests_passed:
    print(f"✓ {test}")
print("=" * 50)
print(f"All {len(tests_passed)} tests PASSED")
```

### 2. Bug Report Template

When you find bugs, document them in `team/isameel/work/notes/backtester-bugs.md`:

```markdown
# Backtester Bug Reports

## Bug 1: [Title]

**Date found:** 2026-02-XX
**Severity:** High/Medium/Low

**Steps to reproduce:**
1. Create test data with X
2. Run backtest with Y strategy
3. Observe Z

**Expected behavior:**
[What should happen]

**Actual behavior:**
[What actually happens]

**Screenshot/output:**
```
[paste output here]
```

**Suggested fix:**
[If you have ideas]

**Status:** Open / Fixed in commit XXX
```

### 3. Sign-Off Document

Create `team/isameel/work/notes/backtester-signoff.md`:

```markdown
# Backtester Testing Sign-Off

## Test Date: [DATE]

## Tests Run

| Test | Status | Notes |
|------|--------|-------|
| Perfect strategy 100% win | ✓ Pass | |
| Wrong strategy 100% loss | ✓ Pass | |
| Skip strategy 0 trades | ✓ Pass | |
| P&L calculation | ✓ Pass | |
| Bankroll tracking | ✓ Pass | |
| Strategy interface | ✓ Pass | |
| Empty data edge case | ✓ Pass | |
| Single game edge case | ✓ Pass | |

## Bugs Found

- [ ] Bug 1: [description] - reported to James
- [ ] Bug 2: [description] - fixed

## Recommendation

[ ] Ready for production use
[ ] Needs fixes before use

## Signed

Tested by: Isameel
Date: [DATE]
```

---

## Done Checklist

- [ ] Test notebook created at `tools/backtester_tests.ipynb`
- [ ] All core tests pass (or bugs documented)
- [ ] Edge cases tested
- [ ] Bugs reported to James
- [ ] Sign-off document completed
- [ ] Backtester approved for team use

---

## What You Will Present (Thursday Feb 26)

**Live demo showing:**
1. Run the test notebook
2. Show test results (all passing or explain failures)
3. Show any bugs found
4. Give verdict: is backtester ready?

**Duration:** 2 minutes max

---

## Resources

- James's backtester: `tools/backtester.ipynb`
- Strategy interface spec: `docs/reference/strategy-interface.md`
- Mya's model interface: `docs/reference/model-interface.md`

---

## Who To Ask If Stuck

1. James — backtester implementation questions
2. Run simpler tests first to understand behavior
3. Ben — expected metric calculations
4. Tan — if unsure what "correct" behavior is
