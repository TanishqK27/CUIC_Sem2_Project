"""Collector module for automated data collection from prediction markets.

This module provides services for collecting data from various prediction
market platforms and storing it in the database for analysis.

Classes:
    - PolymarketCollector: Collects market data and orderbooks from Polymarket
    - CollectionScheduler: Schedules automated background data collection jobs
"""

from cuic_quant.collector.polymarket_collector import PolymarketCollector
from cuic_quant.collector.scheduler import CollectionScheduler

__all__ = ["PolymarketCollector", "CollectionScheduler"]
