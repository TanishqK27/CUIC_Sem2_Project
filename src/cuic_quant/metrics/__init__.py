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


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 365,
) -> float:
    """Calculate annualized Sortino ratio from period returns.

    Uses downside deviation (sqrt of mean of squared negative returns)
    over ALL observations as the denominator, not std of losses only.

    Args:
        returns: Series of percentage returns per period.
        risk_free_rate: Annual risk-free rate. Default 0.0.
        periods_per_year: Number of betting periods per year. Default 365.

    Returns:
        Annualized Sortino ratio. Returns 0.0 if no data or no downside.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than 0")

    clean_returns = _coerce_numeric(returns)
    if clean_returns.empty:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = clean_returns - rf_per_period

    # Downside deviation: sqrt(mean(min(0, r_i)^2)) over ALL observations
    downside_returns = excess_returns.clip(upper=0.0)
    downside_deviation = float(math.sqrt((downside_returns**2).mean()))

    if math.isclose(downside_deviation, 0.0):
        return 0.0

    mean_excess = float(excess_returns.mean())
    return float((mean_excess / downside_deviation) * math.sqrt(periods_per_year))


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
    """Calculate all required metrics from backtester trade output.

    Args:
        trades_df: DataFrame from backtest() with columns pnl, cumulative_pnl,
            outcome, and optionally bankroll.

    Returns:
        Dict with total_trades, win_rate, total_pnl, sharpe_ratio,
        sortino_ratio, max_drawdown, profit_factor.
    """
    required_columns = ["pnl", "cumulative_pnl", "outcome"]
    missing_columns = [column for column in required_columns if column not in trades_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    pnl = _coerce_numeric(trades_df["pnl"])
    cumulative_pnl = trades_df["cumulative_pnl"]
    outcomes = trades_df["outcome"]

    # Compute percentage returns: pnl / bankroll_before_bet
    # bankroll_before_bet = bankroll - pnl (since bankroll is after the trade)
    initial_bankroll = 10000.0
    if "bankroll" in trades_df.columns:
        bankroll = _coerce_numeric(trades_df["bankroll"])
        if not bankroll.empty:
            initial_bankroll = float(bankroll.iloc[0])
            bankroll_before = bankroll - pnl
            # Guard against division by zero
            valid_mask = bankroll_before.abs() > 1e-9
            returns = pd.Series(0.0, index=pnl.index)
            returns[valid_mask] = pnl[valid_mask] / bankroll_before[valid_mask]
        else:
            returns = pnl  # fallback
    else:
        returns = pnl  # fallback if no bankroll column

    return {
        "total_trades": int(len(trades_df)),
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": float(pnl.sum()) if not pnl.empty else 0.0,
        "sharpe_ratio": calculate_sharpe_ratio(returns, periods_per_year=365),
        "sortino_ratio": calculate_sortino_ratio(returns, periods_per_year=365),
        "max_drawdown": calculate_max_drawdown(cumulative_pnl, initial_bankroll),
        "profit_factor": calculate_profit_factor(pnl),
    }


__all__ = [
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_all_metrics",
]
