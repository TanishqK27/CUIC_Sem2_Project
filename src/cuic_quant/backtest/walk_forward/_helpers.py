"""Internal helpers for walk-forward analysis."""

from __future__ import annotations

import warnings
from typing import Any, Callable

import pandas as pd

from cuic_quant.backtest.backtester_backend import backtest
from cuic_quant.metrics import calculate_all_metrics
from cuic_quant.backtest.walk_forward.protocol import TrainableStrategy


def _run_fold_backtest(
    data: pd.DataFrame,
    strategy_fn: Callable,
    initial_bankroll: float,
    cost_pct: float,
    cost_flat: float,
    **extra_kwargs: Any,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Run backtest() on a data slice and compute metrics.

    Args:
        data: DataFrame slice to backtest on.
        strategy_fn: Strategy callable matching the backtester interface.
        initial_bankroll: Starting bankroll for this fold.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat dollar cost per trade.
        **extra_kwargs: Additional keyword arguments forwarded to backtest().

    Returns:
        Tuple of (results DataFrame, metrics dict).
    """
    _empty_metrics: dict[str, float | int] = {
        "total_trades": 0,
        "win_rate": 0.0,
        "total_pnl": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "max_drawdown": 0.0,
        "profit_factor": 0.0,
    }
    try:
        results = backtest(
            data.reset_index(drop=True),
            strategy_fn,
            initial_bankroll=initial_bankroll,
            cost_pct=cost_pct,
            cost_flat=cost_flat,
            **extra_kwargs,
        )
    except Exception as e:
        warnings.warn(
            f"Fold backtest failed: {e}. Returning empty results for this fold.",
            stacklevel=3,
        )
        return pd.DataFrame(), _empty_metrics

    if len(results) > 0:
        metrics = calculate_all_metrics(results)
    else:
        metrics = dict(_empty_metrics)
    return results, metrics


def _aggregate_metrics(
    splits: list[dict[str, Any]],
    key: str = "test_metrics",
) -> dict[str, float | int]:
    """Aggregate metrics across multiple walk-forward folds.

    For Sharpe/Sortino, concatenates all OOS trade results and computes
    a single ratio from the combined series (statistically valid).
    Win rate and profit factor use trade-weighted averages.
    Max drawdown is the worst across folds.

    Args:
        splits: List of per-fold dicts, each containing a metrics sub-dict
            under the given *key*, and a ``results`` DataFrame.
        key: Which metrics dict to read from each split entry.

    Returns:
        Aggregated metrics dict.
    """
    # Concatenate all OOS results
    all_oos_results = []
    for s in splits:
        results_df = s.get("results")
        if results_df is not None and len(results_df) > 0:
            all_oos_results.append(results_df)

    combined: pd.DataFrame | None = None
    if all_oos_results:
        combined = pd.concat(all_oos_results, ignore_index=True)

        # CPCV deduplication: each game appears in C(n-1, k-1) test folds.
        # Average PnL per unique game so metrics (Sharpe, Sortino, trade
        # counts, total PnL) aren't inflated by duplicated rows.
        if (
            "game" in combined.columns
            and "timestamp" in combined.columns
            and combined.duplicated(subset=["timestamp", "game"]).any()
        ):
            agg_spec: dict[str, str | tuple[str, str]] = {
                "pnl": "mean",
                "bet_size": "mean",
            }
            for col in ("odds", "bankroll", "confidence", "closing_odds"):
                if col in combined.columns:
                    agg_spec[col] = "mean"
            for col in ("outcome", "action"):
                if col in combined.columns:
                    agg_spec[col] = "first"

            combined = (
                combined.groupby(["timestamp", "game"], as_index=False, sort=False)
                .agg(agg_spec)
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

        # Recompute cumulative_pnl so metrics (max_drawdown) see a
        # continuous equity curve, not artificial drops at fold boundaries.
        if "pnl" in combined.columns:
            combined["cumulative_pnl"] = combined["pnl"].cumsum()

    # Derive totals from deduplicated combined results when available,
    # otherwise fall back to per-fold sums (regular walk-forward).
    if combined is not None and len(combined) > 0:
        total_trades = len(combined)
        total_pnl = float(combined["pnl"].sum())
    else:
        total_trades = sum(s[key]["total_trades"] for s in splits)
        total_pnl = sum(s[key]["total_pnl"] for s in splits)

    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
        }

    aggregated: dict[str, float | int] = {
        "total_trades": total_trades,
        "total_pnl": round(total_pnl, 2),
    }

    # Win rate from deduplicated combined, else trade-weighted average
    if combined is not None and "outcome" in combined.columns and len(combined) > 0:
        wins = (combined["outcome"] == "WIN").sum()
        aggregated["win_rate"] = round(wins / len(combined), 4)
    else:
        weighted_sum = sum(
            s[key]["win_rate"] * s[key]["total_trades"] for s in splits
        )
        aggregated["win_rate"] = round(weighted_sum / total_trades, 4) if total_trades else 0.0

    if combined is not None and len(combined) > 0:
        combined_metrics = calculate_all_metrics(combined)
        aggregated["sharpe_ratio"] = round(combined_metrics.get("sharpe_ratio", 0.0), 4)
        aggregated["sortino_ratio"] = round(combined_metrics.get("sortino_ratio", 0.0), 4)
        aggregated["profit_factor"] = round(combined_metrics.get("profit_factor", 0.0), 4)
        aggregated["max_drawdown"] = round(combined_metrics.get("max_drawdown", 0.0), 4)
    else:
        aggregated["sharpe_ratio"] = 0.0
        aggregated["sortino_ratio"] = 0.0
        aggregated["profit_factor"] = 0.0
        aggregated["max_drawdown"] = 0.0

    return aggregated


def _prepare_strategy_for_fold(
    strategy: Any,
    train_data: pd.DataFrame,
) -> Callable:
    """Prepare a strategy for a walk-forward fold.

    If *strategy* implements the ``TrainableStrategy`` protocol, calls
    ``strategy.fit(train_data)`` and returns ``strategy.predict`` as the
    callable for ``backtest()``.  Otherwise returns *strategy* unchanged.

    A defensive copy of *train_data* is passed to ``fit()`` so that
    in-place mutations inside ``fit()`` cannot corrupt subsequent folds.

    Args:
        strategy: Either a plain callable or a ``TrainableStrategy`` instance.
        train_data: Training data for this fold (includes ``home_win``).

    Returns:
        Callable suitable for passing to ``backtest()`` as ``strategy_fn``.

    Raises:
        TypeError: If *strategy* is a class (not an instance) that looks
            like a TrainableStrategy, or if ``fit``/``predict`` are not
            callable.
    """
    # Guard: user passed a class instead of an instance
    if isinstance(strategy, type) and (
        hasattr(strategy, "fit") and hasattr(strategy, "predict")
    ):
        raise TypeError(
            f"Received class {strategy.__name__} instead of an instance. "
            f"Pass {strategy.__name__}() (with parentheses) as strategy_fn."
        )

    if isinstance(strategy, TrainableStrategy):
        if not callable(strategy.fit) or not callable(strategy.predict):
            raise TypeError(
                f"Strategy {type(strategy).__name__} has 'fit' and 'predict' "
                f"attributes but they are not callable. Both must be methods."
            )
        strategy.fit(train_data.copy())
        return strategy.predict
    return strategy
