# Task: Kelly Sizing Integration

**Owner:** James
**Deadline:** Feb 19 (Week 2)
**Priority:** Medium — enhances backtester

---

## What You're Building

Integrate the existing Kelly Criterion code into the backtester so strategies can use optimal position sizing.

---

## Why This Matters

Flat betting ($100 every time) is naive. Kelly sizing bets more when edge is higher, less when edge is lower. This is how real quant funds size positions.

---

## Exactly What You Must Deliver

### 1. Kelly Integration in Backtester

Update the backtester to support Kelly sizing:

```python
from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction

def backtest(
    data: pd.DataFrame,
    strategy_fn,
    initial_bankroll: float = 10000,
    kelly_fraction: float = 0.5,  # Half-Kelly is safer
    use_kelly: bool = True
) -> pd.DataFrame:
    """
    Run backtest with optional Kelly sizing.

    If use_kelly=True:
        bet_size = bankroll * kelly_fraction * kelly_optimal

    If use_kelly=False:
        bet_size = strategy's recommended size (flat betting)
    """
    pass
```

### 2. Kelly Calculation

For each bet, calculate optimal Kelly:

```python
def get_kelly_size(
    win_prob: float,      # Strategy's estimated win probability
    odds: float,          # Decimal odds offered
    bankroll: float,      # Current bankroll
    fraction: float = 0.5 # Kelly fraction (0.5 = half Kelly)
) -> float:
    """Return optimal bet size in dollars."""
    kelly = calculate_kelly_fraction(win_prob, odds)
    return bankroll * fraction * max(0, kelly)
```

### 3. Comparison

Show in the notebook:
- Backtest with flat $100 bets
- Backtest with Kelly sizing
- Compare P&L curves

---

## Done Checklist

- [ ] Backtester supports `use_kelly` parameter
- [ ] Uses existing `calculate_kelly_fraction` from `src/cuic_quant/strategies/`
- [ ] Configurable Kelly fraction (full, half, quarter)
- [ ] Comparison notebook showing flat vs Kelly
- [ ] Kelly sizing doesn't blow up bankroll (proper risk management)

---

## What You Will Present (Thursday Feb 19)

**Show comparison:**
1. P&L curve with flat betting
2. P&L curve with Kelly sizing
3. Which performed better and why

**Duration:** 2 minutes max

---

## Resources

- Existing Kelly code: `src/cuic_quant/strategies/kelly_criterion.py`
- Kelly Criterion explainer: `docs/reference/sports-betting.md`

---

## Who To Ask If Stuck

1. Read the existing Kelly code first
2. Ben — how this affects metrics
3. Tan — risk management questions
