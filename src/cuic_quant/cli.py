"""Command-line interface for CUIC Quant tools.

This module provides CLI commands for managing the Polymarket data collection
infrastructure, including database initialization, data collection, API server,
and background scheduling.

Example usage:
    # Initialize the database
    $ cuic-quant init-db

    # Run a data collection
    $ cuic-quant collect --limit 100

    # Start the API server
    $ cuic-quant serve --port 8000 --reload

    # Run the background scheduler
    $ cuic-quant scheduler --market-interval 15 --orderbook-interval 5

    # Show collection statistics
    $ cuic-quant stats
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import NoReturn


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI commands.

    Sets up logging with timestamps and appropriate log level based on
    the verbose flag.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise, use INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def cmd_init_db(args: argparse.Namespace) -> int:
    """Initialize the database schema.

    Creates all database tables defined in the ORM models. Safe to call
    multiple times - existing tables are not modified.

    Args:
        args: Parsed command-line arguments containing:
            - db_path: Optional path to the database file

    Returns:
        Exit code (0 for success).
    """
    from cuic_quant.database.connection import get_engine, init_db

    engine = get_engine(args.db_path)
    init_db(engine)

    db_display = args.db_path or "data/polymarket.db"
    print(f"Database initialized at: {db_display}")
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    """Run data collection from Polymarket.

    Fetches market data and optionally orderbook data from the Polymarket API
    and stores it in the database.

    Args:
        args: Parsed command-line arguments containing:
            - limit: Maximum number of markets to collect
            - full: If True, run full collection including orderbooks

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    from cuic_quant.collector import PolymarketCollector

    collector = PolymarketCollector()

    if args.full:
        print("Running full collection (markets + orderbooks)...")
        result = collector.run_full_collection()
        print(f"Markets fetched: {result.get('markets_fetched', 0)}")
        print(f"Markets saved: {result.get('markets_saved', 0)}")
        print(f"Price points saved: {result.get('price_points_saved', 0)}")
        print(f"Orderbook errors: {result.get('orderbook_errors', 0)}")
    else:
        print(f"Collecting markets (limit={args.limit})...")
        result = collector.collect_markets(limit=args.limit)
        print(f"Markets fetched: {result.get('markets_fetched', 0)}")
        print(f"Markets saved: {result.get('markets_saved', 0)}")

    print(f"Status: {result.get('status', 'unknown')}")

    if result.get("status") == "error":
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1

    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FastAPI server.

    Launches the API server using uvicorn with the specified configuration.

    Args:
        args: Parsed command-line arguments containing:
            - host: Host to bind to
            - port: Port to listen on
            - reload: Enable auto-reload for development

    Returns:
        Exit code (0 for success).
    """
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn not installed. Install with: pip install 'cuic-quant[server]'")
        return 1

    from cuic_quant.api import app

    print(f"Starting API server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_scheduler(args: argparse.Namespace) -> int:
    """Run the background collection scheduler.

    Starts a scheduler that periodically collects market data and orderbooks
    at configurable intervals.

    Args:
        args: Parsed command-line arguments containing:
            - market_interval: Minutes between market collection runs
            - orderbook_interval: Minutes between orderbook collection runs

    Returns:
        Exit code (0 for success).
    """
    import time

    from cuic_quant.collector import CollectionScheduler

    scheduler = CollectionScheduler(
        market_interval_minutes=args.market_interval,
        orderbook_interval_minutes=args.orderbook_interval,
    )

    print(
        f"Starting scheduler (markets: {args.market_interval}min, "
        f"orderbooks: {args.orderbook_interval}min)"
    )
    print("Press Ctrl+C to stop")

    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()

    print("Scheduler stopped")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show collection statistics.

    Displays statistics about the data stored in the database, including
    counts of markets, snapshots, and price points.

    Args:
        args: Parsed command-line arguments (not used).

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    from cuic_quant.database.repositories import MarketRepository

    repo = MarketRepository()

    try:
        stats = repo.get_collection_stats()
    except Exception as e:
        print(f"Error retrieving stats: {e}")
        print("Make sure the database is initialized: cuic-quant init-db")
        return 1

    print("Collection Statistics")
    print("=" * 40)
    print(f"  Unique markets:     {stats['total_markets']:,}")
    print(f"  Market snapshots:   {stats['total_snapshots']:,}")
    print(f"  Active markets:     {stats['active_markets']:,}")
    print(f"  Price points:       {stats['total_price_points']:,}")
    print()
    print("Date Range")
    print("-" * 40)
    print(f"  Oldest snapshot:    {stats['oldest_snapshot'] or 'N/A'}")
    print(f"  Newest snapshot:    {stats['newest_snapshot'] or 'N/A'}")
    print(f"  Oldest price:       {stats['oldest_price'] or 'N/A'}")
    print(f"  Newest price:       {stats['newest_price'] or 'N/A'}")

    return 0


def main() -> int | NoReturn:
    """Main CLI entry point.

    Parses command-line arguments and dispatches to the appropriate
    subcommand handler.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(
        prog="cuic-quant",
        description="CUIC Quant - Polymarket Data Collection Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  cuic-quant init-db                    Initialize the database
  cuic-quant collect --limit 100        Collect up to 100 markets
  cuic-quant collect --full             Full collection with orderbooks
  cuic-quant serve --port 8080          Start API server on port 8080
  cuic-quant scheduler                  Run background scheduler
  cuic-quant stats                      Show collection statistics
""",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG level) logging",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        metavar="COMMAND",
    )

    # init-db command
    init_parser = subparsers.add_parser(
        "init-db",
        help="Initialize the database schema",
        description="Create all database tables. Safe to run multiple times.",
    )
    init_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file (default: data/polymarket.db)",
    )
    init_parser.set_defaults(func=cmd_init_db)

    # collect command
    collect_parser = subparsers.add_parser(
        "collect",
        help="Run data collection from Polymarket",
        description="Fetch market data from the Polymarket API and store in database.",
    )
    collect_parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of markets to collect (default: 500)",
    )
    collect_parser.add_argument(
        "--full",
        action="store_true",
        help="Run full collection including orderbooks",
    )
    collect_parser.set_defaults(func=cmd_collect)

    # serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the FastAPI server",
        description="Launch the REST API server for accessing collected data.",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    serve_parser.set_defaults(func=cmd_serve)

    # scheduler command
    sched_parser = subparsers.add_parser(
        "scheduler",
        help="Run the background collection scheduler",
        description="Start a scheduler for periodic data collection.",
    )
    sched_parser.add_argument(
        "--market-interval",
        type=int,
        default=15,
        help="Minutes between market collection runs (default: 15)",
    )
    sched_parser.add_argument(
        "--orderbook-interval",
        type=int,
        default=5,
        help="Minutes between orderbook collection runs (default: 5)",
    )
    sched_parser.set_defaults(func=cmd_scheduler)

    # stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show collection statistics",
        description="Display statistics about data stored in the database.",
    )
    stats_parser.set_defaults(func=cmd_stats)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.verbose)

    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
