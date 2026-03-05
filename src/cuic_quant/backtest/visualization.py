"""Performance display and plotting helpers for backtest results."""

from __future__ import annotations

import math

import pandas as pd


def display_extended_metrics(
    results_df: pd.DataFrame,
    initial_bankroll: float = 10000.0,
) -> None:
    """Display full performance report for backtest results.

    Prints risk/reward metrics, probability calibration, closing line value,
    statistical significance, and bootstrap confidence intervals.

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

    from cuic_quant.backtest.statistics import (
        bootstrap_confidence_interval,
        significance_report,
    )

    pnl = results_df["pnl"]
    wins_pnl = pnl[results_df["outcome"] == "WIN"]
    losses_pnl = pnl[results_df["outcome"] == "LOSS"]

    avg_win = float(wins_pnl.mean()) if len(wins_pnl) > 0 else 0.0
    avg_loss = float(losses_pnl.mean()) if len(losses_pnl) > 0 else 0.0
    wl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")
    ev_per_bet = float(pnl.mean())

    # Streak calculation
    is_win = (results_df["outcome"] == "WIN").astype(int)
    groups = is_win.groupby((is_win != is_win.shift()).cumsum())
    longest_win = int(groups.sum().max())
    longest_loss = int((groups.count() - groups.sum()).max())

    best = float(pnl.max())
    worst = float(pnl.min())

    # Statistical significance
    sig = significance_report(results_df)
    p_value = sig["p_value"]
    is_significant = sig["is_significant"]
    sample_assessment = sig["sample_size_assessment"]
    ci = sig["confidence_intervals"]["mean_pnl_95ci"]
    roi_ci = sig["confidence_intervals"]["roi_95ci"]

    # Bootstrap CI on total PnL
    lo_pnl, _, hi_pnl = bootstrap_confidence_interval(pnl, n_bootstrap=5000)
    total_pnl = float(pnl.sum())

    # CLV
    clv_raw = metrics.get("clv")
    clv: float | None = float(clv_raw) if clv_raw is not None else None
    has_clv = clv is not None and not math.isnan(clv)

    # Brier Score / Log Loss
    brier = metrics.get("brier_score")
    logloss = metrics.get("log_loss")
    has_calibration = (
        brier is not None
        and not (isinstance(brier, float) and math.isnan(brier))
        and brier != 0.25  # 0.25 = no confidence data (always 0.5)
    )

    W = 52  # total width

    def section(title: str) -> None:
        print("=" * W)
        pad = (W - len(title) - 2) // 2
        print(" " * pad + title)

    def row(label: str, value: str) -> None:
        print(f"  {label:<28}{value:>20}")

    def divider() -> None:
        print("-" * W)

    # ── SECTION 1: Overview ──────────────────────────────────────────────
    section("BACKTEST FULL REPORT")
    print("=" * W)
    row("Total Trades:", f"{metrics['total_trades']:,}")
    row("Win Rate:", f"{metrics['win_rate']:.1%}")
    row("Total PnL:", f"${total_pnl:,.2f}")
    row("Total Wagered:", f"${metrics.get('total_wagered', 0):,.2f}")
    row("ROI (Return on Capital):", f"{metrics.get('return_on_capital', 0):.2%}")
    row("Yield per Bet:", f"{metrics.get('yield_per_bet', 0):.2%}")
    row("Average Odds:", f"{metrics.get('avg_odds', 0):.4f}")

    # ── SECTION 2: Risk / Reward ─────────────────────────────────────────
    divider()
    print("  RISK / REWARD")
    divider()
    row("Sharpe Ratio:", f"{metrics['sharpe_ratio']:.3f}")
    row("Sortino Ratio:", f"{metrics.get('sortino_ratio', 0):.3f}")
    row("Calmar Ratio:", f"{metrics.get('calmar_ratio', 0):.3f}")
    row("Max Drawdown:", f"{-metrics['max_drawdown']:.1%}")
    row("Profit Factor:", f"{metrics['profit_factor']:.3f}")
    row("Kelly Growth Rate:", f"{metrics.get('kelly_growth_rate', 0):.6f}")

    # ── SECTION 3: Trade Stats ───────────────────────────────────────────
    divider()
    print("  TRADE STATISTICS")
    divider()
    row("Average Win:", f"${avg_win:.2f}")
    row("Average Loss:", f"${avg_loss:.2f}")
    row("Win / Loss Ratio:", f"{wl_ratio:.3f}")
    row("Expected Value / Bet:", f"${ev_per_bet:.2f}")
    row("Best Trade:", f"${best:.2f}")
    row("Worst Trade:", f"${worst:.2f}")
    row("Longest Win Streak:", f"{longest_win}")
    row("Longest Loss Streak:", f"{longest_loss}")

    # ── SECTION 4: Probability Calibration ──────────────────────────────
    divider()
    print("  PROBABILITY CALIBRATION")
    divider()
    if has_calibration:
        row("Brier Score:", f"{brier:.4f}  (0=perfect, 0.25=no skill)")
        row("Log Loss:", f"{logloss:.4f}  (lower=better)")
    else:
        row("Brier Score:", "N/A (no confidence values)")
        row("Log Loss:", "N/A (no confidence values)")

    # ── SECTION 5: Closing Line Value ────────────────────────────────────
    divider()
    print("  CLOSING LINE VALUE (CLV)")
    divider()
    if has_clv:
        assert clv is not None
        clv_sign = "+" if clv >= 0 else ""
        clv_label = (
            "POSITIVE edge (beat the market)"
            if clv >= 0
            else "NEGATIVE edge (market beat you)"
        )
        row("Average CLV:", f"{clv_sign}{clv:.4f}")
        row("Assessment:", clv_label)
    else:
        row("CLV:", "N/A (no closing odds in dataset)")

    # ── SECTION 6: Statistical Significance ─────────────────────────────
    divider()
    print("  STATISTICAL SIGNIFICANCE")
    divider()
    sig_label = "SIGNIFICANT [YES]" if is_significant else "NOT significant [NO]"
    row("p-value:", f"{p_value:.4f}  ({sig_label})")
    row("Sample Size:", sample_assessment)
    row("EV 95% CI (per bet):", f"${ci[0]:.2f}  to  ${ci[2]:.2f}")
    row("ROI 95% CI:", f"{roi_ci[0]:.2%}  to  {roi_ci[2]:.2%}")

    # ── SECTION 7: Bootstrap CI ──────────────────────────────────────────
    divider()
    print("  BOOTSTRAP CONFIDENCE INTERVAL  (5,000 resamples)")
    divider()
    row(
        "Total PnL 95% CI:",
        f"${lo_pnl * metrics['total_trades']:,.2f}  to  ${hi_pnl * metrics['total_trades']:,.2f}",
    )
    row("EV per bet 95% CI:", f"${lo_pnl:.2f}  to  ${hi_pnl:.2f}")

    print("=" * W)


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
    running_peak = (
        pd.concat([pd.Series([initial_bankroll]), equity])
        .cummax()
        .iloc[1:]
        .reset_index(drop=True)
    )
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
    ax.axvline(
        x=mean_pnl, color="#FF9800", linewidth=1.5, label=f"Mean: ${mean_pnl:.2f}"
    )
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
        ["Wins", "Losses"],
        [wins, losses],
        color=["#4CAF50", "#F44336"],
        alpha=0.8,
        edgecolor="white",
    )
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h,
            str(int(h)),
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    ax.set_title("Trade Outcomes")
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.show()


__all__ = [
    "display_extended_metrics",
    "plot_performance",
]
