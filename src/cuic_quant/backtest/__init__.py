"""Backtesting framework for strategy validation.

This module provides tools for:
- Loading historical game data from database or CSV
- Running strategies against historical data
- Validating backtest results for correctness and data leakage
- Walk-forward analysis and out-of-sample testing
- Strategy comparison and anomaly detection
- Statistical significance testing
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

# New modules - import conditionally to avoid breaking existing code
# if modules haven't been created yet
try:
    from cuic_quant.backtest.comparison import compare_strategies, detect_suspicious_results
except ImportError:
    pass

try:
    from cuic_quant.backtest.walk_forward import (
        train_test_split,
        walk_forward_backtest,
        expanding_window_backtest,
    )
except ImportError:
    pass

try:
    from cuic_quant.backtest.statistics import (
        significance_report,
        overfitting_report,
    )
except ImportError:
    pass

__all__ = [
    # Core
    "always_bet_away",
    "always_bet_home",
    "backtest",
    "display_extended_metrics",
    "kelly_bet_home_demo",
    "load_backtest_data",
    "plot_performance",
    "validate_backtest_results",
    # Comparison
    "compare_strategies",
    "detect_suspicious_results",
    # Walk-forward
    "train_test_split",
    "walk_forward_backtest",
    "expanding_window_backtest",
    # Statistics
    "significance_report",
    "overfitting_report",
]
