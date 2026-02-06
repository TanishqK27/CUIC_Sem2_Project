"""Pytest configuration and shared fixtures.

This module contains fixtures that can be used across all tests.

Usage:
    Fixtures are automatically discovered by pytest.
    Simply include the fixture name as a parameter in your test function.

Example:
    def test_something(sample_prices):
        assert len(sample_prices) > 0
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_prices() -> list[float]:
    """Sample price data for testing strategies."""
    return [
        0.50,
        0.52,
        0.48,
        0.51,
        0.49,
        0.53,
        0.55,
        0.52,
        0.50,
        0.48,
        0.45,
        0.47,
        0.50,
        0.52,
        0.54,
        0.56,
        0.58,
        0.55,
        0.53,
        0.50,
        0.48,
        0.45,
        0.42,
        0.40,
    ]


@pytest.fixture
def sample_odds() -> dict[str, list[float]]:
    """Sample odds data for arbitrage testing."""
    return {
        "Bookmaker_A": [1.91, 2.05],
        "Bookmaker_B": [2.10, 1.80],
        "Bookmaker_C": [1.95, 1.95],
    }


@pytest.fixture
def sample_market_data() -> dict[str, Any]:
    """Sample market data for testing."""
    return {
        "id": "test_market_123",
        "question": "Will event X happen?",
        "description": "Test market description",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.65", "0.35"],
        "volume": "100000",
        "liquidity": "50000",
        "endDate": "2025-12-31T23:59:59Z",
        "status": "active",
    }


@pytest.fixture
def sample_game_odds() -> dict[str, Any]:
    """Sample game odds data for testing."""
    return {
        "id": "game_123",
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2025-02-15T00:00:00Z",
        "home_team": "Los Angeles Lakers",
        "away_team": "Boston Celtics",
        "bookmakers": [
            {
                "key": "draftkings",
                "title": "DraftKings",
                "last_update": "2025-02-14T12:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Los Angeles Lakers", "price": 2.10},
                            {"name": "Boston Celtics", "price": 1.80},
                        ],
                    }
                ],
            },
            {
                "key": "fanduel",
                "title": "FanDuel",
                "last_update": "2025-02-14T12:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Los Angeles Lakers", "price": 2.05},
                            {"name": "Boston Celtics", "price": 1.85},
                        ],
                    }
                ],
            },
        ],
    }


# =============================================================================
# Mock Client Fixtures
# =============================================================================


@pytest.fixture
def mock_kalshi_client() -> MagicMock:
    """Mock Kalshi client for testing without API calls."""
    client = MagicMock()
    client.is_authenticated = True
    client.get_markets.return_value = []
    client.get_balance.return_value = MagicMock(available=10000.0)
    return client


@pytest.fixture
def mock_odds_api_client() -> MagicMock:
    """Mock Odds API client for testing without API calls."""
    client = MagicMock()
    client.get_sports.return_value = []
    client.get_odds.return_value = []
    client.requests_remaining = 500
    return client


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def temp_env_vars(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up temporary environment variables for testing.

    Returns:
        Dict of environment variable names to values.
    """
    env_vars = {
        "ODDS_API_KEY": "test_odds_api_key",
        "KALSHI_EMAIL": "test@example.com",
        "KALSHI_PASSWORD": "test_password",
        "KALSHI_API_URL": "https://demo-api.kalshi.co/trade-api/v2",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


# =============================================================================
# Time-related Fixtures
# =============================================================================


@pytest.fixture
def fixed_datetime() -> datetime:
    """Return a fixed datetime for reproducible tests."""
    return datetime(2025, 2, 1, 12, 0, 0)


# =============================================================================
# Markers
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests requiring external APIs"
    )
    config.addinivalue_line("markers", "unit: marks unit tests")


# =============================================================================
# Hooks
# =============================================================================


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Modify test collection.

    - Skip integration tests unless --run-integration flag is passed
    - Add markers based on test location
    """
    run_integration = config.getoption("--run-integration", default=False)

    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")

    for item in items:
        # Skip integration tests unless explicitly requested
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)

        # Auto-add unit marker to non-integration tests
        if "integration" not in item.keywords:
            item.add_marker(pytest.mark.unit)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests that require external APIs",
    )
