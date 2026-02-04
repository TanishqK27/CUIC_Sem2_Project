"""Tests for database models and repository.

This module contains unit tests for the database layer including:
- MarketSnapshot and PricePoint models
- Database connection utilities
- MarketRepository query and persistence methods
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from cuic_quant.database.connection import get_engine, get_session, init_db
from cuic_quant.database.models import Base, MarketSnapshot, PricePoint
from cuic_quant.database.repositories import MarketRepository


@pytest.fixture
def test_engine():
    """Create in-memory test database."""
    engine = get_engine(":memory:")
    init_db(engine)
    return engine


@pytest.fixture
def sample_market() -> MarketSnapshot:
    """Sample market for testing."""
    return MarketSnapshot(
        polymarket_id="test_123",
        question="Will it rain tomorrow?",
        yes_price=0.65,
        no_price=0.35,
        volume=100000.0,
        liquidity=50000.0,
        status="active",
        active=True,
    )


@pytest.fixture
def sample_price_point() -> PricePoint:
    """Sample price point for testing."""
    return PricePoint(
        token_id="token_abc",
        price=0.65,
        timestamp=datetime.utcnow(),
        best_bid=0.64,
        best_ask=0.66,
        spread=0.02,
    )


class TestMarketSnapshot:
    """Tests for MarketSnapshot model."""

    def test_create_market(self, test_engine, sample_market) -> None:
        """Should create market snapshot with all fields."""
        with get_session(test_engine) as session:
            session.add(sample_market)
            session.flush()

            assert sample_market.id is not None
            assert sample_market.polymarket_id == "test_123"
            assert sample_market.question == "Will it rain tomorrow?"
            assert sample_market.yes_price == 0.65
            assert sample_market.no_price == 0.35

    def test_market_defaults(self, test_engine) -> None:
        """Should set default values for optional fields."""
        market = MarketSnapshot(
            polymarket_id="test_defaults",
            question="Test question?",
            yes_price=0.5,
            no_price=0.5,
        )

        with get_session(test_engine) as session:
            session.add(market)
            session.flush()

            assert market.id is not None
            assert market.active is True
            assert market.snapshot_at is not None
            assert market.volume is None  # Optional field

    def test_market_repr(self, test_engine, sample_market) -> None:
        """Should return meaningful string representation."""
        with get_session(test_engine) as session:
            session.add(sample_market)
            session.flush()

            repr_str = repr(sample_market)
            assert "MarketSnapshot" in repr_str
            assert "test_123" in repr_str

    def test_multiple_snapshots_same_market(self, test_engine) -> None:
        """Should allow multiple snapshots for same market."""
        snapshot1 = MarketSnapshot(
            polymarket_id="market_xyz",
            question="Test market?",
            yes_price=0.50,
            no_price=0.50,
            snapshot_at=datetime.utcnow() - timedelta(hours=1),
        )
        snapshot2 = MarketSnapshot(
            polymarket_id="market_xyz",
            question="Test market?",
            yes_price=0.55,
            no_price=0.45,
            snapshot_at=datetime.utcnow(),
        )

        with get_session(test_engine) as session:
            session.add_all([snapshot1, snapshot2])
            session.flush()

            assert snapshot1.id != snapshot2.id
            assert snapshot1.yes_price != snapshot2.yes_price


class TestPricePoint:
    """Tests for PricePoint model."""

    def test_create_price_point(self, test_engine, sample_price_point) -> None:
        """Should create price point with all fields."""
        with get_session(test_engine) as session:
            session.add(sample_price_point)
            session.flush()

            assert sample_price_point.id is not None
            assert sample_price_point.token_id == "token_abc"
            assert sample_price_point.price == 0.65
            assert sample_price_point.spread == 0.02

    def test_price_point_defaults(self, test_engine) -> None:
        """Should set default values."""
        price_point = PricePoint(
            token_id="token_xyz",
            price=0.70,
            timestamp=datetime.utcnow(),
        )

        with get_session(test_engine) as session:
            session.add(price_point)
            session.flush()

            assert price_point.id is not None
            assert price_point.created_at is not None
            assert price_point.best_bid is None
            assert price_point.best_ask is None

    def test_price_point_repr(self, test_engine, sample_price_point) -> None:
        """Should return meaningful string representation."""
        with get_session(test_engine) as session:
            session.add(sample_price_point)
            session.flush()

            repr_str = repr(sample_price_point)
            assert "PricePoint" in repr_str
            assert "token_abc" in repr_str


class TestMarketRepository:
    """Tests for MarketRepository."""

    def test_repository_init_with_engine(self, test_engine) -> None:
        """Should initialize with custom engine."""
        repo = MarketRepository(engine=test_engine)
        assert repo._engine == test_engine

    def test_get_latest_markets(self, test_engine, sample_market) -> None:
        """Should return latest markets."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)
        markets = repo.get_latest_markets(limit=10)

        assert len(markets) == 1
        assert markets[0].polymarket_id == "test_123"

    def test_get_latest_markets_empty(self, test_engine) -> None:
        """Should return empty list when no markets."""
        repo = MarketRepository(engine=test_engine)
        markets = repo.get_latest_markets(limit=10)

        assert markets == []

    def test_get_latest_markets_active_only(self, test_engine) -> None:
        """Should filter by active status."""
        active_market = MarketSnapshot(
            polymarket_id="active_1",
            question="Active market?",
            yes_price=0.5,
            no_price=0.5,
            active=True,
        )
        inactive_market = MarketSnapshot(
            polymarket_id="inactive_1",
            question="Inactive market?",
            yes_price=0.5,
            no_price=0.5,
            active=False,
        )

        with get_session(test_engine) as session:
            session.add_all([active_market, inactive_market])

        repo = MarketRepository(engine=test_engine)

        # Active only (default)
        active_results = repo.get_latest_markets(limit=10, active_only=True)
        assert len(active_results) == 1
        assert active_results[0].polymarket_id == "active_1"

        # All markets
        all_results = repo.get_latest_markets(limit=10, active_only=False)
        assert len(all_results) == 2

    def test_get_market_by_id(self, test_engine, sample_market) -> None:
        """Should find market by polymarket_id."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)
        market = repo.get_market_by_id("test_123")

        assert market is not None
        assert market.polymarket_id == "test_123"
        assert market.question == "Will it rain tomorrow?"

    def test_get_market_by_id_not_found(self, test_engine) -> None:
        """Should return None for non-existent market."""
        repo = MarketRepository(engine=test_engine)
        market = repo.get_market_by_id("nonexistent_market")

        assert market is None

    def test_get_markets_df(self, test_engine, sample_market) -> None:
        """Should return DataFrame with market data."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)
        df = repo.get_markets_df(limit=10)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "question" in df.columns
        assert "yes_price" in df.columns
        assert df.iloc[0]["yes_price"] == 0.65

    def test_get_markets_df_empty(self, test_engine) -> None:
        """Should return empty DataFrame when no markets."""
        repo = MarketRepository(engine=test_engine)
        df = repo.get_markets_df(limit=10)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "question" in df.columns

    def test_search_markets(self, test_engine, sample_market) -> None:
        """Should search by question text."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)

        # Should find market with "rain"
        results = repo.search_markets("rain")
        assert len(results) == 1

        # Should not find market with "snow"
        results = repo.search_markets("snow")
        assert len(results) == 0

    def test_search_markets_case_insensitive(self, test_engine, sample_market) -> None:
        """Should perform case-insensitive search."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)

        # Different cases should all match
        assert len(repo.search_markets("RAIN")) == 1
        assert len(repo.search_markets("Rain")) == 1
        assert len(repo.search_markets("rain")) == 1

    def test_save_market_snapshot(self, test_engine) -> None:
        """Should save and return market with generated id."""
        repo = MarketRepository(engine=test_engine)
        snapshot = MarketSnapshot(
            polymarket_id="new_market",
            question="Will X happen?",
            yes_price=0.5,
            no_price=0.5,
        )

        saved = repo.save_market_snapshot(snapshot)

        assert saved.id is not None
        assert saved.polymarket_id == "new_market"

        # Verify it's in the database
        fetched = repo.get_market_by_id("new_market")
        assert fetched is not None

    def test_bulk_save_markets(self, test_engine) -> None:
        """Should bulk save multiple snapshots."""
        repo = MarketRepository(engine=test_engine)
        snapshots = [
            MarketSnapshot(
                polymarket_id=f"bulk_{i}",
                question=f"Question {i}?",
                yes_price=0.5,
                no_price=0.5,
            )
            for i in range(5)
        ]

        count = repo.bulk_save_markets(snapshots)

        assert count == 5

        # Verify all are saved
        markets = repo.get_latest_markets(limit=10)
        assert len(markets) == 5

    def test_bulk_save_markets_empty(self, test_engine) -> None:
        """Should handle empty list."""
        repo = MarketRepository(engine=test_engine)
        count = repo.bulk_save_markets([])

        assert count == 0

    def test_get_price_history(self, test_engine) -> None:
        """Should return price history for token."""
        # Create multiple price points
        now = datetime.utcnow()
        points = [
            PricePoint(
                token_id="token_history",
                price=0.5 + i * 0.01,
                timestamp=now + timedelta(hours=i),
            )
            for i in range(5)
        ]

        with get_session(test_engine) as session:
            session.add_all(points)

        repo = MarketRepository(engine=test_engine)
        history = repo.get_price_history("token_history")

        assert len(history) == 5
        # Should be ordered by timestamp ascending
        assert history[0].price < history[-1].price

    def test_get_price_history_with_date_filter(self, test_engine) -> None:
        """Should filter price history by date range."""
        now = datetime.utcnow()
        points = [
            PricePoint(
                token_id="token_filter",
                price=0.5,
                timestamp=now - timedelta(days=2),
            ),
            PricePoint(
                token_id="token_filter",
                price=0.6,
                timestamp=now - timedelta(days=1),
            ),
            PricePoint(
                token_id="token_filter",
                price=0.7,
                timestamp=now,
            ),
        ]

        with get_session(test_engine) as session:
            session.add_all(points)

        repo = MarketRepository(engine=test_engine)

        # Filter to last day only
        history = repo.get_price_history(
            "token_filter",
            start_date=now - timedelta(hours=25),
        )
        assert len(history) == 2

    def test_get_price_history_df(self, test_engine) -> None:
        """Should return price history as DataFrame."""
        now = datetime.utcnow()
        point = PricePoint(
            token_id="token_df",
            price=0.65,
            timestamp=now,
            best_bid=0.64,
            best_ask=0.66,
            spread=0.02,
        )

        with get_session(test_engine) as session:
            session.add(point)

        repo = MarketRepository(engine=test_engine)
        df = repo.get_price_history_df("token_df")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "price" in df.columns
        assert df.iloc[0]["price"] == 0.65

    def test_get_collection_stats(self, test_engine, sample_market) -> None:
        """Should return collection statistics."""
        with get_session(test_engine) as session:
            session.add(sample_market)

        repo = MarketRepository(engine=test_engine)
        stats = repo.get_collection_stats()

        assert stats["total_markets"] == 1
        assert stats["total_snapshots"] == 1
        assert stats["active_markets"] == 1

    def test_get_collection_stats_empty(self, test_engine) -> None:
        """Should return zeros for empty database."""
        repo = MarketRepository(engine=test_engine)
        stats = repo.get_collection_stats()

        assert stats["total_markets"] == 0
        assert stats["total_snapshots"] == 0
        assert stats["total_price_points"] == 0

    def test_get_top_markets_by_volume(self, test_engine) -> None:
        """Should return markets ordered by volume."""
        markets = [
            MarketSnapshot(
                polymarket_id="low_vol",
                question="Low volume?",
                yes_price=0.5,
                no_price=0.5,
                volume=1000.0,
            ),
            MarketSnapshot(
                polymarket_id="high_vol",
                question="High volume?",
                yes_price=0.5,
                no_price=0.5,
                volume=100000.0,
            ),
            MarketSnapshot(
                polymarket_id="mid_vol",
                question="Mid volume?",
                yes_price=0.5,
                no_price=0.5,
                volume=10000.0,
            ),
        ]

        with get_session(test_engine) as session:
            session.add_all(markets)

        repo = MarketRepository(engine=test_engine)
        top_markets = repo.get_top_markets_by_volume(limit=10)

        assert len(top_markets) == 3
        assert top_markets[0].polymarket_id == "high_vol"
        assert top_markets[1].polymarket_id == "mid_vol"
        assert top_markets[2].polymarket_id == "low_vol"
