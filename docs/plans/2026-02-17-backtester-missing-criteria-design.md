# Backtester Missing Criteria — Design Doc

**Date:** 2026-02-17
**Author:** James
**Status:** Approved

## Problem

The backtester is missing several requirements from the task brief:

1. Kelly criterion integration (module exists but not connected)
2. Transaction cost modeling (no cost deduction in PnL)
3. Notebook assumptions/limitations documentation
4. Strategy markdown/code inconsistency
5. Edge case test gaps (financial extremes)
6. No conclusion cell in notebook

CLV (Closing Line Value) is deferred — our data has no closing odds columns.

## Approach

**Approach A (selected):** Add optional parameters directly to `backtest()`. Backwards-compatible, simple, matches existing code style.

Rejected alternatives:
- Approach B (BacktestConfig dataclass) — too much indirection for current needs
- Approach C (wrapper functions) — duplicated logic, confusing API

## Design

### 1. Transaction Cost Modeling

Add two optional parameters to `backtest()`:

```python
def backtest(
    data, strategy_fn, initial_bankroll=10000.0,
    cost_pct=0.0,   # percentage deducted from winning payouts
    cost_flat=0.0,   # flat dollar fee per trade
):
```

PnL formula with costs:
```
WIN:  pnl = bet_size * (odds - 1) * (1 - cost_pct) - cost_flat
LOSS: pnl = -bet_size - cost_flat
```

Both default to 0.0 — existing behavior unchanged. The validator
(`validate_backtest_results`) must also accept `cost_pct` and `cost_flat`
so it can verify PnL formulas with costs applied.

### 2. Kelly Criterion Integration

**Part A — backtest() parameters:**

```python
def backtest(
    ...,
    position_sizing=None,  # None = use strategy's size, "kelly" = Kelly sizing
    kelly_fraction=0.5,    # fractional Kelly (half-Kelly default)
):
```

When `position_sizing="kelly"`:
- Strategy's `confidence` field is used as `win_probability`
- Bet size = `calculate_kelly_fraction(confidence, odds, kelly_fraction) * bankroll`
- Strategy's `size` field is ignored
- If strategy doesn't return `confidence`, fall back to strategy's `size`

**Part B — Example strategy:**

New `kelly_bet_home()` strategy that returns meaningful `confidence` values
(implied probability + small edge), designed to work with Kelly sizing.

### 3. Notebook Documentation

**Fix strategy inconsistency:**
- Change cell-6 markdown to reference `always_bet_home`
- Change cell-7 code to `strategy = always_bet_home`

**Add assumptions/limitations markdown cell** (after title cell):
- Odds taken at face value (no slippage/liquidity)
- Data is synthetic (dummy_backtest_input.csv)
- Single bet per game, no parlays
- No CLV (future enhancement — needs closing odds)
- Transaction costs optional, default 0

**Add conclusion cell** at notebook end:
- Recap key results
- Note strategy used
- Point to strategy-interface.md for custom strategies

### 4. Edge Case Tests

Add to `tests/test_backtester_backend.py`:

| Test | What it covers |
|------|---------------|
| `test_extreme_high_odds` | Odds of 100.0 — verify PnL doesn't overflow |
| `test_extreme_low_odds` | Odds of 1.001 — verify tiny payout rounds correctly |
| `test_zero_initial_bankroll` | `initial_bankroll=0` — returns empty DataFrame |
| `test_invalid_action_string` | Strategy returns `action="INVALID"` — skipped |
| `test_all_wins` | Every game won — verify final bankroll |
| `test_all_losses` | Every game lost — verify bankroll hits zero |
| `test_cost_pct_applied` | Verify WIN pnl reduced by cost_pct |
| `test_cost_flat_applied` | Verify flat fee deducted from every trade |
| `test_kelly_sizing` | Verify Kelly sizes bets based on confidence |

## Files Changed

| File | Change |
|------|--------|
| `src/cuic_quant/backtest/backtester_backend.py` | Add cost params + Kelly params to `backtest()`, add `kelly_bet_home()`, update validator |
| `src/cuic_quant/backtest/__init__.py` | Export `kelly_bet_home` |
| `tools/backtester.ipynb` | Fix strategy, add assumptions/limitations cell, add conclusion cell |
| `tests/test_backtester_backend.py` | Add 9 new edge case + feature tests |

## Interface Impact

All new parameters have defaults matching current behavior. No existing
callers break. Ben's metrics and Ismaeel's tests are unaffected.
