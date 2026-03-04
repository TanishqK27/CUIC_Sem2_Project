# Design: B1 — past_games Timing Leak Guard

**Date:** 2026-03-04
**Author:** James
**Status:** Approved — ready for implementation

---

## Problem

`backtest()` in `engine.py` builds `context["past_games"]` using `data.loc[:row_idx].iloc[:-1]`
(line 290). This relies on the DataFrame's index ordering matching chronological order.
If a caller passes unsorted data (bypassing `load_backtest_data()`), `past_games` can include
rows from the future — a data leakage bug.

The engine never validates that input data is sorted by timestamp.

---

## Decision

Add a `ValueError` guard at the top of `backtest()` that rejects unsorted data.
Do NOT sort silently — that hides caller bugs.

---

## Design

After the required-columns check (line 226), add:

```python
# B1: Guard against unsorted data — past_games relies on index ordering
ts = pd.to_datetime(data["timestamp"], errors="coerce")
if not ts.is_monotonic_increasing:
    raise ValueError(
        "Input data must be sorted by timestamp (ascending). "
        "Use load_backtest_data() or sort before calling backtest()."
    )
```

`timestamp` is already a required column, so no need to check for its existence.

Test: 1 test passing unsorted data → `ValueError`, 1 test confirming sorted data works.

---

## Files Changed

| File | Change |
|---|---|
| `src/cuic_quant/backtest/engine.py` | Add timestamp monotonicity guard after line 226 |
| `tests/test_audit_fixes.py` | Add `TestPastGamesTimingLeak` (2 tests) |

---

## Out of Scope

- Sorting data inside `backtest()` (hides bugs)
- Changing `past_games` construction (index-based approach is correct given sorted input)
