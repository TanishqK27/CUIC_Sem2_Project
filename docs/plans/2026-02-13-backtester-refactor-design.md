# Backtester Refactor Design

**Date:** 2026-02-13
**Owner:** James
**Status:** Approved

---

## Problem

The backtester logic currently lives inline in `tools/backtester.ipynb`. All functions (`load_backtest_data`, `backtest`, `always_bet_home`) are defined inside notebook cells. This makes it impossible to import and reuse them from other modules, and there is no validation to verify results are correct.

## Solution

Extract all functions into `src/cuic_quant/backtest/backtester_backend.py`. Add a validation function. Rewrite the notebook as a thin caller with zero function definitions.

## Approach

**Direct Extract (Approach A):** Move existing functions as-is with the same signatures and logic. Add docstrings and the validator. No interface changes — downstream consumers (Ben's metrics, Ismaeel's tests) are unaffected.

---

## File: `src/cuic_quant/backtest/backtester_backend.py`

### Functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `load_backtest_data` | `(start_date: str, end_date: str, csv_path: str \| Path \| None = None) -> pd.DataFrame` | Load game data from Railway DB or CSV fallback |
| `backtest` | `(data: pd.DataFrame, strategy_fn: Callable, initial_bankroll: float = 10000.0) -> pd.DataFrame` | Core backtest loop, returns 9-column trade log |
| `always_bet_home` | `(row: pd.Series, context: dict \| None = None) -> dict` | Example strategy for testing |
| `validate_backtest_results` | `(results: pd.DataFrame, input_data: pd.DataFrame, initial_bankroll: float = 10000.0) -> dict` | Full validation suite |

Every function has a Google-style docstring explaining what it is, what it does, why it exists, and how it works.

### Validator Checks

**Category 1 — Schema Validation:**
- 9 required columns present with correct names
- Column types correct
- Actions only BUY_HOME or BUY_AWAY
- Outcomes only WIN or LOSS
- Bet sizes positive

**Category 2 — Math Correctness:**
- WIN pnl == bet_size * (odds - 1)
- LOSS pnl == -bet_size
- cumulative_pnl is running sum of pnl
- bankroll == initial_bankroll + cumulative_pnl at each row
- No bet exceeds available bankroll

**Category 3 — Data Leakage Detection:**
- Every game in results exists in input_data
- Outcomes match input data (BUY_HOME WIN → home_win == 1)
- Trades in chronological order
- Deterministic test: always_bet_home on dummy data matches expected output

**Return Value:**
```python
{
    "passed": bool,
    "checks_run": int,
    "checks_passed": int,
    "failures": list[str],
}
```

---

## File: `src/cuic_quant/backtest/__init__.py`

Updated to export: `load_backtest_data`, `backtest`, `always_bet_home`, `validate_backtest_results`.

---

## File: `tools/backtester.ipynb`

Rewritten as a thin caller. No function definitions. Structure:

1. Title + description
2. Imports from backtester_backend + config
3. Load data (call `load_backtest_data()`)
4. Define/import strategy
5. Run backtest (call `backtest()`)
6. Summary statistics
7. Validate results (call `validate_backtest_results()`)

---

## Data Files Used

- `data/dummy_backtest_input.csv` (25 rows, seed=99)
- `data/test_games.csv` (100 rows, seed=42, from Mya's generator)
- `data/dummy_backtest_output.csv` (expected output for deterministic validation)

---

## What Does NOT Change

- Output format (9 columns, same names, same types)
- Strategy interface (same function signature)
- Data file locations
- Downstream dependencies (Ben's metrics, Ismaeel's tests)
