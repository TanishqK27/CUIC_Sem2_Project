#!/usr/bin/env python3
"""Collect all historic Polymarket NBA data into CockroachDB.

This script collects:
- All NBA events (active + closed)
- All markets within those events
- Full price history for each market

Run manually: python scripts/collect_historic_data.py
Or via cron for scheduled execution.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from cuic_quant.collector import PolymarketCollector
from cuic_quant.database import get_engine, init_db, get_session
from cuic_quant.database.models import Event, MarketSnapshot, PricePoint

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "historic_collection.log"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Run historic data collection."""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("HISTORIC POLYMARKET DATA COLLECTION")
    logger.info(f"Started: {start_time.isoformat()}")
    logger.info("=" * 60)

    try:
        # Initialize database
        logger.info("Connecting to CockroachDB...")
        engine = get_engine()
        init_db(engine)
        logger.info("Database connected and schema ready")

        # Clear existing NBA data for fresh collection
        logger.info("Clearing existing NBA data...")
        with get_session(engine) as session:
            # Find NBA events
            nba_events = session.query(Event).filter(
                Event.slug.ilike('%nba%') | Event.category.ilike('%sport%')
            ).all()

            if nba_events:
                event_ids = [e.id for e in nba_events]
                # Delete price points for NBA markets
                nba_markets = session.query(MarketSnapshot).filter(
                    MarketSnapshot.event_id.in_(event_ids)
                ).all()
                market_ids = [m.id for m in nba_markets]

                if market_ids:
                    session.query(PricePoint).filter(
                        PricePoint.market_id.in_(market_ids)
                    ).delete(synchronize_session=False)

                # Delete NBA markets
                session.query(MarketSnapshot).filter(
                    MarketSnapshot.event_id.in_(event_ids)
                ).delete(synchronize_session=False)

                # Delete NBA events
                session.query(Event).filter(
                    Event.id.in_(event_ids)
                ).delete(synchronize_session=False)

                logger.info(f"Cleared {len(nba_events)} events, {len(nba_markets)} markets")
            else:
                logger.info("No existing NBA data to clear")

        # Create collector
        collector = PolymarketCollector(engine)

        # Collect NBA events with full price history
        logger.info("Collecting all NBA events with price history...")
        logger.info("This may take 15-30 minutes...")

        results = collector.collect_all_events(
            include_closed=True,
            include_price_history=True,
            keywords=["nba"],
        )

        # Log results
        logger.info("-" * 40)
        logger.info("COLLECTION COMPLETE")
        logger.info(f"  Events saved:       {results.get('events_saved', 0):,}")
        logger.info(f"  Markets saved:      {results.get('markets_saved', 0):,}")
        logger.info(f"  Price points saved: {results.get('price_points_saved', 0):,}")
        logger.info(f"  Errors:             {results.get('errors', 0)}")
        logger.info(f"  Status:             {results.get('status', 'unknown')}")

    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Duration: {duration}")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
