# Week 1: Metrics Module

**Owner:** Ben
**Deadline:** Thursday Feb 12
**Priority:** HIGH — needed to evaluate any strategy

---

## Your Role

Build the metrics module. Calculate Sharpe ratio, max drawdown, win rate, etc. from backtester output.

---

## ⚠️ DO NOT WAIT FOR JAMES — START MONDAY

**You have zero dependencies. Build and test your entire module against dummy data.**

Create this dummy DataFrame on Day 1 and develop against it:

| Column | Example Values |
|--------|----------------|
| timestamp | 2026-01-01, 2026-01-02, ... |
| game | "Lakers vs Celtics", ... |
| action | "BUY_HOME", "BUY_AWAY" |
| bet_size | 100.0, 150.0, ... |
| odds | 1.95, 2.10, ... |
| outcome | "WIN", "LOSS" |
| pnl | 95.0, -150.0, ... |
| cumulative_pnl | 95.0, -55.0, ... |
| bankroll | 10095.0, 9945.0, ... |

**Save as:** `data/dummy_backtest_output.csv`

Your module must work with this format. When James delivers his backtester, it will output this exact format — plug and play.

---

## Required Functions

**Location:** `src/cuic_quant/metrics/__init__.py`

### 1. `calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252) -> float`

**Parameters:**
- `returns`: pd.Series of period returns
- `risk_free_rate`: float, annual risk-free rate
- `periods_per_year`: int, trading periods per year

**Returns:** float, annualized Sharpe ratio

**Formula:** `(mean_return - rf) / std_return * sqrt(periods_per_year)`

---

### 2. `calculate_max_drawdown(cumulative_pnl) -> float`

**Parameters:**
- `cumulative_pnl`: pd.Series of cumulative P&L values

**Returns:** float, max drawdown as decimal (0.15 = 15%)

**Formula:** `max((peak - value) / peak)` where peak is running maximum

---

### 3. `calculate_win_rate(outcomes) -> float`

**Parameters:**
- `outcomes`: pd.Series of 'WIN' or 'LOSS' strings

**Returns:** float, win rate as decimal (0.55 = 55%)

---

### 4. `calculate_profit_factor(pnl) -> float`

**Parameters:**
- `pnl`: pd.Series of individual trade P&Ls

**Returns:** float, gross profit / gross loss

**Edge cases:** Handle division by zero (all wins or all losses)

---

### 5. `calculate_all_metrics(trades_df) -> dict`

**Parameters:**
- `trades_df`: DataFrame with columns `pnl`, `cumulative_pnl`, `outcome`

**Returns:** dict with keys:
- `total_trades`: int
- `win_rate`: float
- `total_pnl`: float
- `sharpe_ratio`: float
- `max_drawdown`: float
- `profit_factor`: float

**Flow:**
1. Validate required columns exist
2. Calculate returns from pnl
3. Call each individual metric function
4. Return consolidated dict

---

## Module Structure

```
src/cuic_quant/metrics/
└── __init__.py    # All 5 functions + __all__ export
```

**Export:** All 5 functions in `__all__`

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| James | Get his output format, test with real output | Wed-Thu |
| Isameel | He tests your metrics | Thu |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`

**Libraries:**
- numpy: https://numpy.org/doc/
- pandas: https://pandas.pydata.org/docs/

**Reference:**
- empyrical (Quantopian metrics): https://github.com/quantopian/empyrical
- PyFolio: https://github.com/quantopian/pyfolio

---

## Done Checklist

- [ ] Module at `src/cuic_quant/metrics/__init__.py`
- [ ] All 5 functions implemented
- [ ] Edge cases handled (empty data, all wins, all losses)
- [ ] Test notebook at `tools/test_metrics.ipynb`
- [ ] Works with James's output format

---

## Thursday Presentation (2 min)

1. Import module: `from cuic_quant.metrics import calculate_all_metrics`
2. Run on backtester output
3. Show metrics dict
