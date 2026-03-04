"""Performance display and plotting helpers for backtest results."""

from __future__ import annotations

import pandas as pd


def display_extended_metrics(
    results_df: pd.DataFrame,
    initial_bankroll: float = 10000.0,
) -> None:
    """Display 12 extended performance metrics for backtest results.

    Prints a formatted table of risk/reward statistics including Sharpe
    ratio, Sortino ratio, max drawdown, profit factor, streaks, and more.

    Args:
        results_df: DataFrame output from backtest().
        initial_bankroll: Starting bankroll used in the backtest.
    """
    if len(results_df) == 0:
        print("No trades to analyze.")
        return

    try:
        from cuic_quant.metrics import calculate_all_metrics
        metrics = calculate_all_metrics(results_df)
    except ImportError:
        # Fallback: compute basic metrics locally
        pnl_series = pd.to_numeric(results_df["pnl"], errors="coerce").dropna()
        outcomes = results_df["outcome"]
        wins = int((outcomes == "WIN").sum())
        total = len(outcomes)
        metrics = {
            "total_trades": total,
            "win_rate": wins / total if total > 0 else 0.0,
            "total_pnl": float(pnl_series.sum()) if not pnl_series.empty else 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
        }

    pnl = results_df["pnl"]
    wins_pnl = pnl[results_df["outcome"] == "WIN"]
    losses_pnl = pnl[results_df["outcome"] == "LOSS"]

    avg_win = float(wins_pnl.mean()) if len(wins_pnl) > 0 else 0.0
    avg_loss = float(losses_pnl.mean()) if len(losses_pnl) > 0 else 0.0
    wl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # M3 fix: Use Sortino from calculate_all_metrics (avoids reimplementation)
    sortino = metrics.get("sortino_ratio", 0.0)

    ev_per_bet = float(pnl.mean())

    # Streak calculation
    is_win = (results_df["outcome"] == "WIN").astype(int)
    groups = is_win.groupby((is_win != is_win.shift()).cumsum())
    longest_win = int(groups.sum().max())
    longest_loss = int((groups.count() - groups.sum()).max())

    best = float(pnl.max())
    worst = float(pnl.min())

    print("=" * 45)
    print("       EXTENDED PERFORMANCE METRICS")
    print("=" * 45)
    print(f"  Sharpe Ratio:         {metrics['sharpe_ratio']:>10.3f}")
    print(f"  Sortino Ratio:        {sortino:>10.3f}")
    print(f"  Max Drawdown:         {metrics['max_drawdown']:>9.1%}")
    print(f"  Profit Factor:        {metrics['profit_factor']:>10.3f}")
    print(f"  Average Win:          ${avg_win:>9.2f}")
    print(f"  Average Loss:         ${avg_loss:>9.2f}")
    print(f"  Win/Loss Ratio:       {wl_ratio:>10.3f}")
    print(f"  Expected Value/Bet:   ${ev_per_bet:>9.2f}")
    print(f"  Longest Win Streak:   {longest_win:>10d}")
    print(f"  Longest Loss Streak:  {longest_loss:>10d}")
    print(f"  Best Trade:           ${best:>9.2f}")
    print(f"  Worst Trade:          ${worst:>9.2f}")
    print("=" * 45)


def plot_performance(
    results_df: pd.DataFrame,
    title: str = "Backtest Performance",
    initial_bankroll: float = 10000.0,
) -> None:
    """Plot a 2x2 performance dashboard for backtest results.

    Panels: cumulative P&L, drawdown, P&L distribution, trade outcomes.

    Args:
        results_df: DataFrame output from backtest().
        title: Plot super-title.
        initial_bankroll: Starting bankroll used in the backtest.
    """
    import matplotlib.pyplot as plt

    if len(results_df) == 0:
        print("No trades to plot.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    pnl = results_df["pnl"]
    cum_pnl = results_df["cumulative_pnl"]
    trade_num = range(1, len(results_df) + 1)

    # 1. Cumulative PnL
    ax = axes[0, 0]
    ax.plot(trade_num, cum_pnl, color="#2196F3", linewidth=1.5)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    ax.fill_between(trade_num, cum_pnl, alpha=0.15, color="#2196F3")
    ax.set_title("Cumulative P&L")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("P&L ($)")
    ax.grid(True, alpha=0.3)

    # 2. Drawdown
    ax = axes[0, 1]
    equity = cum_pnl + initial_bankroll
    # Prepend initial_bankroll so cummax sees the starting equity,
    # matching calculate_max_drawdown logic for early-loss drawdowns.
    running_peak = pd.concat([pd.Series([initial_bankroll]), equity]).cummax().iloc[1:].reset_index(drop=True)
    drawdown_pct = (running_peak - equity) / running_peak * 100
    ax.fill_between(trade_num, drawdown_pct, color="#F44336", alpha=0.4)
    ax.plot(trade_num, drawdown_pct, color="#F44336", linewidth=1.0)
    ax.set_title("Drawdown")
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Drawdown (%)")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)

    # 3. PnL Distribution
    ax = axes[1, 0]
    ax.hist(pnl, bins=min(30, len(pnl)), color="#9C27B0", alpha=0.7, edgecolor="white")
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.8)
    mean_pnl = float(pnl.mean())
    ax.axvline(x=mean_pnl, color="#FF9800", linewidth=1.5, label=f"Mean: ${mean_pnl:.2f}")
    ax.set_title("P&L Distribution")
    ax.set_xlabel("P&L ($)")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Trade Outcomes
    ax = axes[1, 1]
    wins = int((results_df["outcome"] == "WIN").sum())
    losses = int((results_df["outcome"] == "LOSS").sum())
    bars = ax.bar(
        ["Wins", "Losses"], [wins, losses],
        color=["#4CAF50", "#F44336"], alpha=0.8, edgecolor="white",
    )
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, h, str(int(h)),
                ha="center", va="bottom", fontweight="bold")
    ax.set_title("Trade Outcomes")
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.show()


__all__ = [
    "display_extended_metrics",
    "plot_performance",
]
