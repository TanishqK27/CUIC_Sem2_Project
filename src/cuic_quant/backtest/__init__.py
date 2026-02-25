"""Backtesting framework for strategy validation.

This module provides tools for:
- Loading historical game data from database or CSV
- Running strategies against historical data
- Validating backtest results for correctness and data leakage

Usage:
    from cuic_quant.backtest import backtest, load_backtest_data, validate_backtest_results

    data = load_backtest_data("2026-01-01", "2026-01-31")
    results = backtest(data, my_strategy)
    report = validate_backtest_results(results, data)
"""

from cuic_quant.backtest.backtester_backend import (
    always_bet_away,
    always_bet_home,
    backtest,
    display_extended_metrics,
    kelly_bet_home_demo,
    load_backtest_data,
    plot_performance,
    validate_backtest_results,
)

__all__ = [
    "always_bet_away",
    "always_bet_home",
    "backtest",
    "display_extended_metrics",
    "kelly_bet_home_demo",
    "load_backtest_data",
    "plot_performance",
    "validate_backtest_results",
]
