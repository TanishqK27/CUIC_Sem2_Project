"""Chronological train/test splitting for time-series data."""

from __future__ import annotations

import warnings

import pandas as pd


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

    # Verify chronological order if timestamp column exists
    if "timestamp" in data.columns:
        ts = pd.to_datetime(data["timestamp"], errors="coerce")
        if not ts.is_monotonic_increasing:
            warnings.warn(
                "Input data is not sorted chronologically. "
                "train_test_split assumes ascending timestamp order. "
                "Sort your data first: data.sort_values('timestamp').",
                stacklevel=2,
            )

    n = len(data)
    split_idx = int(n * train_ratio)
    # Ensure at least 1 row in each partition
    split_idx = max(1, min(split_idx, n - 1))

    train = data.iloc[:split_idx].reset_index(drop=True)
    test_start = min(split_idx + gap, n)
    test = data.iloc[test_start:].reset_index(drop=True)

    return train, test
