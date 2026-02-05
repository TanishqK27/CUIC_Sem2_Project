# Task: Visualization Functions

**Owner:** Ben
**Deadline:** Feb 19 (Week 2)
**Priority:** Medium — needed for presentations

---

## What You're Building

Functions that create charts from backtest results: equity curve, drawdown chart, and trade distribution histogram.

---

## Why This Matters

Charts tell the story. A table of numbers doesn't sell a strategy — a beautiful equity curve going up does. These visualizations will be used in every presentation.

---

## Exactly What You Must Deliver

### 1. Visualization Module

Create `src/cuic_quant/metrics/visualizations.py`:

```python
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

def plot_equity_curve(
    cumulative_pnl: pd.Series,
    title: str = "Equity Curve",
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot cumulative P&L over time.

    Args:
        cumulative_pnl: Series of cumulative P&L (index = dates)
        title: Chart title
        figsize: Figure size (width, height)
        save_path: If provided, save chart to this path

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot the equity curve
    ax.plot(cumulative_pnl.index, cumulative_pnl.values, linewidth=2)

    # Add horizontal line at starting value
    ax.axhline(y=cumulative_pnl.iloc[0], color='gray', linestyle='--', alpha=0.5)

    # Labels
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative P&L ($)')
    ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig

def plot_drawdown(
    cumulative_pnl: pd.Series,
    title: str = "Drawdown",
    figsize: tuple = (12, 4),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot drawdown over time (as negative percentages).

    Shows how far the strategy fell from its peak at each point.
    """
    # Calculate drawdown
    peak = cumulative_pnl.cummax()
    drawdown = (cumulative_pnl - peak) / peak * 100  # as percentage

    fig, ax = plt.subplots(figsize=figsize)
    ax.fill_between(drawdown.index, drawdown.values, 0, alpha=0.5, color='red')
    ax.plot(drawdown.index, drawdown.values, color='darkred', linewidth=1)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Drawdown (%)')
    ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig

def plot_trade_distribution(
    pnl: pd.Series,
    title: str = "Trade P&L Distribution",
    bins: int = 30,
    figsize: tuple = (10, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot histogram of individual trade P&Ls.

    Args:
        pnl: Series of individual trade P&Ls
        title: Chart title
        bins: Number of histogram bins
        figsize: Figure size
        save_path: Optional path to save chart

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Color wins green, losses red
    colors = ['green' if x > 0 else 'red' for x in pnl]
    ax.hist(pnl, bins=bins, edgecolor='black', alpha=0.7)

    # Add vertical line at zero
    ax.axvline(x=0, color='black', linestyle='--', linewidth=2)

    # Add mean line
    ax.axvline(x=pnl.mean(), color='blue', linestyle='-', linewidth=2, label=f'Mean: ${pnl.mean():.2f}')

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Trade P&L ($)')
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig

def create_backtest_report(
    trades_df: pd.DataFrame,
    metrics: dict,
    save_dir: Optional[str] = None
) -> plt.Figure:
    """
    Create a full backtest report with all charts.

    Args:
        trades_df: DataFrame with columns: date, pnl, cumulative_pnl, outcome
        metrics: Dict from calculate_all_metrics()
        save_dir: Directory to save charts (optional)

    Returns:
        Figure with subplots
    """
    fig = plt.figure(figsize=(14, 10))

    # Equity curve (top)
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(trades_df['date'], trades_df['cumulative_pnl'])
    ax1.set_title('Equity Curve')
    ax1.set_ylabel('Cumulative P&L ($)')

    # Drawdown (top right)
    ax2 = fig.add_subplot(2, 2, 2)
    peak = trades_df['cumulative_pnl'].cummax()
    dd = (trades_df['cumulative_pnl'] - peak) / peak * 100
    ax2.fill_between(trades_df['date'], dd, 0, color='red', alpha=0.5)
    ax2.set_title('Drawdown')
    ax2.set_ylabel('Drawdown (%)')

    # Trade distribution (bottom left)
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.hist(trades_df['pnl'], bins=20, edgecolor='black')
    ax3.axvline(x=0, color='red', linestyle='--')
    ax3.set_title('Trade Distribution')
    ax3.set_xlabel('P&L ($)')

    # Metrics text (bottom right)
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    metrics_text = f"""
    Performance Metrics
    -------------------
    Total Trades: {metrics['total_trades']}
    Win Rate: {metrics['win_rate']:.1%}
    Total P&L: ${metrics['total_pnl']:,.2f}
    Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
    Max Drawdown: {metrics['max_drawdown']:.1%}
    Profit Factor: {metrics['profit_factor']:.2f}
    """
    ax4.text(0.1, 0.5, metrics_text, fontsize=12, family='monospace',
             verticalalignment='center')

    plt.tight_layout()

    if save_dir:
        fig.savefig(f"{save_dir}/backtest_report.png", dpi=150, bbox_inches='tight')

    return fig
```

### 2. Update Module Init

Add to `src/cuic_quant/metrics/__init__.py`:

```python
from cuic_quant.metrics.visualizations import (
    plot_equity_curve,
    plot_drawdown,
    plot_trade_distribution,
    create_backtest_report,
)
```

---

## Done Checklist

- [ ] Module created at `src/cuic_quant/metrics/visualizations.py`
- [ ] All 4 functions implemented
- [ ] Charts look professional (labels, titles, colors)
- [ ] Save functionality works
- [ ] `create_backtest_report` combines everything
- [ ] Tested with sample data, charts render correctly

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Generate fake trades data
2. Call `create_backtest_report()`
3. Show the combined figure with all charts
4. Save to file

**Duration:** 2 minutes max

---

## Resources

- matplotlib gallery: https://matplotlib.org/stable/gallery/index.html
- seaborn for prettier charts (optional): https://seaborn.pydata.org/

---

## Who To Ask If Stuck

1. Google "matplotlib equity curve"
2. James — how the trades DataFrame looks
3. Tan — what charts are most useful
