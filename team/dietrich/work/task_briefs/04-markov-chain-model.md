# Task: Markov Chain Model for Price Gaps

**Owner:** Dietrich
**Deadline:** Feb 19 (Week 2) — research in Week 1, build in Week 2
**Priority:** High — core modeling task

---

## What You're Building

A Markov chain model that predicts how Polymarket vs Sportsbook price gaps evolve over time. The hypothesis: if we can predict whether a gap will widen or narrow, we can trade profitably.

---

## Why This Matters

You already have 90K+ price snapshots showing how gaps move. A Markov model captures the transition dynamics — "if gap is currently +5%, what's the probability it goes to +3% vs +7%?"

This is novel research that could be the core of our trading strategy.

---

## Exactly What You Must Deliver

### 1. State Definition

Define discrete states for the price gap. Example:

```
State 1: Large negative gap (PM much higher than SB) — gap < -5%
State 2: Small negative gap — gap between -5% and -2%
State 3: Neutral — gap between -2% and +2%
State 4: Small positive gap — gap between +2% and +5%
State 5: Large positive gap (SB much higher than PM) — gap > +5%
```

You decide the exact thresholds based on data exploration.

### 2. Transition Matrix

Calculate the transition probability matrix from your existing data:

```
P(next_state | current_state)

Example output:
           State1  State2  State3  State4  State5
State1     0.70    0.20    0.08    0.02    0.00
State2     0.15    0.50    0.30    0.05    0.00
State3     0.02    0.20    0.56    0.20    0.02
State4     0.00    0.05    0.30    0.50    0.15
State5     0.00    0.02    0.08    0.20    0.70
```

### 3. Trading Signal

Define a trading rule based on the model:

```python
def markov_signal(current_gap: float, transition_matrix: np.array) -> str:
    """
    Returns 'BUY_PM', 'BUY_SB', or 'HOLD' based on expected gap movement.

    Logic: If gap is expected to narrow, bet on convergence.
    """
    pass
```

### 4. Evaluation

Answer these questions in your notebook:
- Does the gap actually follow a Markov process? (test memorylessness)
- What's the stationary distribution? (where do gaps end up long-term)
- Backtest: if you traded on the Markov signals, what's the P&L?

---

## Done Checklist

- [ ] States defined and justified
- [ ] Transition matrix calculated from real data
- [ ] Visualization of transition probabilities
- [ ] Trading signal function implemented
- [ ] Backtest results (P&L, win rate)
- [ ] Notebook with full methodology documented
- [ ] Conclusions: does this model have edge?

---

## What You Will Present (Thursday Feb 19)

**Show the notebook with:**
1. Your state definitions (30 sec)
2. The transition matrix heatmap (30 sec)
3. Backtest P&L curve (1 min)
4. Conclusion: does it work? (30 sec)

**Duration:** 3 minutes max

---

## Resources

- Your existing price_snapshots data in Railway DB
- Existing mean reversion code: `src/cuic_quant/strategies/mean_reversion.py`
- DataCamp Markov tutorial: https://www.datacamp.com/tutorial/markov-chains-python-tutorial
- NFL Markov example: https://github.com/flancast90/NFL_Markov_Predictor

---

## Who To Ask If Stuck

1. Google "Markov chain Python tutorial"
2. Andrii — statistical methodology
3. Tan — how this fits into the backtester
