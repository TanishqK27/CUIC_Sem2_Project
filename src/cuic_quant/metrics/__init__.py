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


def calculate_max_drawdown(
    cumulative_pnl: pd.Series,
    initial_bankroll: float = 10000.0,
) -> float:
    """Calculate max drawdown as max((peak - value) / peak) on the equity curve.

    Converts cumulative P&L to an equity curve (initial_bankroll + cumulative_pnl)
    so that drawdowns are always expressed as a fraction of peak equity, even for
    early-loss scenarios.

    Args:
        cumulative_pnl: Series of cumulative profit/loss values.
        initial_bankroll: Starting bankroll to anchor the equity curve.

    Returns:
        Max drawdown as a decimal between 0 and 1.
    """
    curve = _coerce_numeric(cumulative_pnl)
    if curve.empty:
        return 0.0

    equity = curve + initial_bankroll
    running_peak = equity.cummax()
    drawdowns = ((running_peak - equity) / running_peak).clip(lower=0)
    return float(drawdowns.max())


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

    # Use bankroll column if present, otherwise default
    initial_bankroll = 10000.0
    if "bankroll" in trades_df.columns:
        first_bankroll = pd.to_numeric(trades_df["bankroll"], errors="coerce").dropna()
        if not first_bankroll.empty:
            initial_bankroll = float(first_bankroll.iloc[0])

    return {
        "total_trades": int(len(trades_df)),
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": float(pnl.sum()) if not pnl.empty else 0.0,
        "sharpe_ratio": calculate_sharpe_ratio(returns),
        "max_drawdown": calculate_max_drawdown(cumulative_pnl, initial_bankroll),
        "profit_factor": calculate_profit_factor(pnl),
    }


__all__ = [
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_all_metrics",
]
