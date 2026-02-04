"""Collector module for automated data collection from prediction markets.

This module provides services for collecting data from various prediction
market platforms and storing it in the database for analysis.

Classes:
    - PolymarketCollector: Collects market data and orderbooks from Polymarket
"""

from cuic_quant.collector.polymarket_collector import PolymarketCollector

__all__ = ["PolymarketCollector"]
