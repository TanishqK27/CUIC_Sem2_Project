"""Backtester backend module — backwards-compatible re-export facade.

U5: This file was split into focused submodules:
    - engine.py: Core backtest loop, constants, example strategies
    - data_loader.py: Data loading from Railway PostgreSQL / local CSV
    - validator.py: Result validation (12 checks)
    - visualization.py: display_extended_metrics(), plot_performance()

All public names are re-exported here so that existing imports like
    from cuic_quant.backtest.backtester_backend import backtest
continue to work without changes.
"""

from __future__ import annotations

# Re-export everything from the split modules
from cuic_quant.backtest.data_loader import (  # noqa: F401
    DATA_DIR,
    DUMMY_CSV,
    PROJECT_ROOT,
    TEST_CSV,
    load_backtest_data,
)
from cuic_quant.backtest.engine import (  # noqa: F401
    OUTPUT_COLUMNS,
    VALID_ACTIONS,
    VALID_OUTCOMES,
    always_bet_away,
    always_bet_home,
    backtest,
    kelly_bet_home_demo,
)
from cuic_quant.backtest.validator import (  # noqa: F401
    validate_backtest_results,
)
from cuic_quant.backtest.visualization import (  # noqa: F401
    display_extended_metrics,
    plot_performance,
)

__all__ = [
    # Constants
    "OUTPUT_COLUMNS",
    "VALID_ACTIONS",
    "VALID_OUTCOMES",
    "PROJECT_ROOT",
    "DATA_DIR",
    "DUMMY_CSV",
    "TEST_CSV",
    # Data
    "load_backtest_data",
    # Engine
    "backtest",
    # Strategies
    "always_bet_home",
    "always_bet_away",
    "kelly_bet_home_demo",
    # Validation
    "validate_backtest_results",
    # Visualization
    "display_extended_metrics",
    "plot_performance",
]
