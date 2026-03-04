"""Strategy comparison and ranking.

Given results from multiple strategies, this module:
  - Computes a summary metrics table for side-by-side comparison.
  - Ranks strategies by a chosen primary metric.
  - Detects anomalies (suspiciously high Sharpe, implausibly low drawdown,
    gaps in trade frequency) that may indicate data snooping or bugs.

Usage::

    from cuic_quant.backtest.comparison import compare_strategies

    results = {
        "LogReg":    logistic_trades_df,
        "RandomForest": rf_trades_df,
        "Baseline":  baseline_trades_df,
    }
    summary = compare_strategies(results)
    print(summary)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from cuic_quant.metrics import calculate_all_metrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core comparison
# ---------------------------------------------------------------------------

def compare_strategies(
    results: dict[str, pd.DataFrame],
    primary_metric: str = "sharpe_ratio",
) -> pd.DataFrame:
    """Build a side-by-side metrics table for multiple strategies.

    Args:
        results: Dict mapping strategy name -> trades DataFrame.
        primary_metric: Column to sort by (descending) in the output table.

    Returns:
        DataFrame indexed by strategy name, sorted by ``primary_metric``.
        Columns match the output of ``calculate_all_metrics`` plus
        additional fields: roi, yield_per_bet, avg_odds, bet_frequency.
    """
    rows = {}
    for name, trades in results.items():
        if trades is None or trades.empty:
            rows[name] = _empty_metrics_row()
            continue
        try:
            metrics = calculate_all_metrics(trades)
        except Exception as exc:
            logger.warning("Failed to compute metrics for '%s': %s", name, exc)
            rows[name] = _empty_metrics_row()
            continue

        # Extra metrics not in the base metrics module
        metrics.update(_extra_metrics(trades))
        rows[name] = metrics

    df = pd.DataFrame(rows).T

    # Sort by primary metric descending
    if primary_metric in df.columns:
        df = df.sort_values(primary_metric, ascending=False)

    return df


def _empty_metrics_row() -> dict[str, float | int]:
    return {
        "total_trades": 0,
        "win_rate": 0.0,
        "total_pnl": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "profit_factor": 0.0,
        "roi": 0.0,
        "yield_per_bet": 0.0,
        "avg_odds": 0.0,
        "bet_frequency": 0.0,
    }


def _extra_metrics(trades: pd.DataFrame) -> dict[str, float]:
    """Compute supplementary metrics not in the core metrics module."""
    extra: dict[str, float] = {}

    # ROI = total_pnl / total_staked
    if "stake" in trades.columns and "pnl" in trades.columns:
        stakes = pd.to_numeric(trades["stake"], errors="coerce").fillna(0)
        pnl = pd.to_numeric(trades["pnl"], errors="coerce").fillna(0)
        total_staked = float(stakes.sum())
        total_pnl = float(pnl.sum())
        extra["roi"] = total_pnl / total_staked if total_staked > 0 else 0.0

        # Yield per bet = mean(pnl / stake)
        yields = pnl / stakes.replace(0, np.nan)
        extra["yield_per_bet"] = float(yields.mean()) if not yields.isna().all() else 0.0
    else:
        extra["roi"] = 0.0
        extra["yield_per_bet"] = 0.0

    # Average odds
    if "odds" in trades.columns:
        odds = pd.to_numeric(trades["odds"], errors="coerce")
        extra["avg_odds"] = float(odds.mean()) if not odds.isna().all() else 0.0
    else:
        extra["avg_odds"] = 0.0

    # Bet frequency (bets per fold or bets per 100 games)
    if "fold" in trades.columns:
        n_folds = trades["fold"].nunique()
        extra["bet_frequency"] = len(trades) / n_folds if n_folds > 0 else float(len(trades))
    else:
        extra["bet_frequency"] = float(len(trades))

    return extra


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

_ANOMALY_THRESHOLDS = {
    "sharpe_ratio": 3.0,       # Annualised Sharpe > 3 is suspicious
    "max_drawdown": 0.005,     # Max drawdown < 0.5% on real data is suspicious
    "win_rate": 0.75,          # Win rate > 75% against the vig is suspicious
    "profit_factor": 5.0,      # Profit factor > 5 is suspicious
}


def detect_anomalies(
    results: dict[str, pd.DataFrame],
    thresholds: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Flag strategies with suspiciously extreme metric values.

    High values can indicate bugs (e.g., accidental lookahead bias),
    data snooping, or overfitting rather than genuine alpha.

    Args:
        results: Dict mapping strategy name -> trades DataFrame.
        thresholds: Override default anomaly thresholds.

    Returns:
        DataFrame with columns: strategy, metric, value, threshold, flagged.
    """
    thresholds = thresholds or _ANOMALY_THRESHOLDS
    summary = compare_strategies(results)

    flags = []
    for strategy in summary.index:
        for metric, threshold in thresholds.items():
            if metric not in summary.columns:
                continue
            val = summary.loc[strategy, metric]
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue

            flagged = abs(val) > threshold if metric != "max_drawdown" else val < threshold
            if flagged:
                flags.append({
                    "strategy": strategy,
                    "metric": metric,
                    "value": round(val, 4),
                    "threshold": threshold,
                    "flagged": True,
                    "note": f"{'suspiciously high' if metric != 'max_drawdown' else 'suspiciously low'}: check for lookahead bias",
                })

    if not flags:
        return pd.DataFrame(columns=["strategy", "metric", "value", "threshold", "flagged", "note"])

    return pd.DataFrame(flags)


# ---------------------------------------------------------------------------
# Ranking helper
# ---------------------------------------------------------------------------

def rank_strategies(
    results: dict[str, pd.DataFrame],
    metrics: list[str] | None = None,
    weights: list[float] | None = None,
) -> pd.DataFrame:
    """Rank strategies using a weighted composite score.

    Each metric is normalised (min-max scaled) and combined using the
    provided weights.  Metrics like ``max_drawdown`` are inverted
    (lower is better) before scoring.

    Args:
        results: Dict mapping strategy name -> trades DataFrame.
        metrics: Metrics to include in the composite score.
            Defaults to ["sharpe_ratio", "win_rate", "profit_factor",
            "roi", "max_drawdown"].
        weights: Relative weights for each metric.  Defaults to
            equal weighting.  For ``max_drawdown`` the score is
            (1 - normalised_value).

    Returns:
        DataFrame with composite_score and rank columns, sorted by rank.
    """
    if metrics is None:
        metrics = ["sharpe_ratio", "win_rate", "profit_factor", "roi", "max_drawdown"]
    if weights is None:
        weights = [1.0] * len(metrics)

    summary = compare_strategies(results)

    # Normalise each metric
    scored = pd.DataFrame(index=summary.index)
    for metric, weight in zip(metrics, weights):
        if metric not in summary.columns:
            continue
        col = pd.to_numeric(summary[metric], errors="coerce").fillna(0)
        mn, mx = col.min(), col.max()
        if mx > mn:
            norm = (col - mn) / (mx - mn)
        else:
            norm = pd.Series(0.5, index=summary.index)

        # Invert metrics where lower is better
        if metric in ("max_drawdown",):
            norm = 1 - norm

        scored[metric] = norm * weight

    summary["composite_score"] = scored.sum(axis=1).round(4)
    summary["rank"] = summary["composite_score"].rank(ascending=False).astype(int)
    return summary.sort_values("rank")
