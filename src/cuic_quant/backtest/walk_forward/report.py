"""Human-readable reporting for walk-forward analysis results."""

from __future__ import annotations

from typing import Any


def walk_forward_report(results: dict[str, Any]) -> str:
    """Generate human-readable report from walk-forward results.

    Accepts the dict returned by any of the walk-forward functions in this
    package (``walk_forward_backtest``, ``expanding_window_backtest``,
    ``anchored_walk_forward``, ``combinatorial_purged_cv``).

    Args:
        results: Dict with ``splits``, ``aggregated_metrics``, and
            optionally ``in_sample_vs_out_of_sample``.

    Returns:
        Multi-line string suitable for ``print()``.
    """
    lines: list[str] = []
    sep = "=" * 60

    lines.append(sep)
    lines.append("           WALK-FORWARD ANALYSIS REPORT")
    lines.append(sep)

    # Aggregated OOS metrics
    agg = results.get("aggregated_metrics", {})
    lines.append("")
    lines.append("  Aggregated Out-of-Sample Metrics")
    lines.append("  " + "-" * 40)
    lines.append(f"  Total Trades:    {agg.get('total_trades', 0):>10}")
    lines.append(f"  Total PnL:       ${agg.get('total_pnl', 0.0):>10.2f}")
    lines.append(f"  Win Rate:        {agg.get('win_rate', 0.0):>10.2%}")
    lines.append(f"  Sharpe Ratio:    {agg.get('sharpe_ratio', 0.0):>10.4f}")
    lines.append(f"  Sortino Ratio:   {agg.get('sortino_ratio', 0.0):>10.4f}")
    lines.append(f"  Max Drawdown:    {agg.get('max_drawdown', 0.0):>10.2%}")
    lines.append(f"  Profit Factor:   {agg.get('profit_factor', 0.0):>10.4f}")

    # Per-fold breakdown
    splits = results.get("splits", [])
    if splits:
        lines.append("")
        lines.append("  Per-Fold Breakdown")
        lines.append("  " + "-" * 40)
        for s in splits:
            fold = s.get("fold", "?")
            tm = s.get("test_metrics", {})
            train_rows = len(s.get("train_data", []))
            test_rows = len(s.get("test_data", []))
            lines.append(
                f"  Fold {fold}: "
                f"train={train_rows} rows, test={test_rows} rows | "
                f"OOS trades={tm.get('total_trades', 0)}, "
                f"PnL=${tm.get('total_pnl', 0.0):.2f}, "
                f"WR={tm.get('win_rate', 0.0):.1%}"
            )

    # IS vs OOS comparison
    is_vs_oos = results.get("in_sample_vs_out_of_sample", [])
    if is_vs_oos:
        lines.append("")
        lines.append("  In-Sample vs Out-of-Sample Comparison")
        lines.append("  " + "-" * 40)
        for entry in is_vs_oos:
            fold = entry.get("fold", "?")
            is_pnl = entry.get("in_sample_pnl", 0.0)
            oos_pnl = entry.get("out_of_sample_pnl", 0.0)
            is_sharpe = entry.get("in_sample_sharpe", 0.0)
            oos_sharpe = entry.get("out_of_sample_sharpe", 0.0)
            lines.append(
                f"  Fold {fold}: "
                f"IS PnL=${is_pnl:>8.2f}  OOS PnL=${oos_pnl:>8.2f}  |  "
                f"IS Sharpe={is_sharpe:>6.3f}  OOS Sharpe={oos_sharpe:>6.3f}"
            )

    # Overfitting signal
    if is_vs_oos:
        is_total = sum(e.get("in_sample_pnl", 0.0) for e in is_vs_oos)
        oos_total = sum(e.get("out_of_sample_pnl", 0.0) for e in is_vs_oos)
        lines.append("")
        if oos_total < 0 < is_total:
            lines.append(
                "  ** WARNING: In-sample profitable but out-of-sample negative. "
                "Possible overfitting. **"
            )
        elif is_total > 0 and oos_total > 0:
            degradation = 1 - (oos_total / is_total) if is_total != 0 else 0
            lines.append(
                f"  Performance degradation IS -> OOS: {degradation:.1%}"
            )

    n_combos = results.get("n_combinations")
    if n_combos is not None:
        lines.append(f"\n  CPCV combinations tested: {n_combos}")

    lines.append(sep)
    return "\n".join(lines)
