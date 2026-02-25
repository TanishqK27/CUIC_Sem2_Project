#!/usr/bin/env python3
"""Merge parallel NBA worker outputs into the main data directory.

Reads CSVs from data/worker-*/  directories, deduplicates using
the existing save_csv() logic, merges checkpoint JSONs, and prints
a summary.

Usage:
    # Merge worker outputs into data/
    python scripts/merge_nba_workers.py

    # Custom paths
    python scripts/merge_nba_workers.py --input-dir data --output-dir data

    # Remove worker directories after merging
    python scripts/merge_nba_workers.py --cleanup
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cuic_quant.data.nba.constants import CSV_CONFIG
from cuic_quant.data.nba.csv_writer import save_csv

import pandas as pd


def find_worker_dirs(input_dir: Path) -> list[Path]:
    """Find all worker-N directories."""
    dirs = sorted(input_dir.glob("worker-*"))
    return [d for d in dirs if d.is_dir()]


def merge_csvs(worker_dirs: list[Path], output_dir: Path) -> dict[str, int]:
    """Merge CSVs from all workers into output_dir using save_csv dedup.

    Returns:
        Dict of csv_name -> total row count after merge.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    row_counts: dict[str, int] = {}

    for name, config in CSV_CONFIG.items():
        filename = config["file"]
        pk = config["pk"]

        # Collect all worker CSVs for this file
        frames = []
        for worker_dir in worker_dirs:
            csv_path = worker_dir / filename
            if csv_path.exists() and csv_path.stat().st_size > 0:
                try:
                    df = pd.read_csv(csv_path, dtype=str)
                    frames.append(df)
                except Exception as e:
                    print(f"  WARNING: Failed to read {csv_path}: {e}")

        if not frames:
            continue

        combined = pd.concat(frames, ignore_index=True)
        output_path = output_dir / filename

        # Use save_csv which handles append + dedup against existing data
        save_csv(combined, output_path, pk)

        # Read back to get final count
        final = pd.read_csv(output_path)
        row_counts[filename] = len(final)
        print(f"  {filename}: {len(final):,} rows (from {len(frames)} workers)")

    return row_counts


def merge_checkpoints(worker_dirs: list[Path], output_dir: Path) -> dict:
    """Merge checkpoint JSONs from all workers.

    Takes the union of all collected games and errors.
    """
    merged = {
        "games_collected": {"boxscores": []},
        "game_datasets": {},
        "errors": [],
        "total_api_calls": 0,
    }

    all_games = set()

    for worker_dir in worker_dirs:
        ckpt_path = worker_dir / ".nba_checkpoint.json"
        if not ckpt_path.exists():
            continue

        try:
            data = json.loads(ckpt_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Union of collected games
        for game_id in data.get("games_collected", {}).get("boxscores", []):
            all_games.add(game_id)

        # Union of game datasets
        for game_id, datasets in data.get("game_datasets", {}).items():
            if game_id not in merged["game_datasets"]:
                merged["game_datasets"][game_id] = datasets
            else:
                # Keep the more complete entry
                if len(datasets) > len(merged["game_datasets"][game_id]):
                    merged["game_datasets"][game_id] = datasets

        # Collect all errors
        merged["errors"].extend(data.get("errors", []))
        merged["total_api_calls"] += data.get("total_api_calls", 0)

    merged["games_collected"]["boxscores"] = sorted(all_games)

    # Merge into existing checkpoint if present
    output_ckpt = output_dir / ".nba_checkpoint.json"
    if output_ckpt.exists():
        try:
            existing = json.loads(output_ckpt.read_text())
            # Preserve non-boxscore fields from existing checkpoint
            existing_games = set(existing.get("games_collected", {}).get("boxscores", []))
            all_games |= existing_games
            merged["games_collected"]["boxscores"] = sorted(all_games)

            # Preserve other categories
            for cat, ids in existing.get("games_collected", {}).items():
                if cat != "boxscores":
                    merged["games_collected"][cat] = ids

            # Merge game_datasets
            for game_id, datasets in existing.get("game_datasets", {}).items():
                if game_id not in merged["game_datasets"]:
                    merged["game_datasets"][game_id] = datasets

            # Preserve other fields
            merged["last_update"] = existing.get("last_update")
            merged["seasons_completed"] = existing.get("seasons_completed", [])
        except (json.JSONDecodeError, OSError):
            pass

    output_ckpt.write_text(json.dumps(merged, indent=2))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge parallel NBA worker outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-dir", default="data",
        help="Directory containing worker-N subdirectories (default: data)",
    )
    parser.add_argument(
        "--output-dir", default="data",
        help="Directory to write merged CSVs (default: data)",
    )
    parser.add_argument(
        "--cleanup", action="store_true",
        help="Remove worker directories after merging",
    )

    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    worker_dirs = find_worker_dirs(input_dir)
    if not worker_dirs:
        print(f"No worker directories found in {input_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  NBA Worker Output Merger")
    print(f"  Workers found: {len(worker_dirs)}")
    print(f"  Input: {input_dir.resolve()}")
    print(f"  Output: {output_dir.resolve()}")
    print(f"{'='*60}")

    # Merge CSVs
    print(f"\n--- Merging CSVs ---")
    row_counts = merge_csvs(worker_dirs, output_dir)

    if not row_counts:
        print("  No CSV data found in worker directories")
        sys.exit(1)

    # Merge checkpoints
    print(f"\n--- Merging checkpoints ---")
    merged_ckpt = merge_checkpoints(worker_dirs, output_dir)
    total_games = len(merged_ckpt["games_collected"].get("boxscores", []))
    total_errors = len(merged_ckpt.get("errors", []))
    print(f"  Games collected: {total_games:,}")
    print(f"  Errors: {total_errors:,}")

    # Incomplete games
    all_expected = {"traditional_player", "traditional_team", "advanced", "hustle", "tracking"}
    incomplete = 0
    for game_id, datasets in merged_ckpt.get("game_datasets", {}).items():
        if all_expected - set(datasets):
            incomplete += 1
    if incomplete:
        print(f"  Games with missing datasets: {incomplete}")

    # Cleanup
    if args.cleanup:
        print(f"\n--- Cleanup ---")
        for worker_dir in worker_dirs:
            shutil.rmtree(worker_dir)
            print(f"  Removed {worker_dir}")
        print(f"  -> {len(worker_dirs)} worker directories removed")

    # Summary
    print(f"\n{'='*60}")
    print(f"  MERGE COMPLETE")
    print(f"  Total games: {total_games:,}")
    print(f"  Output files:")
    for filename, count in sorted(row_counts.items()):
        print(f"    {filename}: {count:,} rows")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
