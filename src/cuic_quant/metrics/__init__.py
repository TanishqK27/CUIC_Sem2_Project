"""Performance metrics for backtest output."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Return a numeric-only series (invalid entries dropped)."""
    return pd.to_numeric(series, errors="coerce").dropna()


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Extended metrics
# ---------------------------------------------------------------------------

def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate annualised Sortino ratio (penalises only downside volatility).

    Formula:
        Sortino = (mean_excess_return / downside_std) * sqrt(periods_per_year)

    where downside_std = std of returns below the risk-free rate.

    Args:
        returns: Series of per-period returns (P&L values).
        risk_free_rate: Annual risk-free rate.
        periods_per_year: Annualisation factor.

    Returns:
        Annualised Sortino ratio.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than 0")

    clean = _coerce_numeric(returns)
    if clean.empty:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess = clean - rf_per_period
    downside = excess[excess < 0]

    if downside.empty:
        return float("inf") if float(excess.mean()) > 0 else 0.0

    downside_std = float(np.sqrt((downside ** 2).mean()))
    if math.isclose(downside_std, 0.0):
        return 0.0

    return float((float(excess.mean()) / downside_std) * math.sqrt(periods_per_year))


def calculate_calmar_ratio(
    pnl: pd.Series,
    initial_bankroll: float = 10000.0,
    periods_per_year: int = 252,
) -> float:
    """Calculate Calmar ratio = annualised return / max drawdown.

    Formula:
        Calmar = annualised_return / max_drawdown

    where annualised_return = (total_pnl / initial_bankroll) * (periods_per_year / n).

    Args:
        pnl: Per-trade P&L series.
        initial_bankroll: Starting capital.
        periods_per_year: Annualisation factor.

    Returns:
        Calmar ratio.  Returns 0.0 if max drawdown is zero.
    """
    clean = _coerce_numeric(pnl)
    if clean.empty:
        return 0.0

    cum_pnl = clean.cumsum()
    max_dd = calculate_max_drawdown(cum_pnl, initial_bankroll)
    if math.isclose(max_dd, 0.0):
        return 0.0

    n = len(clean)
    total_return = float(clean.sum()) / initial_bankroll
    annualised_return = total_return * (periods_per_year / n)

    return float(annualised_return / max_dd)


def calculate_clv(
    trades_df: pd.DataFrame,
    closing_odds_col: str = "closing_odds",
    opening_odds_col: str = "odds",
) -> float:
    """Calculate Closing Line Value (CLV).

    CLV measures whether you consistently beat the closing odds (the most
    efficient market price).  Positive CLV is strong evidence of genuine
    edge rather than luck.

    Formula:
        CLV per bet = implied_prob(closing) - implied_prob(opening)
        Mean CLV = mean over all bets

    Args:
        trades_df: Trades DataFrame.  Must have opening odds column and
            ideally a closing odds column.
        closing_odds_col: Column name for closing odds.
        opening_odds_col: Column name for odds at time of bet.

    Returns:
        Mean CLV as a decimal.  Positive = beating the close.
        Returns NaN if closing odds not available.
    """
    if closing_odds_col not in trades_df.columns:
        return float("nan")

    open_odds = pd.to_numeric(trades_df[opening_odds_col], errors="coerce")
    close_odds = pd.to_numeric(trades_df[closing_odds_col], errors="coerce")

    valid = open_odds.notna() & close_odds.notna() & (open_odds > 1) & (close_odds > 1)
    if valid.sum() == 0:
        return float("nan")

    open_implied = 1.0 / open_odds[valid]
    close_implied = 1.0 / close_odds[valid]
    clv = close_implied - open_implied
    return float(clv.mean())


def calculate_roi(pnl: pd.Series, stakes: pd.Series) -> float:
    """Calculate Return on Investment = total_pnl / total_staked.

    Args:
        pnl: Per-trade P&L series.
        stakes: Per-trade stake series.

    Returns:
        ROI as a decimal (e.g. 0.05 = 5%).
    """
    clean_pnl = _coerce_numeric(pnl)
    clean_stakes = _coerce_numeric(stakes)

    total_staked = float(clean_stakes.sum())
    if math.isclose(total_staked, 0.0):
        return 0.0

    return float(clean_pnl.sum()) / total_staked


def calculate_brier_score(
    model_probs: pd.Series,
    outcomes: pd.Series,
) -> float:
    """Calculate the Brier Score for probabilistic forecast quality.

    Formula:
        BS = mean((p_i - o_i)^2)

    where p_i = model probability, o_i = actual outcome (0 or 1).
    Lower is better; a random model scores ~0.25.

    Args:
        model_probs: Series of model probabilities P(home_win).
        outcomes: Series of actual outcomes (1 = home win, 0 = away win).

    Returns:
        Brier score.  Returns NaN on empty input.
    """
    probs = pd.to_numeric(model_probs, errors="coerce")
    outs = pd.to_numeric(outcomes, errors="coerce")
    valid = probs.notna() & outs.notna()
    if valid.sum() == 0:
        return float("nan")
    return float(((probs[valid] - outs[valid]) ** 2).mean())


def calculate_log_loss(
    model_probs: pd.Series,
    outcomes: pd.Series,
    eps: float = 1e-15,
) -> float:
    """Calculate log loss (binary cross-entropy) for forecast quality.

    Formula:
        LL = -mean(o_i * log(p_i) + (1-o_i) * log(1-p_i))

    Lower is better; a random model scores ~ln(2) = 0.693.

    Args:
        model_probs: Series of model probabilities P(home_win).
        outcomes: Series of actual outcomes (1 or 0).
        eps: Clipping value to avoid log(0).

    Returns:
        Log loss.  Returns NaN on empty input.
    """
    probs = pd.to_numeric(model_probs, errors="coerce").clip(eps, 1 - eps)
    outs = pd.to_numeric(outcomes, errors="coerce")
    valid = probs.notna() & outs.notna()
    if valid.sum() == 0:
        return float("nan")

    p = probs[valid].values
    o = outs[valid].values
    ll = -(o * np.log(p) + (1 - o) * np.log(1 - p))
    return float(ll.mean())


def calculate_kelly_growth_rate(
    model_probs: pd.Series,
    odds: pd.Series,
    kelly_fractions: pd.Series,
) -> float:
    """Calculate expected log growth rate under the Kelly criterion.

    Formula (per bet):
        G_i = p_i * log(1 + b_i * f_i) + (1 - p_i) * log(1 - f_i)

    where b_i = odds_i - 1, f_i = kelly_fraction.
    Mean G across all bets is the expected log growth rate.

    Args:
        model_probs: P(win) per trade.
        odds: Decimal odds per trade.
        kelly_fractions: Bet fraction per trade (stake / bankroll).

    Returns:
        Mean expected log growth rate per bet.
    """
    p = pd.to_numeric(model_probs, errors="coerce")
    o = pd.to_numeric(odds, errors="coerce")
    f = pd.to_numeric(kelly_fractions, errors="coerce")

    valid = p.notna() & o.notna() & f.notna() & (o > 1) & (f > 0) & (f < 1)
    if valid.sum() == 0:
        return float("nan")

    p_v = p[valid].values
    b_v = (o[valid] - 1).values
    f_v = f[valid].values

    growth = p_v * np.log(1 + b_v * f_v) + (1 - p_v) * np.log(1 - f_v)
    return float(growth.mean())


# ---------------------------------------------------------------------------
# Comprehensive metrics calculation
# ---------------------------------------------------------------------------

def calculate_all_metrics(trades_df: pd.DataFrame) -> dict[str, float | int]:
    """Calculate all required metrics from backtester trade output."""
    required_columns = ["pnl", "cumulative_pnl", "outcome"]
    missing_columns = [column for column in required_columns if column not in trades_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    pnl = _coerce_numeric(trades_df["pnl"])
    cumulative_pnl = trades_df["cumulative_pnl"]
    outcomes = trades_df["outcome"]

    returns = pnl

    initial_bankroll = 10000.0
    if "bankroll" in trades_df.columns:
        first_bankroll = pd.to_numeric(trades_df["bankroll"], errors="coerce").dropna()
        if not first_bankroll.empty:
            initial_bankroll = float(first_bankroll.iloc[0])

    metrics: dict[str, float | int] = {
        "total_trades": int(len(trades_df)),
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": float(pnl.sum()) if not pnl.empty else 0.0,
        "sharpe_ratio": calculate_sharpe_ratio(returns),
        "sortino_ratio": calculate_sortino_ratio(returns),
        "calmar_ratio": calculate_calmar_ratio(pnl, initial_bankroll),
        "max_drawdown": calculate_max_drawdown(cumulative_pnl, initial_bankroll),
        "profit_factor": calculate_profit_factor(pnl),
    }

    if "stake" in trades_df.columns:
        metrics["roi"] = calculate_roi(trades_df["pnl"], trades_df["stake"])

    clv = calculate_clv(trades_df)
    if not math.isnan(clv):
        metrics["clv"] = clv

    if "model_prob" in trades_df.columns:
        outcome_binary = (
            trades_df["outcome"].astype(str).str.upper().map({"WIN": 1, "LOSS": 0})
        )
        metrics["brier_score"] = calculate_brier_score(
            trades_df["model_prob"], outcome_binary
        )
        metrics["log_loss"] = calculate_log_loss(
            trades_df["model_prob"], outcome_binary
        )

    if {"stake", "bankroll", "model_prob", "odds"}.issubset(trades_df.columns):
        stakes = pd.to_numeric(trades_df["stake"], errors="coerce")
        bankrolls = pd.to_numeric(trades_df["bankroll"], errors="coerce")
        pnl_col = pd.to_numeric(trades_df["pnl"], errors="coerce").fillna(0)
        pre_bankroll = (bankrolls - pnl_col).clip(lower=1e-8)
        kelly_fracs = (stakes / pre_bankroll).clip(0, 1)
        kgr = calculate_kelly_growth_rate(
            trades_df["model_prob"], trades_df["odds"], kelly_fracs
        )
        if not math.isnan(kgr):
            metrics["kelly_growth_rate"] = kgr

    return metrics


__all__ = [
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_calmar_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_clv",
    "calculate_roi",
    "calculate_brier_score",
    "calculate_log_loss",
    "calculate_kelly_growth_rate",
    "calculate_all_metrics",
]
