"""Backtesting framework for strategy validation.

This module provides a complete sports-betting backtesting pipeline:

- Data loading: NBA CSV data into X/Y/O format
- Strategy interface: pluggable sklearn-style betting strategies
- Backtest engine: value-bet selection + Kelly sizing + transaction costs
- Walk-forward analysis: rolling, expanding, CPCV with model refitting
- Validation: 12-check result validator
- Statistics: binomial tests, bootstrap CI, DSR, PBO
- Strategy comparison: side-by-side metrics + anomaly detection
- Visualisation: equity curves, drawdown, rolling Sharpe

Quickstart::

    from cuic_quant.backtest import (
        load_nba_dataset,
        LogisticRegressionStrategy,
        BacktestConfig,
        run_walk_forward,
        ExpandingWindow,
        BacktestValidator,
    )

    dataset = load_nba_dataset()
    strategy = LogisticRegressionStrategy(C=0.1)
    config = BacktestConfig(kelly_fraction=0.5, min_edge=0.02)

    trades = run_walk_forward(strategy, dataset, ExpandingWindow(), config)
    validator = BacktestValidator()
    print(validator.summary(trades))
"""

from cuic_quant.backtest.data_loader import BacktestDataset, load_nba_dataset
from cuic_quant.backtest.engine import (
    BacktestConfig,
    BettingStrategy,
    HomeAdvantageBaseline,
    LogisticRegressionStrategy,
    RandomForestStrategy,
    TransactionCosts,
    ValueBetBaseline,
    run_backtest,
)
from cuic_quant.backtest.validator import BacktestValidator, ValidationResult
from cuic_quant.backtest.walk_forward import (
    AnchoredSplit,
    BaseSplitter,
    CPCV,
    ExpandingWindow,
    RollingWindow,
    SimpleSplit,
    run_walk_forward,
)
from cuic_quant.backtest.statistics import (
    binomial_test,
    bootstrap_ci,
    bonferroni_correction,
    holm_bonferroni_correction,
    deflated_sharpe_ratio,
    probability_of_backtest_overfitting,
    compute_statistics_report,
)
from cuic_quant.backtest.comparison import (
    compare_strategies,
    detect_anomalies,
    rank_strategies,
)
from cuic_quant.backtest.visualization import (
    equity_curve,
    drawdown_plot,
    rolling_sharpe,
    bet_distribution,
    edge_scatter,
    metrics_bar_chart,
    fold_performance,
)

__all__ = [
    # Data
    "BacktestDataset",
    "load_nba_dataset",
    # Engine
    "BettingStrategy",
    "LogisticRegressionStrategy",
    "RandomForestStrategy",
    "HomeAdvantageBaseline",
    "ValueBetBaseline",
    "TransactionCosts",
    "BacktestConfig",
    "run_backtest",
    # Walk-forward
    "BaseSplitter",
    "SimpleSplit",
    "RollingWindow",
    "ExpandingWindow",
    "AnchoredSplit",
    "CPCV",
    "run_walk_forward",
    # Validation
    "BacktestValidator",
    "ValidationResult",
    # Statistics
    "binomial_test",
    "bootstrap_ci",
    "bonferroni_correction",
    "holm_bonferroni_correction",
    "deflated_sharpe_ratio",
    "probability_of_backtest_overfitting",
    "compute_statistics_report",
    # Comparison
    "compare_strategies",
    "detect_anomalies",
    "rank_strategies",
    # Visualisation
    "equity_curve",
    "drawdown_plot",
    "rolling_sharpe",
    "bet_distribution",
    "edge_scatter",
    "metrics_bar_chart",
    "fold_performance",
]
