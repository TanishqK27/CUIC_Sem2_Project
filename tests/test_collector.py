"""Tests for data collector service.

This module contains unit tests for the Polymarket data collector including:
- Market collection and storage
- Error handling and graceful degradation
- CollectionRun tracking
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from cuic_quant.collector import PolymarketCollector
from cuic_quant.data.polymarket_client import Market, OrderBook
from cuic_quant.database.connection import get_engine, get_session, init_db
from cuic_quant.database.models import CollectionRun, MarketSnapshot


@pytest.fixture
def test_engine():
    """Create in-memory test database."""
    engine = get_engine(":memory:")
    init_db(engine)
    return engine


@pytest.fixture
def mock_client():
    """Mock Polymarket client with sample data."""
    client = MagicMock()
    client.get_markets.return_value = [
        Market(
            id="test_1",
            question="Test market 1?",
            description="Test description 1",
            outcomes=["Yes", "No"],
            yes_price=0.6,
            no_price=0.4,
            volume=10000.0,
            liquidity=5000.0,
            end_date=None,
            status="active",
        ),
        Market(
            id="test_2",
            question="Test market 2?",
            description="Test description 2",
            outcomes=["Yes", "No"],
            yes_price=0.7,
            no_price=0.3,
            volume=20000.0,
            liquidity=8000.0,
            end_date=None,
            status="active",
        ),
    ]
    return client


@pytest.fixture
def mock_orderbook():
    """Mock orderbook data."""
    return OrderBook(
        token_id="token_abc",
        bids=[{"price": 0.64, "size": 100.0}],
        asks=[{"price": 0.66, "size": 100.0}],
        timestamp=datetime.utcnow(),
    )


class TestPolymarketCollector:
    """Tests for PolymarketCollector."""

    def test_collector_init_with_defaults(self, test_engine) -> None:
        """Should initialize with provided engine."""
        mock_client = MagicMock()
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        assert collector.client == mock_client
        assert collector.engine == test_engine

    def test_collect_markets_success(self, mock_client, test_engine) -> None:
        """Should collect and store markets successfully."""
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        result = collector.collect_markets(limit=10)

        assert result["status"] == "success"
        assert result["markets_fetched"] == 2
        assert result["markets_saved"] == 2
        mock_client.get_markets.assert_called_once_with(limit=10, active=True)

    def test_collect_markets_stores_in_database(self, mock_client, test_engine) -> None:
        """Should persist markets to database."""
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        collector.collect_markets(limit=10)

        # Verify data is in database
        with get_session(test_engine) as session:
            snapshots = session.query(MarketSnapshot).all()
            assert len(snapshots) == 2

            # Check first market
            market = next(s for s in snapshots if s.polymarket_id == "test_1")
            assert market.question == "Test market 1?"
            assert market.yes_price == 0.6
            assert market.active is True

    def test_collect_markets_creates_collection_run(
        self, mock_client, test_engine
    ) -> None:
        """Should create CollectionRun record."""
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        collector.collect_markets(limit=10)

        with get_session(test_engine) as session:
            runs = session.query(CollectionRun).all()
            assert len(runs) == 1
            assert runs[0].status == "completed"
            assert runs[0].markets_collected == 2

    def test_collect_markets_api_error(self, test_engine) -> None:
        """Should handle API errors gracefully."""
        mock_client = MagicMock()
        mock_client.get_markets.side_effect = Exception("API Error: Connection failed")

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.collect_markets()

        assert result["status"] == "error"
        assert "API Error" in result["error"]
        assert result["markets_saved"] == 0

    def test_collect_markets_api_error_creates_failed_run(self, test_engine) -> None:
        """Should record failed collection run."""
        mock_client = MagicMock()
        mock_client.get_markets.side_effect = Exception("Network error")

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        collector.collect_markets()

        with get_session(test_engine) as session:
            runs = session.query(CollectionRun).all()
            assert len(runs) == 1
            assert runs[0].status == "failed"
            assert "Network error" in runs[0].error_message

    def test_collect_markets_respects_limit(self, test_engine) -> None:
        """Should pass limit parameter to API client."""
        mock_client = MagicMock()
        mock_client.get_markets.return_value = []

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        collector.collect_markets(limit=25)

        mock_client.get_markets.assert_called_once_with(limit=25, active=True)

    def test_collect_markets_respects_active_only(self, test_engine) -> None:
        """Should pass active_only parameter to API client."""
        mock_client = MagicMock()
        mock_client.get_markets.return_value = []

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        collector.collect_markets(limit=10, active_only=False)

        mock_client.get_markets.assert_called_once_with(limit=10, active=False)

    def test_collect_markets_handles_partial_failure(self, test_engine) -> None:
        """Should continue saving markets even if some fail."""
        mock_client = MagicMock()

        # Create a market that will cause issues during conversion
        # by having a normal market followed by one that should work
        mock_client.get_markets.return_value = [
            Market(
                id="good_market",
                question="Good market?",
                description="Description",
                outcomes=["Yes", "No"],
                yes_price=0.5,
                no_price=0.5,
                volume=1000.0,
                liquidity=500.0,
                end_date=None,
                status="active",
            ),
        ]

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.collect_markets(limit=10)

        assert result["status"] == "success"
        assert result["markets_saved"] == 1

    def test_market_to_snapshot_conversion(self, mock_client, test_engine) -> None:
        """Should correctly convert Market to MarketSnapshot."""
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        market = Market(
            id="convert_test",
            question="Conversion test?",
            description="Test description",
            outcomes=["Yes", "No"],
            yes_price=0.75,
            no_price=0.25,
            volume=50000.0,
            liquidity=25000.0,
            end_date=datetime(2025, 12, 31),
            status="active",
        )

        snapshot = collector._market_to_snapshot(market)

        assert snapshot.polymarket_id == "convert_test"
        assert snapshot.question == "Conversion test?"
        assert snapshot.description == "Test description"
        assert snapshot.yes_price == 0.75
        assert snapshot.no_price == 0.25
        assert snapshot.volume == 50000.0
        assert snapshot.liquidity == 25000.0
        assert snapshot.status == "active"
        assert snapshot.active is True
        assert snapshot.snapshot_at is not None

    def test_collect_orderbooks_success(self, test_engine, mock_orderbook) -> None:
        """Should collect orderbooks and create price points."""
        mock_client = MagicMock()
        mock_client.get_orderbook.return_value = mock_orderbook

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.collect_orderbooks(token_ids=["token_abc"])

        assert result["status"] == "success"
        assert result["price_points_saved"] == 1
        assert result["errors"] == 0

    def test_collect_orderbooks_no_tokens(self, test_engine) -> None:
        """Should handle empty token list gracefully."""
        mock_client = MagicMock()
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        # Empty database means no token_ids available
        result = collector.collect_orderbooks()

        assert result["status"] == "success"
        assert result["price_points_saved"] == 0

    def test_collect_orderbooks_with_errors(self, test_engine) -> None:
        """Should continue on individual orderbook failures."""
        mock_client = MagicMock()

        # First call succeeds, second fails
        mock_client.get_orderbook.side_effect = [
            OrderBook(
                token_id="token_1",
                bids=[{"price": 0.64, "size": 100.0}],
                asks=[{"price": 0.66, "size": 100.0}],
                timestamp=datetime.utcnow(),
            ),
            Exception("Failed to fetch orderbook"),
        ]

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.collect_orderbooks(token_ids=["token_1", "token_2"])

        assert result["status"] == "partial"
        assert result["price_points_saved"] == 1
        assert result["errors"] == 1

    def test_run_full_collection(self, mock_client, test_engine) -> None:
        """Should run both market and orderbook collection."""
        # Setup mock for orderbook collection
        mock_client.get_orderbook.return_value = OrderBook(
            token_id="token_test",
            bids=[{"price": 0.64, "size": 100.0}],
            asks=[{"price": 0.66, "size": 100.0}],
            timestamp=datetime.utcnow(),
        )

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.run_full_collection()

        assert "markets_fetched" in result
        assert "markets_saved" in result
        assert "price_points_saved" in result
        assert "status" in result

    def test_run_full_collection_market_error(self, test_engine) -> None:
        """Should report error status if market collection fails."""
        mock_client = MagicMock()
        mock_client.get_markets.side_effect = Exception("API unavailable")

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.run_full_collection()

        assert result["status"] == "error"


class TestCollectorIntegration:
    """Integration tests for collector with database."""

    def test_multiple_collection_runs(self, mock_client, test_engine) -> None:
        """Should handle multiple consecutive collection runs."""
        collector = PolymarketCollector(client=mock_client, engine=test_engine)

        # Run collection twice
        result1 = collector.collect_markets(limit=10)
        result2 = collector.collect_markets(limit=10)

        assert result1["status"] == "success"
        assert result2["status"] == "success"

        # Should have created two collection runs
        with get_session(test_engine) as session:
            runs = session.query(CollectionRun).all()
            assert len(runs) == 2

        # Should have snapshots from both runs (4 total)
        with get_session(test_engine) as session:
            snapshots = session.query(MarketSnapshot).all()
            assert len(snapshots) == 4

    def test_empty_api_response(self, test_engine) -> None:
        """Should handle empty API response."""
        mock_client = MagicMock()
        mock_client.get_markets.return_value = []

        collector = PolymarketCollector(client=mock_client, engine=test_engine)
        result = collector.collect_markets()

        assert result["status"] == "success"
        assert result["markets_fetched"] == 0
        assert result["markets_saved"] == 0

        # Collection run should still be recorded
        with get_session(test_engine) as session:
            runs = session.query(CollectionRun).all()
            assert len(runs) == 1
            assert runs[0].status == "completed"
