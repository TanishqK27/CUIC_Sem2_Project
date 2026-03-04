"""TrainableStrategy protocol for walk-forward retraining.

Strategies that implement ``fit()`` and ``predict()`` are automatically
detected by walk-forward functions, which call ``fit(train_data)`` before
each fold's backtest.  Plain functions continue to work unchanged.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class TrainableStrategy(Protocol):
    """Protocol for strategies that retrain between walk-forward folds.

    Implement ``fit()`` to learn from training data, and ``predict()`` to
    generate signals row-by-row during backtesting.

    Example::

        class OddsThresholdModel:
            def __init__(self):
                self.threshold = 2.0

            def fit(self, train_data: pd.DataFrame) -> None:
                self.threshold = train_data["home_odds"].mean()

            def predict(
                self, row: pd.Series, context: dict[str, Any] | None = None,
            ) -> dict[str, Any]:
                if row["home_odds"] < self.threshold:
                    return {"action": "BUY_HOME", "size": 100, "confidence": 0.6}
                return {"action": "SKIP"}
    """

    def fit(self, train_data: pd.DataFrame) -> None:
        """Train the strategy on historical data.

        Args:
            train_data: DataFrame with all columns including ``home_win``.
                This is training data --- accessing outcomes is correct here.
        """
        ...

    def predict(
        self,
        row: pd.Series,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a signal for a single game row.

        Same signature as a plain strategy function.  The ``row`` will NOT
        contain ``home_win`` (the backtest engine strips it).

        Args:
            row: Single game row (without outcome).
            context: Backtest context dict (bankroll, history, etc.).

        Returns:
            Signal dict with ``action``, ``size``, ``confidence``, ``reason``.
        """
        ...
