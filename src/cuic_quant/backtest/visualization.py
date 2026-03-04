"""Backtest visualisation helpers.

All functions return a ``matplotlib.figure.Figure`` so the caller can
either display inline in Jupyter (``plt.show()``) or save to disk.

Available plots:
  - equity_curve          — cumulative bankroll over time / trades
  - drawdown_plot         — drawdown from peak equity (filled area)
  - rolling_sharpe        — rolling Sharpe ratio by fold or date window
  - bet_distribution      — histogram of bet sizes and odds
  - edge_scatter          — scatter of edge vs P&L per trade
  - metrics_bar_chart     — side-by-side metrics for multiple strategies
  - fold_performance      — per-fold P&L bar chart for walk-forward analysis
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd


def _get_fig_ax(figsize: tuple[float, float] | None = None) -> tuple[Any, Any]:
    """Create a matplotlib figure and axes, importing lazily."""
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = plt.subplots(figsize=figsize or (12, 5))
    return fig, ax


# ---------------------------------------------------------------------------
# Equity curve
# ---------------------------------------------------------------------------

def equity_curve(
    trades: pd.DataFrame,
    initial_bankroll: float = 10_000.0,
    title: str = "Equity Curve",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Plot the equity curve (bankroll over time).

    Args:
        trades: Backtest trades DataFrame (must have ``bankroll`` or
            ``cumulative_pnl`` column).
        initial_bankroll: Starting bankroll for cumulative P&L baseline.
        title: Plot title.
        figsize: Matplotlib figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = _get_fig_ax(figsize)

    if "bankroll" in trades.columns:
        equity = pd.to_numeric(trades["bankroll"], errors="coerce")
        x_label = "Trade #"
    elif "cumulative_pnl" in trades.columns:
        equity = initial_bankroll + pd.to_numeric(trades["cumulative_pnl"], errors="coerce")
        x_label = "Trade #"
    else:
        ax.text(0.5, 0.5, "No equity data available", ha="center", va="center")
        return fig

    x = range(len(equity))

    # Add initial point
    equity_full = pd.concat([pd.Series([initial_bankroll]), equity.reset_index(drop=True)])

    ax.plot(equity_full.values, color="steelblue", linewidth=1.5, label="Bankroll")
    ax.axhline(initial_bankroll, color="grey", linestyle="--", alpha=0.6, label="Starting bankroll")

    final = float(equity.iloc[-1]) if not equity.empty else initial_bankroll
    pct = (final - initial_bankroll) / initial_bankroll * 100
    ax.set_title(f"{title}  |  Final: £{final:,.0f}  ({pct:+.1f}%)")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Bankroll (£)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Drawdown plot
# ---------------------------------------------------------------------------

def drawdown_plot(
    trades: pd.DataFrame,
    initial_bankroll: float = 10_000.0,
    title: str = "Drawdown",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Plot the drawdown from peak equity as a filled area.

    Args:
        trades: Backtest trades DataFrame.
        initial_bankroll: Starting bankroll.
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = _get_fig_ax(figsize)

    if "bankroll" in trades.columns:
        equity = pd.to_numeric(trades["bankroll"], errors="coerce")
    elif "cumulative_pnl" in trades.columns:
        equity = initial_bankroll + pd.to_numeric(trades["cumulative_pnl"], errors="coerce")
    else:
        ax.text(0.5, 0.5, "No equity data available", ha="center", va="center")
        return fig

    equity_full = pd.concat([pd.Series([initial_bankroll]), equity.reset_index(drop=True)])
    peak = equity_full.cummax()
    drawdown = ((equity_full - peak) / peak.clip(lower=1e-8)) * 100

    max_dd = float(drawdown.min())

    ax.fill_between(range(len(drawdown)), drawdown.values, 0, color="crimson", alpha=0.4)
    ax.plot(drawdown.values, color="crimson", linewidth=1.0)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_title(f"{title}  |  Max Drawdown: {max_dd:.2f}%")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Drawdown (%)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Rolling Sharpe ratio
# ---------------------------------------------------------------------------

def rolling_sharpe(
    trades: pd.DataFrame,
    window: int = 50,
    periods_per_year: int = 252,
    title: str = "Rolling Sharpe Ratio",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Plot the rolling Sharpe ratio over trades.

    Args:
        trades: Backtest trades DataFrame (``pnl`` column required).
        window: Rolling window size in trades.
        periods_per_year: Annualisation factor.
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = _get_fig_ax(figsize)

    if "pnl" not in trades.columns:
        ax.text(0.5, 0.5, "No P&L data", ha="center", va="center")
        return fig

    pnl = pd.to_numeric(trades["pnl"], errors="coerce")
    roll_mean = pnl.rolling(window).mean()
    roll_std = pnl.rolling(window).std(ddof=1).replace(0, np.nan)
    roll_sharpe = (roll_mean / roll_std) * np.sqrt(periods_per_year)

    ax.plot(roll_sharpe.values, color="darkorange", linewidth=1.5)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.axhline(1, color="green", linewidth=0.6, linestyle=":", alpha=0.7, label="Sharpe=1")
    ax.set_title(f"{title}  (window={window})")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Annualised Sharpe")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Bet distribution
# ---------------------------------------------------------------------------

def bet_distribution(
    trades: pd.DataFrame,
    title: str = "Bet Distribution",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Plot histograms of stake sizes and bet odds.

    Args:
        trades: Backtest trades DataFrame.
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, axes = plt.subplots(1, 2, figsize=figsize or (12, 4))
    fig.suptitle(title)

    if "stake" in trades.columns:
        stakes = pd.to_numeric(trades["stake"], errors="coerce").dropna()
        axes[0].hist(stakes.values, bins=30, color="steelblue", alpha=0.7, edgecolor="white")
        axes[0].set_title("Stake Distribution")
        axes[0].set_xlabel("Stake (£)")
        axes[0].set_ylabel("Count")
    else:
        axes[0].text(0.5, 0.5, "No stake data", ha="center", va="center")

    if "odds" in trades.columns:
        odds = pd.to_numeric(trades["odds"], errors="coerce").dropna()
        axes[1].hist(odds.values, bins=30, color="darkorange", alpha=0.7, edgecolor="white")
        axes[1].set_title("Odds Distribution")
        axes[1].set_xlabel("Decimal Odds")
        axes[1].set_ylabel("Count")
    else:
        axes[1].text(0.5, 0.5, "No odds data", ha="center", va="center")

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Edge vs P&L scatter
# ---------------------------------------------------------------------------

def edge_scatter(
    trades: pd.DataFrame,
    title: str = "Edge vs P&L",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Scatter plot of model edge vs trade P&L.

    A profitable strategy should show a positive correlation: higher
    edge games should generate higher P&L on average.

    Args:
        trades: Backtest trades DataFrame.
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = _get_fig_ax(figsize)

    if not {"edge", "pnl", "outcome"}.issubset(trades.columns):
        ax.text(0.5, 0.5, "Required columns missing (edge, pnl, outcome)", ha="center", va="center")
        return fig

    edge = pd.to_numeric(trades["edge"], errors="coerce")
    pnl = pd.to_numeric(trades["pnl"], errors="coerce")
    outcomes = trades["outcome"].astype(str).str.upper()

    win_mask = outcomes == "WIN"
    loss_mask = outcomes == "LOSS"

    ax.scatter(edge[win_mask], pnl[win_mask], color="seagreen", alpha=0.5, s=15, label="WIN")
    ax.scatter(edge[loss_mask], pnl[loss_mask], color="crimson", alpha=0.5, s=15, label="LOSS")
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="grey", linewidth=0.8, linestyle="--")

    # Trend line
    valid = edge.notna() & pnl.notna()
    if valid.sum() > 2:
        import numpy as np

        coef = np.polyfit(edge[valid], pnl[valid], 1)
        x_line = np.linspace(float(edge[valid].min()), float(edge[valid].max()), 100)
        ax.plot(x_line, np.polyval(coef, x_line), "k--", linewidth=1.0, alpha=0.6, label="Trend")

    ax.set_title(title)
    ax.set_xlabel("Model Edge (model_P − implied_P)")
    ax.set_ylabel("Trade P&L (£)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Metrics bar chart
# ---------------------------------------------------------------------------

def metrics_bar_chart(
    comparison_df: pd.DataFrame,
    metrics: list[str] | None = None,
    title: str = "Strategy Comparison",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Side-by-side bar chart comparing strategies across key metrics.

    Args:
        comparison_df: Output of ``compare_strategies()``.
        metrics: Metrics to plot. Defaults to a sensible subset.
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    if metrics is None:
        metrics = ["sharpe_ratio", "win_rate", "roi", "profit_factor"]

    metrics = [m for m in metrics if m in comparison_df.columns]
    if not metrics:
        fig, ax = _get_fig_ax(figsize)
        ax.text(0.5, 0.5, "No comparable metrics found", ha="center", va="center")
        return fig

    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=figsize or (4 * n_metrics, 5))
    if n_metrics == 1:
        axes = [axes]

    fig.suptitle(title, fontsize=13)
    colors = ["steelblue", "darkorange", "seagreen", "crimson", "purple"]

    for ax, metric in zip(axes, metrics):
        vals = pd.to_numeric(comparison_df[metric], errors="coerce").fillna(0)
        bar_colors = [colors[i % len(colors)] for i in range(len(vals))]
        ax.bar(comparison_df.index, vals.values, color=bar_colors, alpha=0.8, edgecolor="white")
        ax.set_title(metric.replace("_", " ").title(), fontsize=10)
        ax.set_xticklabels(comparison_df.index, rotation=20, ha="right", fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")
        ax.axhline(0, color="grey", linewidth=0.6)

    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Fold performance
# ---------------------------------------------------------------------------

def fold_performance(
    trades: pd.DataFrame,
    title: str = "Walk-Forward Fold Performance",
    figsize: tuple[float, float] | None = None,
) -> Any:
    """Bar chart of total P&L per walk-forward fold.

    Args:
        trades: Concatenated walk-forward trades DataFrame (must have
            ``fold`` and ``pnl`` columns).
        title: Plot title.
        figsize: Figure size.

    Returns:
        matplotlib Figure.
    """
    import matplotlib.pyplot as plt  # type: ignore[import]

    fig, ax = _get_fig_ax(figsize)

    if not {"fold", "pnl"}.issubset(trades.columns):
        ax.text(0.5, 0.5, "fold/pnl columns missing", ha="center", va="center")
        return fig

    fold_pnl = (
        trades.groupby("fold")["pnl"]
        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
        .reset_index()
    )
    fold_pnl.columns = ["fold", "total_pnl"]

    colors = ["seagreen" if v >= 0 else "crimson" for v in fold_pnl["total_pnl"]]
    ax.bar(fold_pnl["fold"].astype(str), fold_pnl["total_pnl"], color=colors, alpha=0.8, edgecolor="white")
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_title(title)
    ax.set_xlabel("Fold")
    ax.set_ylabel("Total P&L (£)")
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    return fig
