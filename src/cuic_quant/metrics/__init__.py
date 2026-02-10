"""Performance metrics for backtest trade logs."""

from __future__ import annotations

import math

import pandas as pd


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualized Sharpe ratio from period returns."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be > 0")

    clean_returns = pd.to_numeric(returns, errors="coerce").dropna()
    if clean_returns.empty:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = clean_returns - rf_per_period
    std_return = float(excess_returns.std(ddof=1))

    if math.isclose(std_return, 0.0):
        return 0.0

    mean_return = float(excess_returns.mean())
    sharpe = (mean_return / std_return) * math.sqrt(periods_per_year)
    return float(sharpe)


def calculate_max_drawdown(cumulative_pnl: pd.Series) -> float:
    """Calculate maximum drawdown from cumulative P&L series."""
    curve = pd.to_numeric(cumulative_pnl, errors="coerce").dropna()
    if curve.empty:
        return 0.0

    running_peak = curve.cummax()
    valid = running_peak > 0
    if not valid.any():
        return 0.0

    drawdowns = ((running_peak[valid] - curve[valid]) / running_peak[valid]).clip(lower=0)
    if drawdowns.empty:
        return 0.0

    return float(drawdowns.max())


def calculate_win_rate(outcomes: pd.Series) -> float:
    """Calculate fraction of winning trades from WIN/LOSS labels."""
    clean_outcomes = outcomes.astype("string").str.upper().dropna()
    if clean_outcomes.empty:
        return 0.0

    wins = (clean_outcomes == "WIN").sum()
    total = len(clean_outcomes)
    return float(wins / total)


def calculate_profit_factor(pnl: pd.Series) -> float:
    """Calculate gross profit divided by gross loss."""
    clean_pnl = pd.to_numeric(pnl, errors="coerce").dropna()
    if clean_pnl.empty:
        return 0.0

    gross_profit = float(clean_pnl[clean_pnl > 0].sum())
    gross_loss = float(-clean_pnl[clean_pnl < 0].sum())

    if math.isclose(gross_loss, 0.0):
        return float("inf") if gross_profit > 0 else 0.0

    return float(gross_profit / gross_loss)


def calculate_all_metrics(trades_df: pd.DataFrame) -> dict:
    """Calculate core backtest metrics from trade-level output."""
    required = ["pnl", "cumulative_pnl", "outcome"]
    missing = [col for col in required if col not in trades_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    pnl = pd.to_numeric(trades_df["pnl"], errors="coerce")
    cumulative_pnl = pd.to_numeric(trades_df["cumulative_pnl"], errors="coerce")
    outcomes = trades_df["outcome"]

    returns = pnl.dropna()

    total_trades = int(len(trades_df))
    total_pnl = float(pnl.sum()) if not pnl.dropna().empty else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": total_pnl,
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
