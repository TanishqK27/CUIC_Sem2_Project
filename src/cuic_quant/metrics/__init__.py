"""Performance metrics for backtest output."""

from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Return a numeric-only series (invalid entries dropped)."""
    return pd.to_numeric(series, errors="coerce").dropna()


def _compute_periods_per_year(trades_df: pd.DataFrame) -> float:
    """Compute annualization factor from actual bet frequency.

    S1 fix: Returns are per-bet, not per-day. The correct annualization
    factor is √(actual bets per year), computed from the data's time span.

    Falls back to 365 if timestamps are unavailable or time span is zero.
    """
    if "timestamp" not in trades_df.columns:
        warnings.warn(
            "No 'timestamp' column — using periods_per_year=365 (assumes 1 bet/day). "
            "This may over- or under-state Sharpe/Sortino if bet frequency differs.",
            stacklevel=3,
        )
        return 365.0

    timestamps = pd.to_datetime(trades_df["timestamp"], errors="coerce").dropna()
    if len(timestamps) < 2:
        warnings.warn(
            "Fewer than 2 timestamps — using periods_per_year=365 (assumes 1 bet/day). "
            "Sharpe/Sortino may be inflated by up to 2.65x if actual frequency differs.",
            stacklevel=3,
        )
        return 365.0

    time_span_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
    if time_span_days <= 0:
        warnings.warn(
            "All bets share the same timestamp — using periods_per_year=365 "
            "(assumes 1 bet/day).",
            stacklevel=3,
        )
        return 365.0

    n_bets = len(timestamps)
    bets_per_year = (n_bets - 1) / (time_span_days / 365.25)

    # B4: Cap at 3650 (≈10 bets/day) to prevent inflated Sharpe/Sortino
    # from intraday or same-day multi-game scenarios
    max_periods = 3650.0
    if bets_per_year > max_periods:
        warnings.warn(
            f"Inferred {bets_per_year:.0f} bets/year from {n_bets} bets over "
            f"{time_span_days:.2f} days — capping at {max_periods:.0f} to prevent "
            f"inflated annualized ratios.",
            stacklevel=3,
        )
        bets_per_year = max_periods

    return bets_per_year


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 365.0,
) -> float:
    """Calculate annualized Sharpe ratio from period returns.

    Args:
        returns: Series of percentage returns per period.
        risk_free_rate: Annual risk-free rate. Default 0.0.
        periods_per_year: Number of betting periods per year. Accepts float
            for non-integer values (e.g., computed from actual bet frequency).

    Returns:
        Annualized Sharpe ratio. Returns 0.0 if no data or zero variance.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be greater than 0")

    clean_returns = _coerce_numeric(returns)
    if clean_returns.empty:
        return 0.0

    rf_per_period = risk_free_rate / periods_per_year
    excess_returns = clean_returns - rf_per_period
    std_return = float(excess_returns.std(ddof=1))
    if math.isnan(std_return) or std_return < 1e-12:
        return 0.0

    mean_return = float(excess_returns.mean())
    return float((mean_return / std_return) * math.sqrt(periods_per_year))


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 365.0,
) -> float:
    """Calculate annualized Sortino ratio from period returns.

    Uses downside deviation (sqrt of mean of squared negative returns)
    over ALL observations as the denominator, not std of losses only.

    Args:
        returns: Series of percentage returns per period.
        risk_free_rate: Annual risk-free rate. Default 0.0.
        periods_per_year: Number of betting periods per year. Accepts float
            for non-integer values (e.g., computed from actual bet frequency).

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

    if downside_deviation < 1e-12:
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

    if initial_bankroll <= 0:
        raise ValueError(
            f"initial_bankroll must be positive, got {initial_bankroll!r}."
        )

    equity = curve + initial_bankroll
    # Prepend the initial equity point (before any trade) so drawdowns on the
    # first trade are measured from the correct starting peak.
    equity_with_start = pd.concat(
        [pd.Series([float(initial_bankroll)]), equity],
        ignore_index=True,
    )
    running_peak = equity_with_start.cummax()
    drawdowns = ((running_peak - equity_with_start) / running_peak).clip(lower=0)
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


def calculate_kelly_growth_rate(trades_df: pd.DataFrame) -> float:
    """Calculate realized Kelly growth rate: mean of ln(1 + return_per_bet).

    The Kelly criterion maximizes the expected geometric growth rate of
    bankroll. This computes the *realized* growth rate from actual
    backtest returns so you can compare it to the theoretical optimum.

    Formula: G = (1/N) * sum(ln(1 + r_i))
    where r_i = pnl_i / bankroll_before_bet_i.

    Args:
        trades_df: DataFrame from backtest() with pnl and bankroll columns.

    Returns:
        Mean log growth rate per bet. Positive = growing, negative = shrinking.
        Returns 0.0 if insufficient data.
    """
    if "bankroll" not in trades_df.columns or "pnl" not in trades_df.columns:
        return 0.0

    bankroll = _coerce_numeric(trades_df["bankroll"])
    pnl = _coerce_numeric(trades_df["pnl"])

    if bankroll.empty or pnl.empty:
        return 0.0

    # bankroll is AFTER the trade, so bankroll_before = bankroll - pnl
    bankroll_before = bankroll - pnl
    valid_mask = bankroll_before > 1e-9

    if not valid_mask.any():
        return 0.0

    returns = pnl[valid_mask] / bankroll_before[valid_mask]
    # Clip returns to prevent log(0) when bankroll is wiped out
    returns_clipped = returns.clip(lower=-0.9999)
    log_returns = np.log(1 + returns_clipped)
    return float(log_returns.mean())


def calculate_clv(trades_df: pd.DataFrame) -> float:
    """Calculate average Closing Line Value.

    CLV measures how much edge you captured vs the closing line — the gold
    standard metric in sports betting. Positive CLV means you consistently
    got better prices than the final market odds.

    Formula: CLV = mean(bet_odds / closing_odds - 1)

    A CLV of 0.03 means you got 3% better odds than closing on average.
    CLV detects genuine skill in ~50 bets vs ~2000+ needed for P&L.

    Args:
        trades_df: DataFrame with odds and closing_odds columns.

    Returns:
        Average CLV as a decimal (0.03 = 3%). Returns NaN if closing_odds
        not available or all NaN.
    """
    if "closing_odds" not in trades_df.columns or "odds" not in trades_df.columns:
        return float("nan")

    odds = _coerce_numeric(trades_df["odds"])
    closing = _coerce_numeric(trades_df["closing_odds"])

    # Align indices and filter valid pairs (both non-NaN)
    valid = odds.index.intersection(closing.index)
    if len(valid) == 0:
        return float("nan")

    odds_valid = odds[valid]
    closing_valid = closing[valid]

    # Guard against zero/invalid closing odds
    mask = closing_valid > 1.0
    if not mask.any():
        return float("nan")

    clv = odds_valid[mask] / closing_valid[mask] - 1
    return float(clv.mean())


def calculate_brier_score(trades_df: pd.DataFrame) -> float:
    """Calculate Brier Score for probability calibration.

    Brier Score = (1/N) * sum((confidence - outcome)^2)
    where outcome is 1 for WIN, 0 for LOSS.

    Lower is better: 0.0 = perfect, 0.25 = random (p=0.5), 1.0 = worst.

    Confidence values outside [0, 1] are clamped with a warning.

    Args:
        trades_df: DataFrame with confidence and outcome columns.

    Returns:
        Brier Score. Returns NaN if confidence not available.
    """
    if "confidence" not in trades_df.columns:
        return float("nan")

    conf = _coerce_numeric(trades_df["confidence"])
    if conf.empty:
        return float("nan")

    outcomes = trades_df["outcome"]
    valid = conf.index.intersection(outcomes.index)
    if len(valid) == 0:
        return float("nan")

    actual = (outcomes[valid] == "WIN").astype(float)
    predicted = conf[valid]

    # Filter out NaN confidence values
    mask = predicted.notna()
    if not mask.any():
        return float("nan")

    p = predicted[mask]
    # Warn and clamp confidence outside [0, 1]
    if (p < 0).any() or (p > 1).any():
        warnings.warn(
            "Confidence values outside [0, 1] detected in Brier Score — "
            "clamping to valid range.",
            stacklevel=2,
        )
        p = p.clip(0.0, 1.0)

    return float(((p - actual[mask]) ** 2).mean())


def calculate_log_loss(trades_df: pd.DataFrame) -> float:
    """Calculate Log Loss (cross-entropy) for probability calibration.

    Log Loss = -(1/N) * sum(y * ln(p) + (1-y) * ln(1-p))
    where y is outcome (1=WIN, 0=LOSS) and p is confidence.

    Lower is better: 0.0 = perfect, 0.693 = random (p=0.5).
    Clips probabilities to [1e-15, 1-1e-15] to avoid log(0).

    Args:
        trades_df: DataFrame with confidence and outcome columns.

    Returns:
        Log Loss. Returns NaN if confidence not available.
    """
    if "confidence" not in trades_df.columns:
        return float("nan")

    conf = _coerce_numeric(trades_df["confidence"])
    if conf.empty:
        return float("nan")

    outcomes = trades_df["outcome"]
    valid = conf.index.intersection(outcomes.index)
    if len(valid) == 0:
        return float("nan")

    actual = (outcomes[valid] == "WIN").astype(float)
    predicted = conf[valid]

    mask = predicted.notna()
    if not mask.any():
        return float("nan")

    p = predicted[mask].clip(1e-15, 1 - 1e-15)
    y = actual[mask]
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def calculate_all_metrics(trades_df: pd.DataFrame) -> dict[str, float | int]:
    """Calculate all required metrics from backtester trade output.

    Args:
        trades_df: DataFrame from backtest() with columns pnl, cumulative_pnl,
            outcome, and optionally bankroll, bet_size, odds, timestamp.

    Returns:
        Dict with total_trades, win_rate, total_pnl, sharpe_ratio,
        sortino_ratio, max_drawdown, profit_factor, plus additional metrics
        (yield_on_turnover, yield_per_bet, avg_odds, total_wagered, calmar_ratio,
        bet_frequency) when the relevant columns are available.
    """
    required_columns = ["pnl", "cumulative_pnl", "outcome"]
    missing_columns = [column for column in required_columns if column not in trades_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    pnl = _coerce_numeric(trades_df["pnl"])
    cumulative_pnl = trades_df["cumulative_pnl"]
    outcomes = trades_df["outcome"]

    # Resolve initial_bankroll — single source of truth for all downstream metrics.
    # Step 1: authoritative source — set by backtest() in results.attrs
    initial_bankroll: float | None = trades_df.attrs.get("initial_bankroll")

    # Step 2: derivation fallback — for DataFrames not produced by backtest()
    #         bankroll[0] is the bankroll AFTER the first trade; subtracting pnl[0]
    #         gives the bankroll BEFORE the first trade.
    if initial_bankroll is None and "bankroll" in trades_df.columns:
        _bk = _coerce_numeric(trades_df["bankroll"])
        if not _bk.empty and not pnl.empty:
            initial_bankroll = float(_bk.iloc[0] - pnl.iloc[0])
            if initial_bankroll <= 0:
                raise ValueError(
                    f"Derived initial_bankroll ({initial_bankroll!r}) is not positive. "
                    "The bankroll column value at row 0 minus pnl at row 0 must be > 0."
                )

    # Step 3: strict fail — a wrong initial_bankroll silently corrupts drawdown,
    #         return_on_capital and calmar_ratio, so we surface it loudly.
    if initial_bankroll is None:
        raise ValueError(
            "calculate_all_metrics requires initial_bankroll. "
            "Either use a DataFrame produced by backtest() (which sets "
            "attrs['initial_bankroll'] automatically), or set "
            "trades_df.attrs['initial_bankroll'] = <value> before calling."
        )
    if initial_bankroll <= 0:
        raise ValueError(
            f"initial_bankroll must be positive, got {initial_bankroll!r}. "
            "A zero or negative starting bankroll makes drawdown and "
            "return_on_capital undefined."
        )

    # Compute percentage returns: pnl / bankroll_before_bet
    if "bankroll" in trades_df.columns:
        bankroll = _coerce_numeric(trades_df["bankroll"])
        if not bankroll.empty:
            bankroll_before = bankroll - pnl
            valid_mask = bankroll_before.abs() > 1e-9
            returns = pd.Series(0.0, index=pnl.index)
            returns[valid_mask] = pnl[valid_mask] / bankroll_before[valid_mask]
        else:
            returns = pnl  # fallback
    else:
        returns = pnl  # fallback if no bankroll column

    # S1 fix: Compute actual annualization factor from bet frequency
    periods_per_year = _compute_periods_per_year(trades_df)

    total_pnl = float(pnl.sum()) if not pnl.empty else 0.0
    max_dd = calculate_max_drawdown(cumulative_pnl, initial_bankroll)

    metrics: dict[str, float | int] = {
        "total_trades": int(len(trades_df)),
        "win_rate": calculate_win_rate(outcomes),
        "total_pnl": total_pnl,
        "sharpe_ratio": calculate_sharpe_ratio(returns, periods_per_year=periods_per_year),
        "sortino_ratio": calculate_sortino_ratio(returns, periods_per_year=periods_per_year),
        "max_drawdown": max_dd,
        "profit_factor": calculate_profit_factor(pnl),
    }

    # M1: Additional metrics from bet_size, odds, timestamp columns
    if "bet_size" in trades_df.columns:
        bet_sizes = _coerce_numeric(trades_df["bet_size"])
        total_wagered = float(bet_sizes.sum()) if not bet_sizes.empty else 0.0
        metrics["total_wagered"] = total_wagered
        if total_wagered > 0:
            # yield_on_turnover = total_pnl / total_wagered
            metrics["yield_on_turnover"] = total_pnl / total_wagered
        else:
            metrics["yield_on_turnover"] = 0.0
        # return_on_capital = total_pnl / initial_bankroll (the "real" ROI)
        if initial_bankroll > 0:
            metrics["return_on_capital"] = total_pnl / initial_bankroll
        else:
            metrics["return_on_capital"] = 0.0

        # yield_per_bet: mean of per-trade returns (mean of ratios, not ratio of means)
        if not bet_sizes.empty:
            valid_mask = bet_sizes > 0
            if valid_mask.any():
                per_trade_return = pnl[valid_mask] / bet_sizes[valid_mask]
                metrics["yield_per_bet"] = float(per_trade_return.mean())
            else:
                metrics["yield_per_bet"] = 0.0
        else:
            metrics["yield_per_bet"] = 0.0

    if "odds" in trades_df.columns:
        odds_series = _coerce_numeric(trades_df["odds"])
        metrics["avg_odds"] = float(odds_series.mean()) if not odds_series.empty else 0.0

    # Calmar ratio: annualized_return / max_drawdown
    if max_dd > 0:
        total_return = total_pnl / initial_bankroll if initial_bankroll > 0 else 0.0
        # Annualize using actual time span
        if "timestamp" in trades_df.columns:
            ts = pd.to_datetime(trades_df["timestamp"], errors="coerce").dropna()
            if len(ts) >= 2:
                span_years = (ts.max() - ts.min()).total_seconds() / (365.25 * 86400.0)
                if span_years > 0:
                    annualized_return = total_return / span_years
                else:
                    annualized_return = total_return
            else:
                annualized_return = total_return
        else:
            annualized_return = total_return
        metrics["calmar_ratio"] = annualized_return / max_dd
    else:
        metrics["calmar_ratio"] = 0.0

    # Bet frequency (bets per day)
    if "timestamp" in trades_df.columns:
        timestamps = pd.to_datetime(trades_df["timestamp"], errors="coerce").dropna()
        if len(timestamps) >= 2:
            span_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
            if span_days > 0:
                metrics["bet_frequency"] = (len(timestamps) - 1) / span_days

    # Store the annualization factor used (for transparency)
    metrics["periods_per_year"] = periods_per_year

    # M1: Kelly growth rate — realized geometric growth rate per bet
    metrics["kelly_growth_rate"] = calculate_kelly_growth_rate(trades_df)

    # M2: CLV — Closing Line Value (when closing_odds available)
    if "closing_odds" in trades_df.columns:
        clv = calculate_clv(trades_df)
        if not math.isnan(clv):
            metrics["clv"] = clv

    # M4: Brier Score and Log Loss (when confidence available)
    if "confidence" in trades_df.columns:
        brier = calculate_brier_score(trades_df)
        if not math.isnan(brier):
            metrics["brier_score"] = brier
        logloss = calculate_log_loss(trades_df)
        if not math.isnan(logloss):
            metrics["log_loss"] = logloss

    return metrics


__all__ = [
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "calculate_kelly_growth_rate",
    "calculate_clv",
    "calculate_brier_score",
    "calculate_log_loss",
    "calculate_all_metrics",
]
