#!/usr/bin/env python3
"""NBA data collection CLI.

Usage:
    # Full historical collection (all 4 seasons, ~17 hours)
    python scripts/collect_nba_stats.py --mode full

    # Resume interrupted collection
    python scripts/collect_nba_stats.py --mode full --resume

    # Daily incremental update (~1-2 min)
    python scripts/collect_nba_stats.py --mode update

    # Specific season only
    python scripts/collect_nba_stats.py --mode full --seasons 2024-25

    # Dry run
    python scripts/collect_nba_stats.py --mode update --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add src to path so we can import cuic_quant
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cuic_quant.data.nba.collector import NBACollector


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/nba_collection.log"),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect NBA stats from nba_api",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "update"],
        required=True,
        help="'full' for historical collection, 'update' for incremental",
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=None,
        help="Specific seasons to collect (e.g. 2024-25). Defaults to all 4.",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for CSVs (default: data)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry previously failed games",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be collected without making API calls",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    setup_logging(verbose=args.verbose)

    collector = NBACollector(
        output_dir=args.output_dir,
        seasons=args.seasons,
        resume=args.resume,
        retry_failed=args.retry_failed,
        dry_run=args.dry_run,
    )

    if args.mode == "full":
        collector.run_full()
    elif args.mode == "update":
        collector.run_update()


if __name__ == "__main__":
    main()
