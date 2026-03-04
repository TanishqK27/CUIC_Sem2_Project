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
    combinatorial_purged_cv -- Combinatorial Purged Cross-Validation (CPCV).
    walk_forward_report     -- Human-readable summary of walk-forward results.
"""

from .protocol import TrainableStrategy
from .report import walk_forward_report
from .splitting import train_test_split
from .strategies import (
    anchored_walk_forward,
    combinatorial_purged_cv,
    expanding_window_backtest,
    walk_forward_backtest,
)

__all__ = [
    "TrainableStrategy",
    "anchored_walk_forward",
    "combinatorial_purged_cv",
    "expanding_window_backtest",
    "train_test_split",
    "walk_forward_backtest",
    "walk_forward_report",
]
