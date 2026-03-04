"""Walk-forward backtesting with model refitting.

Provides five split strategies matching common sports-betting literature:

  * SimpleSplit       — single train/test holdout
  * RollingWindow     — fixed-size rolling window (model refit each fold)
  * ExpandingWindow   — anchored start, growing training set
  * AnchoredSplit     — alias for ExpandingWindow
  * CPCV              — Combinatorial Purged Cross-Validation (Marcos Lopez de Prado)

Each splitter yields (train_idx, test_idx) tuples over a sorted integer index.
``run_walk_forward`` orchestrates the full pipeline and concatenates fold
results into a single trades DataFrame, so the notebook gets one clean table.

References:
    - Lopez de Prado, M. (2018). Advances in Financial Machine Learning.
    - georgedouzas/sports-betting TimeSeriesSplit pattern.
"""

from __future__ import annotations

import itertools
import logging
from abc import ABC, abstractmethod
from typing import Generator

import numpy as np
import pandas as pd

from cuic_quant.backtest.engine import (
    BacktestConfig,
    BettingStrategy,
    _empty_trades_df,
    run_backtest,
)
from cuic_quant.backtest.data_loader import BacktestDataset

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Split strategies
# ---------------------------------------------------------------------------

IndexPair = tuple[np.ndarray, np.ndarray]


class BaseSplitter(ABC):
    """Abstract base for walk-forward splitters."""

    @abstractmethod
    def split(self, n: int) -> Generator[IndexPair, None, None]:
        """Yield (train_indices, test_indices) pairs.

        Args:
            n: Total number of observations (time-ordered).

        Yields:
            Tuples of integer arrays (train_idx, test_idx).
        """


class SimpleSplit(BaseSplitter):
    """Single train/test holdout split.

    Args:
        test_fraction: Fraction of data reserved for testing.
    """

    def __init__(self, test_fraction: float = 0.2) -> None:
        if not 0 < test_fraction < 1:
            raise ValueError("test_fraction must be in (0, 1)")
        self.test_fraction = test_fraction

    def split(self, n: int) -> Generator[IndexPair, None, None]:
        split_point = int(n * (1 - self.test_fraction))
        train = np.arange(split_point)
        test = np.arange(split_point, n)
        if len(train) > 0 and len(test) > 0:
            yield train, test


class RollingWindow(BaseSplitter):
    """Rolling fixed-size training window.

    Each fold advances by ``step`` observations.  The model is refit on
    each fold, which is the key difference from a simple split.

    Args:
        train_size: Number of observations in the training window.
        test_size: Number of observations in each test fold.
        step: How many observations to advance between folds.
    """

    def __init__(
        self,
        train_size: int = 200,
        test_size: int = 50,
        step: int = 50,
    ) -> None:
        self.train_size = train_size
        self.test_size = test_size
        self.step = step

    def split(self, n: int) -> Generator[IndexPair, None, None]:
        start = 0
        while start + self.train_size + self.test_size <= n:
            train = np.arange(start, start + self.train_size)
            test = np.arange(
                start + self.train_size,
                min(start + self.train_size + self.test_size, n),
            )
            if len(test) > 0:
                yield train, test
            start += self.step


class ExpandingWindow(BaseSplitter):
    """Expanding (anchored) training window.

    Training set grows with each fold; the start is always index 0.
    This is the most conservative approach: the model sees all historical
    data up to the test period.

    Args:
        min_train_size: Minimum training observations before first test fold.
        test_size: Number of observations in each test fold.
        step: Fold advance step.
    """

    def __init__(
        self,
        min_train_size: int = 150,
        test_size: int = 50,
        step: int = 50,
    ) -> None:
        self.min_train_size = min_train_size
        self.test_size = test_size
        self.step = step

    def split(self, n: int) -> Generator[IndexPair, None, None]:
        train_end = self.min_train_size
        while train_end + self.test_size <= n:
            train = np.arange(0, train_end)
            test = np.arange(train_end, min(train_end + self.test_size, n))
            if len(test) > 0:
                yield train, test
            train_end += self.step


# Alias
AnchoredSplit = ExpandingWindow


class CPCV(BaseSplitter):
    """Combinatorial Purged Cross-Validation (simplified).

    Splits data into ``n_splits`` equally-sized groups and tests on
    ``n_test_splits`` of them, cycling through all combinations.
    A purge gap between train and test groups is applied to prevent
    information leakage around fold boundaries.

    Note:
        Full CPCV requires an embargo period; this implementation uses a
        simple index purge gap instead.

    Args:
        n_splits: Total number of groups.
        n_test_splits: Number of groups to hold out as test each fold.
        purge_gap: Number of observations to purge at fold boundaries.

    References:
        Lopez de Prado, M. (2018). Chapter 12.
    """

    def __init__(
        self,
        n_splits: int = 6,
        n_test_splits: int = 2,
        purge_gap: int = 5,
    ) -> None:
        self.n_splits = n_splits
        self.n_test_splits = n_test_splits
        self.purge_gap = purge_gap

    def split(self, n: int) -> Generator[IndexPair, None, None]:
        group_size = n // self.n_splits
        if group_size < 5:
            logger.warning("CPCV group size too small (%d); falling back to ExpandingWindow", group_size)
            yield from ExpandingWindow().split(n)
            return

        groups = [
            np.arange(i * group_size, min((i + 1) * group_size, n))
            for i in range(self.n_splits)
        ]

        for test_combo in itertools.combinations(range(self.n_splits), self.n_test_splits):
            test_groups = set(test_combo)
            train_groups = [g for i, g in enumerate(groups) if i not in test_groups]
            test_groups_arr = [groups[i] for i in test_combo]

            test_idx = np.concatenate(test_groups_arr)
            test_min, test_max = test_idx.min(), test_idx.max()

            # Apply purge gap
            train_idx_list = []
            for g in train_groups:
                purged = g[
                    (g < test_min - self.purge_gap)
                    | (g > test_max + self.purge_gap)
                ]
                train_idx_list.append(purged)

            if not train_idx_list:
                continue
            train_idx = np.concatenate(train_idx_list)

            if len(train_idx) > 0 and len(test_idx) > 0:
                yield np.sort(train_idx), np.sort(test_idx)


# ---------------------------------------------------------------------------
# Walk-forward orchestrator
# ---------------------------------------------------------------------------

def run_walk_forward(
    strategy: BettingStrategy,
    dataset: BacktestDataset,
    splitter: BaseSplitter | None = None,
    config: BacktestConfig | None = None,
    carry_bankroll: bool = True,
) -> pd.DataFrame:
    """Run a full walk-forward backtest and concatenate all fold results.

    The strategy is *refit* on each training fold, preventing lookahead
    bias.  Each fold's trades are labelled with a fold number.

    When ``carry_bankroll=True`` (default), the bankroll at the end of each
    fold is carried forward as the starting bankroll for the next fold.
    This gives a realistic continuous equity curve and ensures the
    max drawdown metric stays in [0, 1].

    Args:
        strategy: BettingStrategy instance.  Will be fit in-place per fold.
        dataset: BacktestDataset (X, Y, O, dates) from the data loader.
        splitter: Walk-forward split strategy.  Defaults to ExpandingWindow
            with min_train_size=150, test_size=50, step=50.
        config: Backtest configuration.  Uses defaults if None.
        carry_bankroll: If True, pass the final bankroll from fold N as the
            starting bankroll for fold N+1.  Defaults to True.

    Returns:
        Concatenated trades DataFrame across all folds.  An empty DataFrame
        is returned if no folds produce any trades.
    """
    if splitter is None:
        splitter = ExpandingWindow(min_train_size=150, test_size=50, step=50)

    if config is None:
        config = BacktestConfig()

    X, Y, O, dates = dataset.X, dataset.Y, dataset.O, dataset.dates
    n = len(X)

    fold_dfs = []
    current_bankroll = config.initial_bankroll

    for fold_id, (train_idx, test_idx) in enumerate(splitter.split(n)):
        logger.info(
            "Fold %d: train=%d games, test=%d games, bankroll=%.2f",
            fold_id,
            len(train_idx),
            len(test_idx),
            current_bankroll,
        )

        # Stop if we've run out of money
        if current_bankroll < 1.0:
            logger.warning("Bankroll depleted at fold %d — stopping walk-forward", fold_id)
            break

        X_train = X.iloc[train_idx]
        Y_train = Y.iloc[train_idx]
        X_test = X.iloc[test_idx]
        Y_test = Y.iloc[test_idx]
        O_test = O.iloc[test_idx]
        dates_test = dates[test_idx] if dates is not None else None

        # Build per-fold config with current bankroll
        fold_config = BacktestConfig(
            initial_bankroll=current_bankroll if carry_bankroll else config.initial_bankroll,
            kelly_fraction=config.kelly_fraction,
            max_bet_fraction=config.max_bet_fraction,
            min_edge=config.min_edge,
            transaction_costs=config.transaction_costs,
            bet_side=config.bet_side,
        )

        fold_df = run_backtest(
            strategy=strategy,
            X_train=X_train,
            Y_train=Y_train,
            X_test=X_test,
            Y_test=Y_test,
            O_test=O_test,
            config=fold_config,
            dates_test=dates_test,
            fold_id=fold_id,
        )
        fold_dfs.append(fold_df)

        # Carry bankroll forward
        if carry_bankroll and not fold_df.empty and "bankroll" in fold_df.columns:
            final_bk = pd.to_numeric(fold_df["bankroll"], errors="coerce").dropna()
            if not final_bk.empty:
                current_bankroll = max(0.0, float(final_bk.iloc[-1]))

    if not fold_dfs or all(df.empty for df in fold_dfs):
        logger.warning("Walk-forward produced zero trades across all folds")
        return _empty_trades_df()

    all_trades = pd.concat([df for df in fold_dfs if not df.empty], ignore_index=True)

    # Recompute global cumulative P&L across all folds (from initial bankroll)
    if not all_trades.empty:
        all_trades["cumulative_pnl"] = all_trades["pnl"].cumsum().round(4)

    return all_trades
