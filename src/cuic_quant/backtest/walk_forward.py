"""Walk-forward analysis and out-of-sample testing for the CUIC backtester.

Why: Fitting a model on data and evaluating on the same data produces
meaningless results. Walk-forward analysis trains on a sliding window of
historical data and tests on the next unseen period, providing realistic
out-of-sample performance estimates.

Functions:
    train_test_split        -- Simple chronological train/test split with optional purge gap.
    walk_forward_backtest   -- Rolling-window walk-forward with n_splits folds.
    expanding_window_backtest -- Growing training window walk-forward.
    anchored_walk_forward   -- Walk-forward anchored to a fixed start date.
    combinatorial_purged_cv -- Combinatorial Purged Cross-Validation (CPCV) a la Lopez de Prado.
    walk_forward_report     -- Human-readable summary of walk-forward results.
"""

from __future__ import annotations

import itertools
from typing import Any, Callable

import pandas as pd

from cuic_quant.backtest.backtester_backend import backtest
from cuic_quant.metrics import calculate_all_metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    results = backtest(
        data.reset_index(drop=True),
        strategy_fn,
        initial_bankroll=initial_bankroll,
        cost_pct=cost_pct,
        cost_flat=cost_flat,
        **extra_kwargs,
    )
    if len(results) > 0:
        metrics = calculate_all_metrics(results)
    else:
        metrics = {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
        }
    return results, metrics


def _aggregate_metrics(
    splits: list[dict[str, Any]],
    key: str = "test_metrics",
) -> dict[str, float | int]:
    """Aggregate metrics across multiple walk-forward folds.

    Computes a weighted average (by total_trades) for rate-based metrics
    (win_rate, sharpe_ratio, sortino_ratio, profit_factor) and a simple
    sum for additive metrics (total_trades, total_pnl).  Max drawdown is
    reported as the worst across folds.

    Args:
        splits: List of per-fold dicts, each containing a metrics sub-dict
            under the given *key*.
        key: Which metrics dict to read from each split entry.

    Returns:
        Aggregated metrics dict.
    """
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

    # Trade-weighted averages for ratio metrics
    rate_keys = ["win_rate", "sharpe_ratio", "sortino_ratio", "profit_factor"]
    aggregated: dict[str, float | int] = {
        "total_trades": total_trades,
        "total_pnl": round(total_pnl, 2),
    }
    for rk in rate_keys:
        weighted_sum = sum(
            s[key][rk] * s[key]["total_trades"] for s in splits
        )
        aggregated[rk] = round(weighted_sum / total_trades, 4) if total_trades else 0.0

    # Max drawdown: report the worst across folds
    aggregated["max_drawdown"] = round(
        max((s[key]["max_drawdown"] for s in splits), default=0.0), 4
    )

    return aggregated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def train_test_split(
    data: pd.DataFrame,
    train_ratio: float = 0.7,
    gap: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split time-series data into train and test sets.

    The split is purely positional (row-based) and respects chronological
    order -- earlier rows go to train, later rows to test.

    Args:
        data: DataFrame sorted by timestamp.
        train_ratio: Fraction of data for training (default 70 %).
        gap: Number of rows to skip between train and test (purging).
            This prevents information leakage when the strategy uses
            features with look-back windows.

    Returns:
        (train_df, test_df) tuple. Both DataFrames have their index
        reset. If the gap consumes all test data, test_df will be empty.

    Raises:
        ValueError: If train_ratio is not in the open interval (0, 1).
        ValueError: If data is empty.
    """
    if not 0 < train_ratio < 1:
        raise ValueError(f"train_ratio must be in (0, 1), got {train_ratio}")
    if len(data) == 0:
        raise ValueError("Cannot split empty DataFrame")

    n = len(data)
    split_idx = int(n * train_ratio)
    # Ensure at least 1 row in each partition
    split_idx = max(1, min(split_idx, n - 1))

    train = data.iloc[:split_idx].reset_index(drop=True)
    test_start = min(split_idx + gap, n)
    test = data.iloc[test_start:].reset_index(drop=True)

    return train, test


def walk_forward_backtest(
    data: pd.DataFrame,
    strategy_fn: Callable,
    n_splits: int = 5,
    train_ratio: float = 0.7,
    gap: int = 0,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Run walk-forward analysis with rolling windows.

    The data is divided into *n_splits* consecutive, non-overlapping test
    windows.  For each fold the training set is the *train_ratio* portion
    of data immediately preceding the test window (rolling, not expanding).

    For each split:
        1. Define train window and test window.
        2. (The caller's *strategy_fn* can inspect train data externally;
           this function does NOT fit anything -- it only manages splits.)
        3. Run ``backtest()`` on the test window only.
        4. Optionally run ``backtest()`` on the train window for
           in-sample vs out-of-sample comparison.
        5. Collect results.

    Args:
        data: DataFrame sorted by timestamp with columns required by
            ``backtest()`` (timestamp, game, home_team, away_team,
            home_odds, away_odds, home_win).
        strategy_fn: Strategy callable matching the backtester interface.
        n_splits: Number of walk-forward folds. Default 5.
        train_ratio: Fraction of each fold used for training.  The test
            portion is ``1 - train_ratio`` of the fold size. Default 0.7.
        gap: Rows to purge between train and test per fold.
        initial_bankroll: Starting bankroll per fold.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat dollar cost per trade.
        **extra_kwargs: Forwarded to ``backtest()`` (e.g. position_sizing).

    Returns:
        Dict with:
            - ``splits``: list of dicts, one per fold, each containing
              ``train_data``, ``test_data``, ``results``, ``test_metrics``,
              ``train_results``, ``train_metrics``.
            - ``aggregated_metrics``: combined out-of-sample metrics.
            - ``in_sample_vs_out_of_sample``: per-fold comparison.

    Raises:
        ValueError: If n_splits < 2 or data is too small to split.
    """
    if n_splits < 2:
        raise ValueError(f"n_splits must be >= 2, got {n_splits}")
    n = len(data)
    if n < n_splits * 2:
        raise ValueError(
            f"Not enough data ({n} rows) for {n_splits} splits -- "
            f"need at least {n_splits * 2} rows."
        )

    fold_size = n // n_splits
    splits: list[dict[str, Any]] = []

    for i in range(n_splits):
        # Test window for this fold
        test_start = i * fold_size
        test_end = (i + 1) * fold_size if i < n_splits - 1 else n
        test_data = data.iloc[test_start:test_end]

        # Training window: rows *before* this test window
        train_size = int(fold_size * train_ratio / (1 - train_ratio)) if train_ratio < 1 else fold_size
        train_start = max(0, test_start - gap - train_size)
        train_end = max(train_start, test_start - gap)
        train_data = data.iloc[train_start:train_end]

        # Run OOS backtest on test window
        test_results, test_metrics = _run_fold_backtest(
            test_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        # Run IS backtest on train window for comparison
        if len(train_data) > 0:
            train_results, train_metrics = _run_fold_backtest(
                train_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
                **extra_kwargs,
            )
        else:
            train_results = pd.DataFrame()
            train_metrics = {
                "total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
                "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
                "max_drawdown": 0.0, "profit_factor": 0.0,
            }

        splits.append({
            "fold": i,
            "train_data": train_data.reset_index(drop=True),
            "test_data": test_data.reset_index(drop=True),
            "results": test_results,
            "test_metrics": test_metrics,
            "train_results": train_results,
            "train_metrics": train_metrics,
        })

    aggregated = _aggregate_metrics(splits, key="test_metrics")

    # In-sample vs out-of-sample comparison
    is_vs_oos: list[dict[str, Any]] = []
    for s in splits:
        is_vs_oos.append({
            "fold": s["fold"],
            "in_sample_pnl": s["train_metrics"]["total_pnl"],
            "out_of_sample_pnl": s["test_metrics"]["total_pnl"],
            "in_sample_sharpe": s["train_metrics"]["sharpe_ratio"],
            "out_of_sample_sharpe": s["test_metrics"]["sharpe_ratio"],
            "in_sample_win_rate": s["train_metrics"]["win_rate"],
            "out_of_sample_win_rate": s["test_metrics"]["win_rate"],
        })

    return {
        "splits": splits,
        "aggregated_metrics": aggregated,
        "in_sample_vs_out_of_sample": is_vs_oos,
    }


def expanding_window_backtest(
    data: pd.DataFrame,
    strategy_fn: Callable,
    min_train_size: int = 50,
    step_size: int = 10,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Expanding window walk-forward (growing training set).

    Starts with *min_train_size* rows for training and tests on the next
    *step_size* rows.  Each subsequent fold adds *step_size* rows to the
    training set (the anchor stays at the beginning of the data).

    Args:
        data: DataFrame sorted by timestamp.
        strategy_fn: Strategy callable.
        min_train_size: Minimum number of rows before the first test.
        step_size: Number of rows added to training (and used for testing)
            in each step.
        initial_bankroll: Starting bankroll per fold.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat dollar cost per trade.
        **extra_kwargs: Forwarded to ``backtest()``.

    Returns:
        Dict with ``splits`` (list of fold dicts), ``aggregated_metrics``,
        and ``in_sample_vs_out_of_sample``.

    Raises:
        ValueError: If data is too short for even one fold.
    """
    n = len(data)
    if n < min_train_size + step_size:
        raise ValueError(
            f"Not enough data ({n} rows) for min_train_size={min_train_size} "
            f"+ step_size={step_size}."
        )

    splits: list[dict[str, Any]] = []
    fold_idx = 0
    train_end = min_train_size

    while train_end + step_size <= n:
        test_start = train_end
        test_end = min(train_end + step_size, n)

        train_data = data.iloc[:train_end]
        test_data = data.iloc[test_start:test_end]

        test_results, test_metrics = _run_fold_backtest(
            test_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )
        train_results, train_metrics = _run_fold_backtest(
            train_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        splits.append({
            "fold": fold_idx,
            "train_data": train_data.reset_index(drop=True),
            "test_data": test_data.reset_index(drop=True),
            "results": test_results,
            "test_metrics": test_metrics,
            "train_results": train_results,
            "train_metrics": train_metrics,
        })

        train_end += step_size
        fold_idx += 1

    aggregated = _aggregate_metrics(splits, key="test_metrics")

    is_vs_oos: list[dict[str, Any]] = []
    for s in splits:
        is_vs_oos.append({
            "fold": s["fold"],
            "in_sample_pnl": s["train_metrics"]["total_pnl"],
            "out_of_sample_pnl": s["test_metrics"]["total_pnl"],
            "in_sample_sharpe": s["train_metrics"]["sharpe_ratio"],
            "out_of_sample_sharpe": s["test_metrics"]["sharpe_ratio"],
        })

    return {
        "splits": splits,
        "aggregated_metrics": aggregated,
        "in_sample_vs_out_of_sample": is_vs_oos,
    }


def anchored_walk_forward(
    data: pd.DataFrame,
    strategy_fn: Callable,
    anchor_date: str,
    test_periods: list[tuple[str, str]],
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Walk-forward with fixed anchor date for training start.

    Training always begins at *anchor_date* and extends up to the start
    of each test period.  This is useful when you have a specific
    historical event you always want included in training.

    Args:
        data: DataFrame sorted by timestamp.  Must have a ``timestamp``
            column parseable by ``pd.to_datetime``.
        strategy_fn: Strategy callable.
        anchor_date: Start date for all training windows (inclusive).
            Format ``"YYYY-MM-DD"``.
        test_periods: List of ``(start_date, end_date)`` strings defining
            each out-of-sample window.
        initial_bankroll: Starting bankroll per fold.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat dollar cost per trade.
        **extra_kwargs: Forwarded to ``backtest()``.

    Returns:
        Dict with ``splits``, ``aggregated_metrics``, and
        ``in_sample_vs_out_of_sample``.
    """
    data = data.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    anchor_dt = pd.to_datetime(anchor_date)

    splits: list[dict[str, Any]] = []

    for fold_idx, (test_start_str, test_end_str) in enumerate(test_periods):
        test_start_dt = pd.to_datetime(test_start_str)
        test_end_dt = pd.to_datetime(test_end_str)

        train_mask = (data["timestamp"] >= anchor_dt) & (data["timestamp"] < test_start_dt)
        test_mask = (data["timestamp"] >= test_start_dt) & (data["timestamp"] <= test_end_dt)

        train_data = data.loc[train_mask]
        test_data = data.loc[test_mask]

        if len(test_data) == 0:
            continue

        test_results, test_metrics = _run_fold_backtest(
            test_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        if len(train_data) > 0:
            train_results, train_metrics = _run_fold_backtest(
                train_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
                **extra_kwargs,
            )
        else:
            train_results = pd.DataFrame()
            train_metrics = {
                "total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
                "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
                "max_drawdown": 0.0, "profit_factor": 0.0,
            }

        splits.append({
            "fold": fold_idx,
            "test_period": (test_start_str, test_end_str),
            "train_data": train_data.reset_index(drop=True),
            "test_data": test_data.reset_index(drop=True),
            "results": test_results,
            "test_metrics": test_metrics,
            "train_results": train_results,
            "train_metrics": train_metrics,
        })

    aggregated = _aggregate_metrics(splits, key="test_metrics") if splits else {
        "total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
        "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
        "max_drawdown": 0.0, "profit_factor": 0.0,
    }

    is_vs_oos: list[dict[str, Any]] = []
    for s in splits:
        is_vs_oos.append({
            "fold": s["fold"],
            "test_period": s["test_period"],
            "in_sample_pnl": s["train_metrics"]["total_pnl"],
            "out_of_sample_pnl": s["test_metrics"]["total_pnl"],
            "in_sample_sharpe": s["train_metrics"]["sharpe_ratio"],
            "out_of_sample_sharpe": s["test_metrics"]["sharpe_ratio"],
        })

    return {
        "splits": splits,
        "aggregated_metrics": aggregated,
        "in_sample_vs_out_of_sample": is_vs_oos,
    }


def combinatorial_purged_cv(
    data: pd.DataFrame,
    strategy_fn: Callable,
    n_splits: int = 5,
    n_test_splits: int = 2,
    purge_gap: int = 0,
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Combinatorial Purged Cross-Validation (CPCV) from Lopez de Prado.

    Divides data into *n_splits* contiguous groups and creates all
    C(n_splits, n_test_splits) combinations.  For each combination the
    selected groups form the test set and the remaining groups form the
    training set.  Rows within *purge_gap* of a train/test boundary are
    removed from the training set to prevent leakage.

    Args:
        data: DataFrame sorted by timestamp.
        strategy_fn: Strategy callable.
        n_splits: Number of contiguous groups. Default 5.
        n_test_splits: Number of groups used as test per combination.
            Default 2.
        purge_gap: Rows to remove from training at each boundary with a
            test group (both sides). Default 0.
        initial_bankroll: Starting bankroll per fold.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat dollar cost per trade.
        **extra_kwargs: Forwarded to ``backtest()``.

    Returns:
        Dict with ``splits`` (one entry per combination), ``aggregated_metrics``,
        ``n_combinations`` (total number of train/test combos), and
        ``in_sample_vs_out_of_sample``.

    Raises:
        ValueError: If n_test_splits >= n_splits.
    """
    if n_test_splits >= n_splits:
        raise ValueError(
            f"n_test_splits ({n_test_splits}) must be < n_splits ({n_splits})"
        )

    n = len(data)
    group_size = n // n_splits
    # Build group boundaries: list of (start, end) row indices
    groups: list[tuple[int, int]] = []
    for g in range(n_splits):
        start = g * group_size
        end = (g + 1) * group_size if g < n_splits - 1 else n
        groups.append((start, end))

    combos = list(itertools.combinations(range(n_splits), n_test_splits))
    splits: list[dict[str, Any]] = []

    for combo_idx, test_group_indices in enumerate(combos):
        test_group_set = set(test_group_indices)

        # Build test DataFrame from selected groups
        test_slices = [data.iloc[groups[g][0]:groups[g][1]] for g in test_group_indices]
        test_data = pd.concat(test_slices, ignore_index=True)

        # Build train DataFrame from remaining groups, with purging
        train_slices: list[pd.DataFrame] = []
        for g in range(n_splits):
            if g in test_group_set:
                continue
            g_start, g_end = groups[g]

            # Purge rows near test-group boundaries
            purge_start = g_start
            purge_end = g_end
            for tg in test_group_indices:
                tg_start, tg_end = groups[tg]
                # If this train group is directly before a test group
                if g_end == tg_start:
                    purge_end = max(g_start, g_end - purge_gap)
                # If this train group is directly after a test group
                if g_start == tg_end:
                    purge_start = min(g_end, g_start + purge_gap)

            if purge_start < purge_end:
                train_slices.append(data.iloc[purge_start:purge_end])

        train_data = pd.concat(train_slices, ignore_index=True) if train_slices else pd.DataFrame()

        # Run backtests
        test_results, test_metrics = _run_fold_backtest(
            test_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        if len(train_data) > 0:
            train_results, train_metrics = _run_fold_backtest(
                train_data, strategy_fn, initial_bankroll, cost_pct, cost_flat,
                **extra_kwargs,
            )
        else:
            train_results = pd.DataFrame()
            train_metrics = {
                "total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
                "sharpe_ratio": 0.0, "sortino_ratio": 0.0,
                "max_drawdown": 0.0, "profit_factor": 0.0,
            }

        splits.append({
            "fold": combo_idx,
            "test_groups": list(test_group_indices),
            "train_data": train_data,
            "test_data": test_data,
            "results": test_results,
            "test_metrics": test_metrics,
            "train_results": train_results,
            "train_metrics": train_metrics,
        })

    aggregated = _aggregate_metrics(splits, key="test_metrics")

    is_vs_oos: list[dict[str, Any]] = []
    for s in splits:
        is_vs_oos.append({
            "fold": s["fold"],
            "test_groups": s["test_groups"],
            "in_sample_pnl": s["train_metrics"]["total_pnl"],
            "out_of_sample_pnl": s["test_metrics"]["total_pnl"],
            "in_sample_sharpe": s["train_metrics"]["sharpe_ratio"],
            "out_of_sample_sharpe": s["test_metrics"]["sharpe_ratio"],
        })

    return {
        "splits": splits,
        "aggregated_metrics": aggregated,
        "n_combinations": len(combos),
        "in_sample_vs_out_of_sample": is_vs_oos,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def walk_forward_report(results: dict[str, Any]) -> str:
    """Generate human-readable report from walk-forward results.

    Accepts the dict returned by any of the walk-forward functions in this
    module (``walk_forward_backtest``, ``expanding_window_backtest``,
    ``anchored_walk_forward``, ``combinatorial_purged_cv``).

    Args:
        results: Dict with ``splits``, ``aggregated_metrics``, and
            optionally ``in_sample_vs_out_of_sample``.

    Returns:
        Multi-line string suitable for ``print()``.
    """
    lines: list[str] = []
    sep = "=" * 60

    lines.append(sep)
    lines.append("           WALK-FORWARD ANALYSIS REPORT")
    lines.append(sep)

    # Aggregated OOS metrics
    agg = results.get("aggregated_metrics", {})
    lines.append("")
    lines.append("  Aggregated Out-of-Sample Metrics")
    lines.append("  " + "-" * 40)
    lines.append(f"  Total Trades:    {agg.get('total_trades', 0):>10}")
    lines.append(f"  Total PnL:       ${agg.get('total_pnl', 0.0):>10.2f}")
    lines.append(f"  Win Rate:        {agg.get('win_rate', 0.0):>10.2%}")
    lines.append(f"  Sharpe Ratio:    {agg.get('sharpe_ratio', 0.0):>10.4f}")
    lines.append(f"  Sortino Ratio:   {agg.get('sortino_ratio', 0.0):>10.4f}")
    lines.append(f"  Max Drawdown:    {agg.get('max_drawdown', 0.0):>10.2%}")
    lines.append(f"  Profit Factor:   {agg.get('profit_factor', 0.0):>10.4f}")

    # Per-fold breakdown
    splits = results.get("splits", [])
    if splits:
        lines.append("")
        lines.append("  Per-Fold Breakdown")
        lines.append("  " + "-" * 40)
        for s in splits:
            fold = s.get("fold", "?")
            tm = s.get("test_metrics", {})
            train_rows = len(s.get("train_data", []))
            test_rows = len(s.get("test_data", []))
            lines.append(
                f"  Fold {fold}: "
                f"train={train_rows} rows, test={test_rows} rows | "
                f"OOS trades={tm.get('total_trades', 0)}, "
                f"PnL=${tm.get('total_pnl', 0.0):.2f}, "
                f"WR={tm.get('win_rate', 0.0):.1%}"
            )

    # IS vs OOS comparison
    is_vs_oos = results.get("in_sample_vs_out_of_sample", [])
    if is_vs_oos:
        lines.append("")
        lines.append("  In-Sample vs Out-of-Sample Comparison")
        lines.append("  " + "-" * 40)
        for entry in is_vs_oos:
            fold = entry.get("fold", "?")
            is_pnl = entry.get("in_sample_pnl", 0.0)
            oos_pnl = entry.get("out_of_sample_pnl", 0.0)
            is_sharpe = entry.get("in_sample_sharpe", 0.0)
            oos_sharpe = entry.get("out_of_sample_sharpe", 0.0)
            lines.append(
                f"  Fold {fold}: "
                f"IS PnL=${is_pnl:>8.2f}  OOS PnL=${oos_pnl:>8.2f}  |  "
                f"IS Sharpe={is_sharpe:>6.3f}  OOS Sharpe={oos_sharpe:>6.3f}"
            )

    # Overfitting signal
    if is_vs_oos:
        is_total = sum(e.get("in_sample_pnl", 0.0) for e in is_vs_oos)
        oos_total = sum(e.get("out_of_sample_pnl", 0.0) for e in is_vs_oos)
        lines.append("")
        if oos_total < 0 < is_total:
            lines.append(
                "  ** WARNING: In-sample profitable but out-of-sample negative. "
                "Possible overfitting. **"
            )
        elif is_total > 0 and oos_total > 0:
            degradation = 1 - (oos_total / is_total) if is_total != 0 else 0
            lines.append(
                f"  Performance degradation IS -> OOS: {degradation:.1%}"
            )

    n_combos = results.get("n_combinations")
    if n_combos is not None:
        lines.append(f"\n  CPCV combinations tested: {n_combos}")

    lines.append(sep)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np

    print("=" * 60)
    print("  walk_forward.py self-test")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Build synthetic game data
    # ------------------------------------------------------------------
    rng = np.random.RandomState(42)
    n_games = 200

    dates = pd.date_range("2025-01-01", periods=n_games, freq="D")
    home_odds = rng.uniform(1.3, 3.0, size=n_games).round(2)
    away_odds = rng.uniform(1.3, 3.0, size=n_games).round(2)
    home_win = rng.choice([0, 1], size=n_games)

    sample_data = pd.DataFrame({
        "timestamp": dates,
        "game": [f"Team{i}H vs Team{i}A" for i in range(n_games)],
        "home_team": [f"Team{i}H" for i in range(n_games)],
        "away_team": [f"Team{i}A" for i in range(n_games)],
        "home_odds": home_odds,
        "away_odds": away_odds,
        "home_win": home_win,
    })

    # Simple deterministic strategy
    def simple_home_strategy(
        row: pd.Series,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {"action": "BUY_HOME", "confidence": 0.5, "size": 100.0}

    # ------------------------------------------------------------------
    # 1. train_test_split
    # ------------------------------------------------------------------
    print("\n--- Test 1: train_test_split ---")
    train, test = train_test_split(sample_data, train_ratio=0.7, gap=5)
    assert len(train) == 140, f"Expected 140 train rows, got {len(train)}"
    assert len(test) == 55, f"Expected 55 test rows, got {len(test)}"
    print(f"  train={len(train)} rows, test={len(test)} rows -- OK")

    # Edge case: gap=0
    train0, test0 = train_test_split(sample_data, train_ratio=0.7, gap=0)
    assert len(train0) + len(test0) == 200
    print(f"  gap=0: train={len(train0)}, test={len(test0)} -- OK")

    # ------------------------------------------------------------------
    # 2. walk_forward_backtest
    # ------------------------------------------------------------------
    print("\n--- Test 2: walk_forward_backtest ---")
    wf_results = walk_forward_backtest(
        sample_data,
        simple_home_strategy,
        n_splits=4,
        train_ratio=0.7,
        gap=0,
        initial_bankroll=10000.0,
    )
    assert "splits" in wf_results
    assert "aggregated_metrics" in wf_results
    assert "in_sample_vs_out_of_sample" in wf_results
    assert len(wf_results["splits"]) == 4
    print(f"  {len(wf_results['splits'])} folds -- OK")
    print(f"  Aggregated OOS metrics: {wf_results['aggregated_metrics']}")

    # ------------------------------------------------------------------
    # 3. expanding_window_backtest
    # ------------------------------------------------------------------
    print("\n--- Test 3: expanding_window_backtest ---")
    ew_results = expanding_window_backtest(
        sample_data,
        simple_home_strategy,
        min_train_size=50,
        step_size=25,
        initial_bankroll=10000.0,
    )
    assert len(ew_results["splits"]) > 0
    print(f"  {len(ew_results['splits'])} folds -- OK")
    print(f"  Aggregated OOS metrics: {ew_results['aggregated_metrics']}")

    # ------------------------------------------------------------------
    # 4. anchored_walk_forward
    # ------------------------------------------------------------------
    print("\n--- Test 4: anchored_walk_forward ---")
    aw_results = anchored_walk_forward(
        sample_data,
        simple_home_strategy,
        anchor_date="2025-01-01",
        test_periods=[
            ("2025-04-01", "2025-05-01"),
            ("2025-05-01", "2025-06-01"),
            ("2025-06-01", "2025-07-01"),
        ],
        initial_bankroll=10000.0,
    )
    assert len(aw_results["splits"]) == 3
    print(f"  {len(aw_results['splits'])} folds -- OK")
    print(f"  Aggregated OOS metrics: {aw_results['aggregated_metrics']}")

    # ------------------------------------------------------------------
    # 5. combinatorial_purged_cv
    # ------------------------------------------------------------------
    print("\n--- Test 5: combinatorial_purged_cv ---")
    cpcv_results = combinatorial_purged_cv(
        sample_data,
        simple_home_strategy,
        n_splits=5,
        n_test_splits=2,
        purge_gap=2,
        initial_bankroll=10000.0,
    )
    assert cpcv_results["n_combinations"] == 10  # C(5,2) = 10
    print(f"  {cpcv_results['n_combinations']} combinations -- OK")
    print(f"  Aggregated OOS metrics: {cpcv_results['aggregated_metrics']}")

    # ------------------------------------------------------------------
    # 6. walk_forward_report
    # ------------------------------------------------------------------
    print("\n--- Test 6: walk_forward_report ---")
    for label, res in [
        ("walk_forward_backtest", wf_results),
        ("expanding_window", ew_results),
        ("anchored", aw_results),
        ("CPCV", cpcv_results),
    ]:
        report = walk_forward_report(res)
        assert isinstance(report, str)
        assert len(report) > 100
        print(f"\n  Report for {label}:")
        for line in report.split("\n"):
            print(f"    {line}")

    # ------------------------------------------------------------------
    # 7. Verify import path
    # ------------------------------------------------------------------
    print("\n--- Test 7: Import verification ---")
    from cuic_quant.backtest.walk_forward import (
        anchored_walk_forward as _awf,
        combinatorial_purged_cv as _cpcv,
        expanding_window_backtest as _ewb,
        train_test_split as _tts,
        walk_forward_backtest as _wfb,
        walk_forward_report as _wfr,
    )
    print("  All 6 public functions importable -- OK")

    print("\n" + "=" * 60)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 60)
