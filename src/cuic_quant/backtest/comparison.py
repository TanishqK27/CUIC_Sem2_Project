"""Strategy comparison and statistical anomaly detection.

U1: compare_strategies() — run multiple strategies on the same data and
    produce a comparison table. Essential for 11 team members to evaluate
    their work side by side.

S5: detect_suspicious_results() — statistical anomaly detection that can
    catch cheating strategies (data leakage via closure) that pass all
    mechanical validator checks.
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

from cuic_quant.backtest.backtester_backend import backtest
from cuic_quant.metrics import calculate_all_metrics


# ---------------------------------------------------------------------------
# U1: Strategy Comparison
# ---------------------------------------------------------------------------


def compare_strategies(
    data: pd.DataFrame,
    strategies: dict[str, Callable],
    initial_bankroll: float = 10000.0,
    cost_pct: float = 0.0,
    cost_flat: float = 0.0,
    position_sizing: str | None = None,
    kelly_fraction: float = 0.5,
) -> pd.DataFrame:
    """Run multiple strategies on the same data and compare performance.

    Args:
        data: Historical game data from load_backtest_data().
        strategies: Dict mapping strategy names to strategy functions.
        initial_bankroll: Starting bankroll for each strategy.
        cost_pct: Percentage cost per winning trade.
        cost_flat: Flat cost per trade.
        position_sizing: Position sizing method (None or "kelly").
        kelly_fraction: Fraction of Kelly to use.

    Returns:
        DataFrame with one row per strategy and columns for each metric.
        Index is strategy_name.
    """
    rows: list[dict[str, Any]] = []

    for name, strategy_fn in strategies.items():
        try:
            results = backtest(
                data,
                strategy_fn,
                initial_bankroll=initial_bankroll,
                cost_pct=cost_pct,
                cost_flat=cost_flat,
                position_sizing=position_sizing,
                kelly_fraction=kelly_fraction,
            )

            if len(results) == 0:
                row = {
                    "strategy_name": name,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "yield_on_turnover": 0.0,
                    "sharpe_ratio": 0.0,
                    "sortino_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "profit_factor": 0.0,
                }
            else:
                metrics = calculate_all_metrics(results)
                row = {"strategy_name": name, **metrics}

        except Exception as exc:
            warnings.warn(
                f"Strategy '{name}' failed: {exc}",
                stacklevel=2,
            )
            row = {"strategy_name": name, "error": str(exc)}

        rows.append(row)

    comparison_df = pd.DataFrame(rows)
    if "strategy_name" in comparison_df.columns:
        comparison_df = comparison_df.set_index("strategy_name")

    return comparison_df


def rank_strategies(
    comparison_df: pd.DataFrame,
    metric: str = "sharpe_ratio",
    ascending: bool = False,
) -> pd.DataFrame:
    """Rank strategies by a specific metric.

    Args:
        comparison_df: Output from compare_strategies().
        metric: Column name to sort by.
        ascending: If True, lowest value ranks first.

    Returns:
        Sorted DataFrame with rank column added.
    """
    if metric not in comparison_df.columns:
        available = [c for c in comparison_df.columns if c != "error"]
        raise ValueError(f"Metric '{metric}' not found. Available: {available}")

    ranked = comparison_df.sort_values(metric, ascending=ascending).copy()
    # Use dense ranking to handle ties (equal values get same rank)
    ranked.insert(
        0, "rank",
        ranked[metric].rank(method="dense", ascending=ascending).astype("Int64").values
    )
    return ranked


def display_comparison(
    comparison_df: pd.DataFrame,
    highlight_best: bool = True,
) -> None:
    """Pretty-print a comparison table.

    Args:
        comparison_df: Output from compare_strategies().
        highlight_best: If True, mark the best value in each column.
    """
    if len(comparison_df) == 0:
        print("No strategies to compare.")
        return

    # Curated metrics with display formatting
    _METRICS = [
        ("total_trades", "Total Trades", lambda v: f"{int(v):>10d}"),
        ("win_rate", "Win Rate", lambda v: f"{v:>9.1%}"),
        ("total_pnl", "Total PnL", lambda v: f"${v:>9,.0f}"),
        ("return_on_capital", "ROI", lambda v: f"{v:>9.1%}"),
        ("sharpe_ratio", "Sharpe Ratio", lambda v: f"{v:>10.2f}"),
        ("sortino_ratio", "Sortino Ratio", lambda v: f"{v:>10.2f}"),
        ("max_drawdown", "Max Drawdown", lambda v: f"{-v:>9.1%}"),
        ("profit_factor", "Profit Factor", lambda v: f"{v:>10.2f}"),
        ("clv", "CLV", lambda v: f"{v:>+9.1%}"),
    ]

    strategies = list(comparison_df.index)
    col_width = max(14, *(len(s) + 2 for s in strategies))
    header_width = 18 + col_width * len(strategies)

    print("=" * header_width)
    print("     STRATEGY COMPARISON")
    print("=" * header_width)

    # Header row
    header = " " * 18
    for s in strategies:
        header += f"{s:>{col_width}}"
    print(header)

    # Metric rows
    for key, label, fmt in _METRICS:
        if key not in comparison_df.columns:
            continue
        row = f"  {label:<16}"
        for s in strategies:
            val = comparison_df.loc[s, key]
            row += f"{fmt(val):>{col_width}}" if not pd.isna(val) else f"{'N/A':>{col_width}}"
        print(row)

    print("=" * header_width)

    # Single-line winner by Sharpe
    if highlight_best and len(comparison_df) > 1 and "sharpe_ratio" in comparison_df.columns:
        best = comparison_df["sharpe_ratio"].idxmax()
        print(f"\n  Best risk-adjusted: {best} (Sharpe {comparison_df.loc[best, 'sharpe_ratio']:.2f})")


# ---------------------------------------------------------------------------
# S5: Statistical Anomaly / Cheating Detection
# ---------------------------------------------------------------------------


def detect_suspicious_results(
    results: pd.DataFrame,
    input_data: pd.DataFrame | None = None,
    n_trades_threshold: int = 20,
) -> dict[str, Any]:
    """Detect statistically suspicious backtest results (possible data leakage).

    A cheating strategy that reads home_win via closure achieves 100% win rate
    and passes all 11 mechanical validator checks. This function adds statistical
    anomaly detection that the validator cannot provide.

    Checks:
        1. Win rate anomaly: Is win rate significantly higher than odds imply?
        2. Perfect prediction: P(all wins by chance) = (1/avg_odds)^n.
        3. Odds-adjusted return: Actual return vs expected from odds.
        4. Entropy of outcomes: Perfectly predicted = zero entropy.
        5. Run test: Absence of expected losing streaks.

    Args:
        results: DataFrame from backtest().
        input_data: Original input data (for cross-referencing).
        n_trades_threshold: Minimum trades for meaningful analysis.

    Returns:
        Dict with is_suspicious, anomaly_score, checks, warnings.
    """
    checks: list[dict[str, Any]] = []
    report_warnings: list[str] = []

    if len(results) == 0:
        return {
            "is_suspicious": False,
            "anomaly_score": 0.0,
            "checks": [],
            "warnings": ["No trades to analyze"],
        }

    n_trades = len(results)
    outcomes = results["outcome"]
    wins = int((outcomes == "WIN").sum())
    win_rate = wins / n_trades

    if n_trades < n_trades_threshold:
        report_warnings.append(
            f"Only {n_trades} trades — statistical detection is unreliable "
            f"below {n_trades_threshold}."
        )

    # Check 1: Win rate vs implied probability from odds
    if "odds" in results.columns:
        avg_odds = float(results["odds"].mean())
        # Per-game implied probabilities (not averaged — each game tested
        # against its own odds to avoid Poisson-binomial vs binomial error).
        p_i = (1.0 / results["odds"]).clip(upper=0.999)
        implied_win_rate = float(p_i.mean())
        # Normal approximation to Poisson binomial: each game is an
        # independent Bernoulli with its own p_i = 1/odds_i.
        if n_trades >= 5:
            expected_wins = float(p_i.sum())
            variance = float((p_i * (1.0 - p_i)).sum())
            if variance > 0:
                z = (wins - expected_wins) / (variance ** 0.5)
                p_val = float(1.0 - stats.norm.cdf(z))
            else:
                p_val = 1.0
        else:
            p_val = 1.0

        checks.append({
            "name": "win_rate_vs_odds",
            "passed": p_val > 0.001,
            "p_value": p_val,
            "detail": (
                f"Win rate {win_rate:.1%} vs implied {implied_win_rate:.1%} "
                f"(avg odds {avg_odds:.2f}), p={p_val:.6f}"
            ),
        })
    else:
        avg_odds = 2.0
        implied_win_rate = 0.5

    # Check 2: Perfect prediction probability
    if n_trades >= 5:
        # P(all wins) under fair odds
        p_perfect = implied_win_rate ** n_trades
        is_suspiciously_perfect = win_rate == 1.0 and n_trades >= 10
        checks.append({
            "name": "perfect_prediction",
            "passed": not is_suspiciously_perfect,
            "p_value": p_perfect if win_rate == 1.0 else 1.0,
            "detail": (
                f"{'100% win rate' if win_rate == 1.0 else f'{win_rate:.1%} win rate'} "
                f"over {n_trades} trades. P(all wins by chance) = {p_perfect:.2e}"
            ),
        })

    # Check 3: Odds-adjusted return
    if "odds" in results.columns and "bet_size" in results.columns:
        actual_pnl = float(results["pnl"].sum())
        # Expected PnL if each bet had implied_win_rate chance of winning
        expected_pnl = 0.0
        for _, row in results.iterrows():
            implied_p = 1.0 / row["odds"] if row["odds"] > 0 else 0.5
            expected_win = row["bet_size"] * (row["odds"] - 1) * implied_p
            expected_loss = -row["bet_size"] * (1 - implied_p)
            expected_pnl += expected_win + expected_loss

        # When expected_pnl ≈ 0 (fair odds), use absolute excess instead of ratio
        # to avoid the denominator guard defaulting to 0.0 and auto-passing
        if abs(expected_pnl) > 0.01:
            pnl_ratio = actual_pnl / abs(expected_pnl)
            is_suspicious = abs(pnl_ratio) > 5.0
        else:
            # Fair odds: expected PnL ≈ 0, so any large actual PnL is suspicious
            # Use a per-trade threshold: > $50 profit per trade is suspicious at fair odds
            per_trade_excess = abs(actual_pnl) / max(n_trades, 1)
            avg_bet = float(results["bet_size"].mean()) if "bet_size" in results.columns else 100.0
            pnl_ratio = per_trade_excess / max(avg_bet, 1.0)
            is_suspicious = pnl_ratio > 0.5  # >50% return per trade at fair odds

        checks.append({
            "name": "odds_adjusted_return",
            "passed": not is_suspicious,
            "p_value": None,
            "detail": (
                f"Actual PnL ${actual_pnl:.2f} vs expected ${expected_pnl:.2f} "
                f"(ratio: {pnl_ratio:.2f}x)"
            ),
        })

    # Check 4: Shannon entropy of outcome sequence
    if n_trades >= 10:
        p_win = win_rate
        p_loss = 1 - win_rate
        if p_win > 0 and p_loss > 0:
            entropy = -(p_win * math.log2(p_win) + p_loss * math.log2(p_loss))
        elif p_win == 1.0 or p_loss == 1.0:
            entropy = 0.0
        else:
            entropy = 0.0

        # Maximum entropy for binary outcome is 1.0.
        # Only flag when entropy == 0 (100% or 0% win rate).  The Poisson
        # binomial test already handles mixed-odds significance; a fixed
        # entropy threshold produces false positives on legitimate
        # high-win-rate strategies (e.g. heavy favourites).
        checks.append({
            "name": "outcome_entropy",
            "passed": entropy > 0.0,
            "p_value": None,
            "detail": f"Shannon entropy = {entropy:.4f} (max 1.0)",
        })

    # Check 5: Run test for randomness of wins/losses
    if n_trades >= 10:
        # Count runs (consecutive same-outcome sequences)
        outcome_binary = (outcomes == "WIN").astype(int).values
        runs = 1
        for i in range(1, len(outcome_binary)):
            if outcome_binary[i] != outcome_binary[i - 1]:
                runs += 1

        # Expected runs under randomness
        n1 = wins
        n2 = n_trades - wins
        expected_runs = float(n_trades)  # default
        z_runs = 0.0
        p_runs = 1.0
        if n1 > 0 and n2 > 0:
            expected_runs = 1 + (2 * n1 * n2) / (n1 + n2)
            denom = (n1 + n2) ** 2 * (n1 + n2 - 1)
            if denom > 0:
                var_runs = (
                    (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / denom
                )
                if var_runs > 0:
                    z_runs = (runs - expected_runs) / math.sqrt(var_runs)
                    p_runs = 2 * (1 - stats.norm.cdf(abs(z_runs)))

        checks.append({
            "name": "runs_test",
            "passed": p_runs > 0.01,
            "p_value": p_runs,
            "detail": (
                f"{runs} runs observed, ~{expected_runs:.1f} expected "
                f"(z={z_runs:.2f}, p={p_runs:.4f})"
            ),
        })

    # Check 6: Bet-size-outcome correlation (catches the #1 bypass: big bets on known wins)
    if "bet_size" in results.columns and n_trades >= 10:
        outcome_binary = (outcomes == "WIN").astype(float).values
        bet_sizes = results["bet_size"].values
        # Only run if bet sizes vary (constant bet sizes can't correlate)
        if np.std(bet_sizes) > 1e-6:
            corr, p_corr = stats.pointbiserialr(outcome_binary, bet_sizes)
            # Strong positive correlation = bigger bets on wins = likely leakage
            is_corr_suspicious = corr > 0.3 and p_corr < 0.05
            checks.append({
                "name": "bet_size_outcome_correlation",
                "passed": not is_corr_suspicious,
                "p_value": float(p_corr),
                "detail": (
                    f"Point-biserial r={corr:.3f}, p={p_corr:.4f}. "
                    f"Suspicious if r>0.3 with p<0.05 (bigger bets on wins = possible leakage)."
                ),
            })

    # Compute overall anomaly score (0-1)
    n_failed = sum(1 for c in checks if not c["passed"])
    anomaly_score = n_failed / max(len(checks), 1)

    is_suspicious = anomaly_score >= 0.4 or (win_rate == 1.0 and n_trades >= 10)

    if is_suspicious:
        report_warnings.append(
            f"SUSPICIOUS: {n_failed}/{len(checks)} anomaly checks failed. "
            f"Win rate {win_rate:.1%} over {n_trades} trades may indicate data leakage."
        )

    return {
        "is_suspicious": is_suspicious,
        "anomaly_score": anomaly_score,
        "checks": checks,
        "warnings": report_warnings,
        "n_trades": n_trades,
        "win_rate": win_rate,
    }


def implied_edge_analysis(
    results: pd.DataFrame,
) -> dict[str, float]:
    """Calculate implied edge from results vs what odds suggest.

    Args:
        results: DataFrame from backtest() with odds column.

    Returns:
        Dict with actual_win_rate, implied_win_rate, edge, edge_pct.
    """
    if len(results) == 0 or "odds" not in results.columns:
        return {"actual_win_rate": 0.0, "implied_win_rate": 0.0, "edge": 0.0, "edge_pct": 0.0}

    actual_win_rate = float((results["outcome"] == "WIN").mean())
    implied_win_rate = float((1.0 / results["odds"]).mean())
    edge = actual_win_rate - implied_win_rate

    return {
        "actual_win_rate": actual_win_rate,
        "implied_win_rate": implied_win_rate,
        "edge": edge,
        "edge_pct": edge * 100,
    }


def validate_no_leakage_statistical(
    results: pd.DataFrame,
    input_data: pd.DataFrame | None = None,
    alpha: float = 0.01,
) -> dict[str, Any]:
    """Enhanced validator adding statistical leakage checks.

    Complements validate_backtest_results() in backtester_backend.py
    with checks that can detect data leakage even when mechanical checks pass.

    Args:
        results: DataFrame from backtest().
        input_data: Original input data.
        alpha: Significance threshold.

    Returns:
        Dict with passed, checks, warnings.
    """
    detection = detect_suspicious_results(results, input_data)

    passed = not detection["is_suspicious"]
    return {
        "passed": passed,
        "anomaly_score": detection["anomaly_score"],
        "checks": detection["checks"],
        "warnings": detection["warnings"],
    }


__all__ = [
    "compare_strategies",
    "rank_strategies",
    "display_comparison",
    "detect_suspicious_results",
    "implied_edge_analysis",
    "validate_no_leakage_statistical",
]
