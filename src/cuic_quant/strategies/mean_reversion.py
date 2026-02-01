"""Mean reversion strategies for prediction markets.

Mean reversion strategies exploit the tendency of prices to return to
their historical average after large deviations. In prediction markets,
this can occur after news-driven overreactions.

Example:
    >>> from cuic_quant.strategies import mean_reversion_signal
    >>>
    >>> # Price history for a market
    >>> prices = [0.50, 0.52, 0.48, 0.45, 0.35]  # Recent drop
    >>> signal = mean_reversion_signal(prices)
    >>> print(f"Signal: {signal}")  # Likely "BUY" due to low price

Note:
    - Mean reversion works best in markets with stable fundamentals
    - News-driven moves may represent permanent information shifts
    - See docs/research/methodology.md for backtesting guidelines
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass
class MeanReversionResult:
    """Result of mean reversion analysis."""

    signal: Literal["BUY", "SELL", "HOLD"]
    z_score: float
    current_price: float
    mean_price: float
    std_dev: float
    deviation_pct: float


def mean_reversion_signal(
    prices: list[float] | np.ndarray,
    lookback: int = 24,
    z_threshold: float = 2.0,
) -> Literal["BUY", "SELL", "HOLD"]:
    """Generate a mean reversion trading signal.

    The strategy:
    - BUY when price is significantly below the mean (negative z-score)
    - SELL when price is significantly above the mean (positive z-score)
    - HOLD when price is within normal range

    Args:
        prices: Historical prices (most recent last).
        lookback: Number of periods for mean/std calculation.
        z_threshold: Z-score threshold for signal generation.

    Returns:
        Trading signal: "BUY", "SELL", or "HOLD".

    Example:
        >>> prices = [0.50, 0.52, 0.48, 0.51, 0.35]  # Big drop
        >>> signal = mean_reversion_signal(prices, lookback=4, z_threshold=1.5)
        >>> print(signal)  # "BUY" - price below mean
    """
    result = analyze_mean_reversion(prices, lookback, z_threshold)
    return result.signal


def analyze_mean_reversion(
    prices: list[float] | np.ndarray,
    lookback: int = 24,
    z_threshold: float = 2.0,
) -> MeanReversionResult:
    """Perform detailed mean reversion analysis.

    Args:
        prices: Historical prices (most recent last).
        lookback: Number of periods for mean/std calculation.
        z_threshold: Z-score threshold for signal generation.

    Returns:
        MeanReversionResult with detailed analysis.

    Raises:
        ValueError: If insufficient data for lookback period.

    Example:
        >>> prices = [0.50, 0.52, 0.48, 0.51, 0.49, 0.35]
        >>> result = analyze_mean_reversion(prices, lookback=5)
        >>> print(f"Z-score: {result.z_score:.2f}")
        >>> print(f"Signal: {result.signal}")
    """
    prices = np.array(prices)

    if len(prices) < lookback:
        raise ValueError(
            f"Insufficient data: need {lookback} prices, got {len(prices)}"
        )

    # Use lookback period for statistics
    lookback_prices = prices[-lookback:]
    mean_price = np.mean(lookback_prices)
    std_dev = np.std(lookback_prices, ddof=1)  # Sample std dev

    current_price = prices[-1]

    # Handle zero or near-zero std dev
    if std_dev < 1e-10:
        z_score = 0.0
    else:
        z_score = (current_price - mean_price) / std_dev

    deviation_pct = (current_price - mean_price) / mean_price * 100

    # Generate signal
    if z_score < -z_threshold:
        signal: Literal["BUY", "SELL", "HOLD"] = "BUY"
    elif z_score > z_threshold:
        signal = "SELL"
    else:
        signal = "HOLD"

    return MeanReversionResult(
        signal=signal,
        z_score=z_score,
        current_price=current_price,
        mean_price=mean_price,
        std_dev=std_dev,
        deviation_pct=deviation_pct,
    )


def calculate_half_life(prices: list[float] | np.ndarray) -> float | None:
    """Calculate the half-life of mean reversion.

    The half-life indicates how quickly prices revert to the mean.
    Shorter half-life suggests faster mean reversion.

    Uses the Ornstein-Uhlenbeck model:
        dp = θ(μ - p)dt + σdW

    Half-life = ln(2) / θ

    Args:
        prices: Historical price series.

    Returns:
        Half-life in periods, or None if not mean-reverting.

    Example:
        >>> prices = [0.50, 0.52, 0.51, 0.53, 0.52, 0.51, 0.50]
        >>> half_life = calculate_half_life(prices)
        >>> if half_life:
        ...     print(f"Half-life: {half_life:.1f} periods")
    """
    prices = np.array(prices)

    if len(prices) < 10:
        return None

    # Calculate price changes
    price_changes = np.diff(prices)
    lagged_prices = prices[:-1]

    # Regress price changes on lagged prices
    # dp = α + β * p_{t-1}
    # Mean-reverting if β < 0
    try:
        # Simple OLS
        x = lagged_prices - np.mean(lagged_prices)
        y = price_changes

        beta = np.dot(x, y) / np.dot(x, x)

        if beta >= 0:
            return None  # Not mean-reverting

        # Half-life = -ln(2) / ln(1 + β) ≈ -ln(2) / β for small β
        half_life = -np.log(2) / beta

        return max(0, half_life)

    except (ZeroDivisionError, RuntimeWarning):
        return None


def bollinger_bands(
    prices: list[float] | np.ndarray,
    lookback: int = 20,
    num_std: float = 2.0,
) -> dict[str, float]:
    """Calculate Bollinger Bands for mean reversion signals.

    Args:
        prices: Historical prices.
        lookback: Period for moving average.
        num_std: Number of standard deviations for bands.

    Returns:
        Dict with upper, middle, lower bands and current position.

    Example:
        >>> prices = list(range(100))  # Trending up
        >>> bands = bollinger_bands(prices)
        >>> print(f"Upper: {bands['upper']:.2f}")
        >>> print(f"Position: {bands['position']}")
    """
    prices = np.array(prices)

    if len(prices) < lookback:
        raise ValueError(f"Need at least {lookback} prices")

    recent = prices[-lookback:]
    middle = np.mean(recent)
    std = np.std(recent, ddof=1)

    upper = middle + num_std * std
    lower = middle - num_std * std

    current = prices[-1]

    # Position relative to bands (-1 to 1)
    band_width = upper - lower
    if band_width > 0:
        position = 2 * (current - lower) / band_width - 1
    else:
        position = 0.0

    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "current": current,
        "position": position,  # -1 at lower, 0 at middle, 1 at upper
        "width_pct": band_width / middle * 100 if middle > 0 else 0,
    }


def rsi(
    prices: list[float] | np.ndarray,
    period: int = 14,
) -> float:
    """Calculate Relative Strength Index (RSI).

    RSI measures momentum and can indicate overbought/oversold conditions.
    - RSI > 70: Potentially overbought (mean reversion sell signal)
    - RSI < 30: Potentially oversold (mean reversion buy signal)

    Args:
        prices: Historical prices.
        period: RSI calculation period.

    Returns:
        RSI value (0-100).

    Example:
        >>> prices = [100, 102, 101, 103, 105, 104, 106, 108, 110, 112]
        >>> rsi_value = rsi(prices, period=5)
        >>> if rsi_value > 70:
        ...     print("Potentially overbought")
    """
    prices = np.array(prices)

    if len(prices) < period + 1:
        raise ValueError(f"Need at least {period + 1} prices")

    # Calculate price changes
    deltas = np.diff(prices)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate average gain/loss
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi_value = 100 - (100 / (1 + rs))

    return rsi_value
