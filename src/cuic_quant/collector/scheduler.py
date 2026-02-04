"""Collection scheduler for automated background data collection.

This module provides a scheduler service that automates periodic data collection
from prediction markets using APScheduler for background job management.

Example:
    >>> from cuic_quant.collector import CollectionScheduler
    >>>
    >>> scheduler = CollectionScheduler(market_interval_minutes=15)
    >>> scheduler.start()
    >>> # ... scheduler runs in background ...
    >>> scheduler.stop()

The scheduler handles:
    - Periodic market data collection at configurable intervals
    - Periodic orderbook data collection at configurable intervals
    - Background execution using APScheduler
    - Graceful shutdown with job completion
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from cuic_quant.collector.polymarket_collector import PolymarketCollector

logger = logging.getLogger(__name__)


class CollectionScheduler:
    """Scheduler for automated periodic data collection.

    This scheduler uses APScheduler to run data collection jobs in the background
    at configurable intervals. It manages both market data collection and orderbook
    collection as separate jobs with independent schedules.

    Args:
        market_interval_minutes: Interval in minutes between market collection runs.
            Default is 15 minutes.
        orderbook_interval_minutes: Interval in minutes between orderbook collection
            runs. Default is 5 minutes.

    Attributes:
        collector: The PolymarketCollector instance used for data collection.
        market_interval_minutes: Configured interval for market collection.
        orderbook_interval_minutes: Configured interval for orderbook collection.

    Example:
        >>> scheduler = CollectionScheduler(
        ...     market_interval_minutes=15,
        ...     orderbook_interval_minutes=5,
        ... )
        >>> scheduler.start()
        >>> print(f"Running: {scheduler.is_running}")
        >>> jobs = scheduler.get_jobs()
        >>> for job in jobs:
        ...     print(f"Job {job['id']} next runs at {job['next_run']}")
        >>> scheduler.stop()
    """

    def __init__(
        self,
        market_interval_minutes: int = 15,
        orderbook_interval_minutes: int = 5,
    ) -> None:
        """Initialize the collection scheduler.

        Args:
            market_interval_minutes: Interval in minutes between market collection
                runs. Default is 15 minutes.
            orderbook_interval_minutes: Interval in minutes between orderbook
                collection runs. Default is 5 minutes.
        """
        self._scheduler = BackgroundScheduler()
        self.collector: PolymarketCollector = PolymarketCollector()
        self.market_interval_minutes = market_interval_minutes
        self.orderbook_interval_minutes = orderbook_interval_minutes

    def start(self) -> None:
        """Start the scheduler with configured collection jobs.

        Adds market collection and orderbook collection jobs to the scheduler
        with their respective intervals, then starts the background scheduler.

        The jobs will begin running immediately and repeat at the configured
        intervals until stop() is called.

        Example:
            >>> scheduler = CollectionScheduler()
            >>> scheduler.start()
            >>> print(f"Scheduler is running: {scheduler.is_running}")
        """
        if self._scheduler.running:
            logger.warning("Scheduler already running, skipping start")
            return

        # Add market collection job
        self._scheduler.add_job(
            self._collect_markets_job,
            trigger=IntervalTrigger(minutes=self.market_interval_minutes),
            id="collect_markets",
            name="Market Data Collection",
            replace_existing=True,
        )

        # Add orderbook collection job
        self._scheduler.add_job(
            self._collect_orderbooks_job,
            trigger=IntervalTrigger(minutes=self.orderbook_interval_minutes),
            id="collect_orderbooks",
            name="Orderbook Data Collection",
            replace_existing=True,
        )

        # Start the scheduler
        self._scheduler.start()

        logger.info(
            f"CollectionScheduler started - markets every {self.market_interval_minutes}m, "
            f"orderbooks every {self.orderbook_interval_minutes}m"
        )

    def stop(self) -> None:
        """Stop the scheduler gracefully.

        Shuts down the scheduler and waits for any running jobs to complete
        before returning. Sets is_running to False.

        Example:
            >>> scheduler = CollectionScheduler()
            >>> scheduler.start()
            >>> # ... do work ...
            >>> scheduler.stop()
            >>> print(f"Scheduler stopped: {not scheduler.is_running}")
        """
        self._scheduler.shutdown(wait=True)
        logger.info("CollectionScheduler stopped")

    def run_now(self) -> dict[str, Any]:
        """Run a full collection cycle immediately.

        Executes the collector's run_full_collection() method without waiting
        for the scheduled interval. Useful for testing or manual triggering.

        Returns:
            Dictionary with collection statistics from run_full_collection():
                - markets_fetched: Number of markets retrieved from API
                - markets_saved: Number of markets saved to database
                - price_points_saved: Number of price points created
                - orderbook_errors: Number of orderbook fetch errors
                - status: Overall status ("success", "partial", or "error")

        Example:
            >>> scheduler = CollectionScheduler()
            >>> result = scheduler.run_now()
            >>> print(f"Collected {result['markets_saved']} markets")
        """
        logger.info("Running immediate full collection")
        return self.collector.run_full_collection()

    def _collect_markets_job(self) -> None:
        """Private job function for scheduled market collection.

        Called by the scheduler at the configured market interval.
        Wraps the collector call in try/except for error resilience.
        """
        try:
            logger.debug("Scheduled market collection job starting")
            result = self.collector.collect_markets()
            logger.info(
                f"Scheduled market collection completed: "
                f"{result.get('markets_saved', 0)} markets saved"
            )
        except Exception as e:
            logger.error(f"Scheduled market collection job failed: {e}", exc_info=True)

    def _collect_orderbooks_job(self) -> None:
        """Private job function for scheduled orderbook collection.

        Called by the scheduler at the configured orderbook interval.
        Wraps the collector call in try/except for error resilience.
        """
        try:
            logger.debug("Scheduled orderbook collection job starting")
            result = self.collector.collect_orderbooks()
            logger.info(
                f"Scheduled orderbook collection completed: "
                f"{result.get('price_points_saved', 0)} price points saved"
            )
        except Exception as e:
            logger.error(f"Scheduled orderbook collection job failed: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running.

        Returns:
            True if the scheduler has been started and not stopped,
            False otherwise.

        Example:
            >>> scheduler = CollectionScheduler()
            >>> print(scheduler.is_running)  # False
            >>> scheduler.start()
            >>> print(scheduler.is_running)  # True
        """
        return self._scheduler.running

    def get_jobs(self) -> list[dict[str, Any]]:
        """Get information about all scheduled jobs.

        Returns a list of dictionaries containing information about each
        scheduled job, including its ID, name, and next scheduled run time.

        Returns:
            List of job information dictionaries with keys:
                - id: Unique job identifier
                - name: Human-readable job name
                - next_run: Datetime of next scheduled execution (or None)

        Example:
            >>> scheduler = CollectionScheduler()
            >>> scheduler.start()
            >>> for job in scheduler.get_jobs():
            ...     print(f"{job['name']}: next run at {job['next_run']}")
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time,
                }
            )
        return jobs
