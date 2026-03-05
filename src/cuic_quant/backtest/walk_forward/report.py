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
    lines.append("  Out-of-Sample Performance (aggregated across folds)")
    lines.append("  " + "-" * 46)
    lines.append(f"  Total Trades:    {agg.get('total_trades', 0):>10}")
    lines.append(f"  Win Rate:        {agg.get('win_rate', 0.0):>10.1%}")
    lines.append(f"  Total PnL:       ${agg.get('total_pnl', 0.0):>9,.0f}")
    lines.append(f"  Sharpe Ratio:    {agg.get('sharpe_ratio', 0.0):>10.2f}")
    lines.append(f"  Max Drawdown:    {-agg.get('max_drawdown', 0.0):>9.1%}")
    lines.append(f"  Profit Factor:   {agg.get('profit_factor', 0.0):>10.2f}")

    # Per-fold breakdown (compact)
    splits = results.get("splits", [])
    if splits:
        lines.append("")
        lines.append("  Per-Fold Results")
        lines.append("  " + "-" * 46)
        for s in splits:
            fold = s.get("fold", "?")
            tm = s.get("test_metrics", {})
            n_train = len(s.get("train_data", []))
            n_test = len(s.get("test_data", []))
            wr = tm.get("win_rate", 0.0)
            pnl = tm.get("total_pnl", 0.0)
            lines.append(
                f"  Fold {fold}: {n_train} train / {n_test} test "
                f"-> {tm.get('total_trades', 0)} bets, "
                f"{wr:.0%} WR, ${pnl:,.0f} PnL"
            )

    # Overfitting check
    is_vs_oos = results.get("in_sample_vs_out_of_sample", [])
    if is_vs_oos:
        is_total = sum(e.get("in_sample_pnl", 0.0) for e in is_vs_oos)
        oos_total = sum(e.get("out_of_sample_pnl", 0.0) for e in is_vs_oos)

        lines.append("")
        lines.append("  Overfitting Check")
        lines.append("  " + "-" * 46)

        if oos_total < 0 < is_total:
            lines.append(
                "  LIKELY OVERFIT: Profitable in-sample but "
                "negative out-of-sample."
            )
        elif is_total > 0 and oos_total > 0:
            degradation = 1 - (oos_total / is_total) if is_total != 0 else 0
            if degradation > 0.5:
                verdict = "HIGH degradation — possible overfitting"
            elif degradation > 0.25:
                verdict = "MODERATE degradation — monitor closely"
            else:
                verdict = "LOW degradation — looks stable"
            lines.append(
                f"  IS PnL: ${is_total:,.0f}  ->  OOS PnL: ${oos_total:,.0f}  "
                f"({degradation:.0%} drop)"
            )
            lines.append(f"  Verdict: {verdict}")
        elif is_total <= 0 and oos_total <= 0:
            lines.append("  Both IS and OOS negative — no edge detected.")
        else:
            lines.append(
                f"  IS PnL: ${is_total:,.0f}  ->  OOS PnL: ${oos_total:,.0f}"
            )

    n_combos = results.get("n_combinations")
    if n_combos is not None:
        lines.append(f"\n  CPCV combinations tested: {n_combos}")

    lines.append(sep)
    return "\n".join(lines)
