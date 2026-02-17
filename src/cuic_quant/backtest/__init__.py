"""Public API for the backtest package.

Notebook and tests import from ``cuic_quant.backtest`` directly, so this file
re-exports the backend implementation from ``backtester_backend.py``.
"""

from cuic_quant.backtest.backtester_backend import (
    DATA_DIR,
    DUMMY_CSV,
    OUTPUT_COLUMNS,
    TEST_CSV,
    always_bet_home,
    backtest,
    load_backtest_data,
    validate_backtest_results,
)

__all__ = [
    "DATA_DIR",
    "DUMMY_CSV",
    "OUTPUT_COLUMNS",
    "TEST_CSV",
    "always_bet_home",
    "backtest",
    "load_backtest_data",
    "validate_backtest_results",
]
