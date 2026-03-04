"""Walk-forward backtest strategies.

Functions:
    walk_forward_backtest   -- Rolling-window walk-forward with n_splits folds.
    expanding_window_backtest -- Growing training window walk-forward.
    anchored_walk_forward   -- Walk-forward anchored to a fixed start date.
    combinatorial_purged_cv -- Combinatorial Purged Cross-Validation (CPCV).
"""

from __future__ import annotations

import itertools
import warnings
from typing import Any, Callable

import pandas as pd

from ._helpers import (
    _aggregate_metrics,
    _prepare_strategy_for_fold,
    _run_fold_backtest,
)


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
        2. If *strategy_fn* is a ``TrainableStrategy``, call
           ``strategy_fn.fit(train_data)`` to retrain before this fold.
        3. Run ``backtest()`` on the test window only.
        4. Run ``backtest()`` on the train window for in-sample vs
           out-of-sample comparison.
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
    if not 0 < train_ratio < 1:
        raise ValueError(f"train_ratio must be in (0, 1), got {train_ratio}")
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

        # Skip fold 0 if it has zero training data — testing on earliest
        # data with no training is not a valid walk-forward fold and
        # corrupts aggregated OOS metrics.
        if len(train_data) == 0:
            warnings.warn(
                f"Walk-forward fold {i} has zero training data — skipping. "
                f"This typically happens for fold 0.",
                stacklevel=2,
            )
            continue

        # Prepare strategy (calls fit() on TrainableStrategy instances)
        fold_strategy = _prepare_strategy_for_fold(strategy_fn, train_data)

        # Run OOS backtest on test window
        test_results, test_metrics = _run_fold_backtest(
            test_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        # Run IS backtest on train window for comparison
        train_results, train_metrics = _run_fold_backtest(
            train_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

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

        # Prepare strategy (calls fit() on TrainableStrategy instances)
        fold_strategy = _prepare_strategy_for_fold(strategy_fn, train_data)

        test_results, test_metrics = _run_fold_backtest(
            test_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )
        train_results, train_metrics = _run_fold_backtest(
            train_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
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
            "in_sample_win_rate": s["train_metrics"]["win_rate"],
            "out_of_sample_win_rate": s["test_metrics"]["win_rate"],
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

        # Prepare strategy (calls fit() on TrainableStrategy instances)
        fold_strategy = _prepare_strategy_for_fold(strategy_fn, train_data)

        test_results, test_metrics = _run_fold_backtest(
            test_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        if len(train_data) > 0:
            train_results, train_metrics = _run_fold_backtest(
                train_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
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
            "in_sample_win_rate": s["train_metrics"]["win_rate"],
            "out_of_sample_win_rate": s["test_metrics"]["win_rate"],
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

            # Collect valid (non-purged) slices of this train group.
            # Start with the whole group and progressively split it
            # around each test group boundary.
            valid_slices: list[tuple[int, int]] = [(g_start, g_end)]
            for tg in test_group_indices:
                tg_start, tg_end = groups[tg]
                new_slices: list[tuple[int, int]] = []
                for s_start, s_end in valid_slices:
                    # No overlap — keep slice as-is
                    if s_end <= tg_start - purge_gap or s_start >= tg_end + purge_gap:
                        new_slices.append((s_start, s_end))
                        continue
                    # Portion before the test group (respecting purge gap)
                    before_end = min(s_end, tg_start - purge_gap)
                    if before_end > s_start:
                        new_slices.append((s_start, before_end))
                    # Portion after the test group (respecting purge gap)
                    after_start = max(s_start, tg_end + purge_gap)
                    if after_start < s_end:
                        new_slices.append((after_start, s_end))
                valid_slices = new_slices

            for s_start, s_end in valid_slices:
                train_slices.append(data.iloc[s_start:s_end])

        train_data = pd.concat(train_slices, ignore_index=True) if train_slices else pd.DataFrame()

        # Prepare strategy (calls fit() on TrainableStrategy instances)
        fold_strategy = _prepare_strategy_for_fold(strategy_fn, train_data)

        # Run backtests
        test_results, test_metrics = _run_fold_backtest(
            test_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
            **extra_kwargs,
        )

        if len(train_data) > 0:
            train_results, train_metrics = _run_fold_backtest(
                train_data, fold_strategy, initial_bankroll, cost_pct, cost_flat,
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
            "in_sample_win_rate": s["train_metrics"]["win_rate"],
            "out_of_sample_win_rate": s["test_metrics"]["win_rate"],
        })

    return {
        "splits": splits,
        "aggregated_metrics": aggregated,
        "n_combinations": len(combos),
        "in_sample_vs_out_of_sample": is_vs_oos,
    }
