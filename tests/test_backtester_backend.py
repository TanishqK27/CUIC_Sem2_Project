"""Tests for backtester backend module."""

from __future__ import annotations

import pandas as pd
import pytest


class TestAlwaysBetHome:
    """Tests for the always_bet_home example strategy."""

    def test_returns_buy_home_action(self) -> None:
        """Should always return BUY_HOME action."""
        from cuic_quant.backtest.backtester_backend import always_bet_home

        row = pd.Series({
            "timestamp": pd.Timestamp("2026-01-01"),
            "game": "Lakers vs Celtics",
            "home_team": "Lakers",
            "away_team": "Celtics",
            "home_odds": 1.95,
            "away_odds": 2.05,
        })

        signal = always_bet_home(row)
        assert signal["action"] == "BUY_HOME"
        assert signal["size"] == 100.0
        assert signal["confidence"] == 0.5

    def test_accepts_context(self) -> None:
        """Should accept optional context dict without error."""
        from cuic_quant.backtest.backtester_backend import always_bet_home

        row = pd.Series({"home_odds": 1.95, "away_odds": 2.05})
        context = {"bankroll": 5000.0, "trade_count": 3}
        signal = always_bet_home(row, context)
        assert signal["action"] == "BUY_HOME"
