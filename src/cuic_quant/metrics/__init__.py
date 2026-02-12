"""Performance metrics for backtest output."""

from __future__ import annotations

import math

import pandas as pd


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Return a numeric-only series (invalid entries dropped)."""
    return pd.to_numeric(series, errors="coerce").dropna()


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized Sharpe ratio from period returns."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than 0")

    clean_returns = _coerce_numeric(returns)
    if clean_returns.empty:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = clean_returns - rf_per_period
    std_return = float(excess_returns.std(ddof=1))
    if math.isclose(std_return, 0.0):
        return 0.0

    mean_return = float(excess_returns.mean())
    return float((mean_return / std_return) * math.sqrt(periods_per_year))


def calculate_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """Calculate max drawdown as max((peak - value) / peak).

    For periods with positive peaks, returns percentage drawdown as a decimal.
    For periods before any positive peak (early losses), returns the absolute
    drawdown from zero (the starting point of cumulative P&L).
    """
    curve = _coerce_numeric(cumulative_pnl)
    if curve.empty:
        return 0.0

    # Running peak should be at least 0 (cumulative P&L starts at 0)
    running_peak = curve.cummax().clip(lower=0)
    positive_peak_mask = running_peak > 0

    max_drawdown = 0.0

    # Percentage drawdown for periods with positive peaks
    if positive_peak_mask.any():
        valid_peaks = running_peak[positive_peak_mask]
        valid_values = curve[positive_peak_mask]
        pct_drawdowns = ((valid_peaks - valid_values) / valid_peaks).clip(lower=0)
        max_drawdown = max(max_drawdown, float(pct_drawdowns.max()))

    # Absolute drawdown for periods with peak = 0 (before first profit)
    zero_peak_mask = running_peak == 0
    if zero_peak_mask.any():
        # When peak is 0, absolute drawdown is -value (how far below zero)
        values_at_zero_peak = curve[zero_peak_mask]
        abs_drawdowns = (-values_at_zero_peak).clip(lower=0)
        max_drawdown = max(max_drawdown, float(abs_drawdowns.max()))

    return max_drawdown


def calculate_win_rate(outcomes: pd.Series) -> float:
    """Calculate win rate from WIN/LOSS outcomes."""
    normalized = outcomes.astype("string").str.upper().dropna()
    valid_outcomes = normalized[normalized.isin(["WIN", "LOSS"])]
    if valid_outcomes.empty:
        return 0.0

    wins = int((valid_outcomes == "WIN").sum())
    return float(wins / len(valid_outcomes))


def calculate_profit_factor(pnl: pd.Series) -> float:
    """Calculate gross profit divided by gross loss."""
    clean_pnl = _coerce_numeric(pnl)
    if clean_pnl.empty:
        return 0.0

    gross_profit = float(clean_pnl[clean_pnl > 0].sum())
    gross_loss = float(-clean_pnl[clean_pnl < 0].sum())
    if math.isclose(gross_loss, 0.0):
        return float("inf") if gross_profit > 0 else 0.0

    return float(gross_profit / gross_loss)


def calculate_all_metrics(trades_df: pd.DataFrame) -> dict[str, float | int]:
    """Calculate all required metrics from backtester trade output."""
    required_columns = ["pnl", "cumulative_pnl", "outcome"]
    missing_columns = [column for column in required_columns if column not in trades_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    pnl = _coerce_numeric(trades_df["pnl"])
    cumulative_pnl = trades_df["cumulative_pnl"]
    outcomes = trades_df["outcome"]

    # Brief spec: derive returns from pnl for Sharpe input.
    returns = pnl

    return {
        "total_trades": int(len(trades_df)),
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": float(pnl.sum()) if not pnl.empty else 0.0,
        "sharpe_ratio": calculate_sharpe_ratio(returns),
        "max_drawdown": calculate_max_drawdown(cumulative_pnl),
        "profit_factor": calculate_profit_factor(pnl),
    }


__all__ = [
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_all_metrics",
]
