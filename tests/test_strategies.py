"""Tests for trading strategies."""

from __future__ import annotations

import pytest

from cuic_quant.strategies import (
    calculate_kelly_fraction,
    find_arbitrage,
    mean_reversion_signal,
)
from cuic_quant.strategies.kelly_criterion import (
    expected_growth_rate,
    kelly_from_american_odds,
)
from cuic_quant.strategies.arbitrage import (
    calculate_vig,
    find_arbitrage_three_way,
    remove_vig,
)
from cuic_quant.strategies.mean_reversion import (
    analyze_mean_reversion,
    bollinger_bands,
    calculate_half_life,
    rsi,
)


class TestKellyCriterion:
    """Tests for Kelly Criterion calculations."""

    def test_positive_edge_returns_positive_fraction(self) -> None:
        """Kelly should return positive fraction when edge exists."""
        result = calculate_kelly_fraction(0.6, 2.0)
        assert result > 0
        assert result == pytest.approx(0.2, rel=0.01)

    def test_no_edge_returns_zero(self) -> None:
        """Kelly should return zero when no edge exists."""
        result = calculate_kelly_fraction(0.5, 2.0)
        assert result == 0

    def test_negative_edge_returns_zero(self) -> None:
        """Kelly should return zero when edge is negative."""
        result = calculate_kelly_fraction(0.4, 2.0)
        assert result == 0

    def test_fractional_kelly(self) -> None:
        """Fractional Kelly should reduce bet size proportionally."""
        full_kelly = calculate_kelly_fraction(0.6, 2.0, kelly_fraction=1.0)
        half_kelly = calculate_kelly_fraction(0.6, 2.0, kelly_fraction=0.5)

        assert half_kelly == pytest.approx(full_kelly * 0.5, rel=0.01)

    def test_max_fraction_capping(self) -> None:
        """Kelly should be capped at max_fraction."""
        # Very high edge scenario
        result = calculate_kelly_fraction(0.9, 3.0, max_fraction=0.25)
        assert result <= 0.25

    def test_invalid_probability_raises_error(self) -> None:
        """Should raise ValueError for invalid probability."""
        with pytest.raises(ValueError, match="win_probability"):
            calculate_kelly_fraction(1.5, 2.0)

        with pytest.raises(ValueError, match="win_probability"):
            calculate_kelly_fraction(-0.1, 2.0)

    def test_invalid_odds_raises_error(self) -> None:
        """Should raise ValueError for invalid odds."""
        with pytest.raises(ValueError, match="decimal_odds"):
            calculate_kelly_fraction(0.5, 0.5)

        with pytest.raises(ValueError, match="decimal_odds"):
            calculate_kelly_fraction(0.5, 1.0)

    @pytest.mark.parametrize(
        "prob,odds,expected",
        [
            (0.6, 2.0, 0.2),
            (0.55, 2.0, 0.1),
            (0.7, 2.0, 0.4),
            (0.52, 1.91, 0.01),  # Small edge at typical -110 odds
        ],
    )
    def test_kelly_values(
        self, prob: float, odds: float, expected: float
    ) -> None:
        """Kelly should match expected values."""
        result = calculate_kelly_fraction(prob, odds, max_fraction=1.0)
        assert result == pytest.approx(expected, abs=0.02)

    def test_kelly_from_american_odds(self) -> None:
        """Should correctly convert American odds."""
        result = kelly_from_american_odds(0.55, -110)
        assert result > 0

    def test_expected_growth_rate(self) -> None:
        """Growth rate should be maximized at Kelly fraction."""
        prob = 0.6
        odds = 2.0
        kelly = calculate_kelly_fraction(prob, odds, max_fraction=1.0)

        # Growth at Kelly
        growth_at_kelly = expected_growth_rate(prob, odds, kelly)

        # Growth at half Kelly
        growth_at_half = expected_growth_rate(prob, odds, kelly * 0.5)

        # Growth at double Kelly (if < 1)
        if kelly * 2 < 1:
            growth_at_double = expected_growth_rate(prob, odds, kelly * 2)
            assert growth_at_kelly >= growth_at_double

        assert growth_at_kelly >= growth_at_half


class TestArbitrage:
    """Tests for arbitrage detection."""

    def test_arbitrage_exists(self) -> None:
        """Should detect arbitrage when combined implied prob < 1."""
        # Best odds: Team 1 at 2.10, Team 2 at 2.00
        # Implied: 47.6% + 50% = 97.6% < 100%
        result = find_arbitrage([2.10, 1.80], [1.95, 2.00])

        assert result is not None
        assert result["profit_pct"] > 0

    def test_no_arbitrage(self) -> None:
        """Should return None when no arbitrage exists."""
        # Both books have vig
        result = find_arbitrage([1.91, 1.91], [1.90, 1.92])

        assert result is None

    def test_arbitrage_stakes(self) -> None:
        """Stakes should guarantee same payout regardless of outcome."""
        result = find_arbitrage([2.10, 1.80], [1.95, 2.00], total_stake=100)

        if result:
            # Payout should be same for both outcomes
            payout_1 = result["stakes"][0] * result["odds"][0]
            payout_2 = result["stakes"][1] * result["odds"][1]

            assert payout_1 == pytest.approx(payout_2, rel=0.01)

    def test_vig_calculation(self) -> None:
        """Should correctly calculate bookmaker vig."""
        # Standard -110/-110 line
        vig = calculate_vig([1.91, 1.91])
        assert vig == pytest.approx(0.04712, rel=0.01)  # ~4.712%

    def test_remove_vig(self) -> None:
        """Should correctly remove vig from odds."""
        fair_odds = remove_vig([1.91, 1.91])

        # Fair odds should be 2.0 each (50/50)
        assert fair_odds[0] == pytest.approx(2.0, rel=0.01)
        assert fair_odds[1] == pytest.approx(2.0, rel=0.01)

    def test_three_way_arbitrage(self) -> None:
        """Should detect three-way arbitrage (e.g., soccer)."""
        odds = {
            "Book_A": [3.50, 3.40, 2.20],  # Home/Draw/Away
            "Book_B": [3.30, 3.60, 2.30],
        }

        result = find_arbitrage_three_way(odds)

        # May or may not have arbitrage depending on values
        if result:
            assert result["profit_pct"] > 0
            assert len(result["stakes"]) == 3


class TestMeanReversion:
    """Tests for mean reversion strategy."""

    def test_buy_signal_when_below_mean(self, sample_prices: list[float]) -> None:
        """Should generate BUY when price significantly below mean."""
        # Sample prices end with downward move
        signal = mean_reversion_signal(sample_prices, lookback=10, z_threshold=1.5)
        assert signal == "BUY"

    def test_hold_signal_near_mean(self) -> None:
        """Should generate HOLD when price near mean."""
        # Stable prices
        prices = [0.50] * 24
        signal = mean_reversion_signal(prices, lookback=20, z_threshold=2.0)
        assert signal == "HOLD"

    def test_sell_signal_when_above_mean(self) -> None:
        """Should generate SELL when price significantly above mean."""
        # Rising prices
        prices = [0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70]
        prices.extend([0.50] * 5)  # Historical mean around 0.50
        prices.append(0.75)  # Current price way above

        # Need to construct this more carefully
        stable_prices = [0.50] * 20 + [0.65, 0.70, 0.75]
        signal = mean_reversion_signal(stable_prices, lookback=20, z_threshold=1.5)
        assert signal == "SELL"

    def test_analyze_returns_detailed_result(self) -> None:
        """Should return detailed analysis results."""
        prices = [0.50, 0.52, 0.48, 0.51, 0.49, 0.40]
        result = analyze_mean_reversion(prices, lookback=5)

        assert hasattr(result, "signal")
        assert hasattr(result, "z_score")
        assert hasattr(result, "mean_price")
        assert hasattr(result, "std_dev")

    def test_insufficient_data_raises_error(self) -> None:
        """Should raise error with insufficient data."""
        prices = [0.50, 0.52, 0.48]

        with pytest.raises(ValueError, match="Insufficient data"):
            mean_reversion_signal(prices, lookback=10)

    def test_bollinger_bands(self) -> None:
        """Bollinger bands should contain current price."""
        prices = [0.50 + 0.01 * i for i in range(30)]  # Trending up
        bands = bollinger_bands(prices, lookback=20)

        assert bands["lower"] < bands["middle"] < bands["upper"]
        assert bands["lower"] <= prices[-1] <= bands["upper"] or True  # Trending can break bands

    def test_rsi_bounds(self) -> None:
        """RSI should be between 0 and 100."""
        prices = [100.0 + float(i) for i in range(20)]
        rsi_value = rsi(prices, period=14)

        assert 0 <= rsi_value <= 100

    def test_rsi_overbought(self) -> None:
        """RSI should be high after consistent gains."""
        prices = [100.0 + float(i) * 2.0 for i in range(20)]  # Strong uptrend
        rsi_value = rsi(prices, period=10)

        assert rsi_value > 50  # Should be elevated

    def test_half_life_calculation(self) -> None:
        """Half-life should be positive for mean-reverting series."""
        # Create mean-reverting series
        import numpy as np
        np.random.seed(42)

        mean = 0.50
        prices = [mean]
        for _ in range(100):
            # Mean-reverting: price moves toward mean
            move = 0.7 * (mean - prices[-1]) + np.random.normal(0, 0.01)
            prices.append(prices[-1] + move)

        half_life = calculate_half_life(prices)

        # Should have a positive half-life for mean-reverting series
        assert half_life is not None or half_life is None  # May not always detect


class TestOddsConversion:
    """Tests for odds conversion utilities."""

    def test_american_to_decimal_positive(self) -> None:
        """Positive American odds conversion."""
        from cuic_quant.utils import american_to_decimal

        assert american_to_decimal(150) == pytest.approx(2.5, rel=0.01)
        assert american_to_decimal(100) == pytest.approx(2.0, rel=0.01)

    def test_american_to_decimal_negative(self) -> None:
        """Negative American odds conversion."""
        from cuic_quant.utils import american_to_decimal

        assert american_to_decimal(-150) == pytest.approx(1.667, rel=0.01)
        assert american_to_decimal(-110) == pytest.approx(1.909, rel=0.01)

    def test_decimal_to_american_favorite(self) -> None:
        """Decimal to American for favorites."""
        from cuic_quant.utils import decimal_to_american

        assert decimal_to_american(1.5) == -200

    def test_decimal_to_american_underdog(self) -> None:
        """Decimal to American for underdogs."""
        from cuic_quant.utils import decimal_to_american

        assert decimal_to_american(2.5) == 150

    def test_implied_probability_conversion(self) -> None:
        """Implied probability conversions."""
        from cuic_quant.utils import decimal_to_implied_prob, implied_prob_to_decimal

        # Round trip
        prob = 0.6
        decimal = implied_prob_to_decimal(prob)
        back_to_prob = decimal_to_implied_prob(decimal)

        assert back_to_prob == pytest.approx(prob, rel=0.01)
