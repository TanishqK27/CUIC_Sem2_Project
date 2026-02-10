"""CSV writer with append and deduplication support."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_csv(
    df: pd.DataFrame,
    path: Path,
    primary_keys: list[str],
) -> None:
    """Save DataFrame to CSV, appending and deduplicating on primary keys.

    If the file exists, new rows are appended and duplicates on the
    primary key columns are removed, keeping the latest (new) data.

    Args:
        df: New data to save.
        path: Path to the CSV file.
        primary_keys: Columns forming the unique key for deduplication.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and path.stat().st_size > 0:
        existing = pd.read_csv(path, dtype=str)
        combined = pd.concat([existing, df.astype(str)], ignore_index=True)
        combined = combined.drop_duplicates(subset=primary_keys, keep="last")
    else:
        combined = df

    combined.to_csv(path, index=False)


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file, returning empty DataFrame if it doesn't exist."""
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path)
    return pd.DataFrame()
