"""Statistical significance testing and overfitting protection.

S3: Provides p-values, bootstrap confidence intervals, and minimum sample
    size calculations to determine if backtest results are statistically
    meaningful.

S4: Provides multiple-testing corrections (Bonferroni, Holm-Bonferroni),
    Deflated Sharpe Ratio, and Probability of Backtest Overfitting to
    guard against data-snooping bias when evaluating many strategies.

References:
    - Bailey & Lopez de Prado (2014): "The Deflated Sharpe Ratio"
    - Bailey et al. (2017): "Probability of Backtest Overfitting"
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# S3: Statistical Significance Testing
# ---------------------------------------------------------------------------


def calculate_p_value(
    win_rate: float,
    n_trades: int,
    null_hypothesis: float = 0.5,
    alternative: str = "greater",
) -> float:
    """Binomial test p-value for win rate vs null hypothesis.

    Uses a one-sided test by default ("greater") because in betting strategy
    evaluation, we care whether the win rate is *better* than the null — a
    strategy with a 30% win rate is not "significant" in a useful sense.

    Args:
        win_rate: Observed win rate (0-1).
        n_trades: Number of trades.
        null_hypothesis: Expected win rate under null (default 0.5 = no edge).
        alternative: Test direction. "greater" (default) tests if win_rate
            exceeds null. "two-sided" tests if it differs in either direction.

    Returns:
        P-value. Lower means more significant (win rate > null with high confidence).
    """
    if n_trades <= 0:
        return 1.0
    wins = int(round(win_rate * n_trades))
    result = stats.binomtest(wins, n_trades, null_hypothesis, alternative=alternative)
    return float(result.pvalue)


def bootstrap_confidence_interval(
    pnl_series: pd.Series,
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95,
    metric_fn: Callable[[pd.Series], float] | None = None,
    seed: int | None = 42,
) -> tuple[float, float, float]:
    """Bootstrap confidence interval for any metric.

    Args:
        pnl_series: Series of PnL values (or any numeric series).
        n_bootstrap: Number of bootstrap resamples.
        confidence_level: Confidence level (e.g. 0.95 for 95% CI).
        metric_fn: Function to compute metric from a series.
            Default: np.mean.
        seed: Random seed for reproducibility.

    Returns:
        (lower, point_estimate, upper) tuple.
    """
    data = pnl_series.dropna().values
    if len(data) == 0:
        return (0.0, 0.0, 0.0)

    if metric_fn is None:
        metric_fn = lambda s: float(np.mean(s))

    rng = np.random.default_rng(seed)
    point_estimate = metric_fn(pd.Series(data))

    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = rng.choice(data, size=len(data), replace=True)
        bootstrap_stats.append(metric_fn(pd.Series(sample)))

    bootstrap_stats = np.array(bootstrap_stats)
    alpha = 1 - confidence_level
    lower = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    upper = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))

    return (lower, point_estimate, upper)


def minimum_sample_size(
    expected_edge: float = 0.05,
    power: float = 0.80,
    alpha: float = 0.01,
) -> int:
    """Calculate minimum bets needed for statistical significance.

    Uses normal approximation to the binomial for sample size calculation.

    Args:
        expected_edge: Expected edge over null (e.g. 0.05 for 55% vs 50%).
        power: Statistical power (probability of detecting true effect).
        alpha: Significance level.

    Returns:
        Minimum number of bets required.
    """
    if expected_edge <= 0:
        return 0

    p0 = 0.5  # null hypothesis
    p1 = p0 + expected_edge

    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    # Sample size formula for comparing two proportions (one-sample version)
    numerator = (z_alpha * math.sqrt(p0 * (1 - p0)) + z_beta * math.sqrt(p1 * (1 - p1))) ** 2
    denominator = (p1 - p0) ** 2

    return int(math.ceil(numerator / denominator))


def significance_report(results_df: pd.DataFrame) -> dict[str, Any]:
    """Generate comprehensive significance report for backtest results.

    Args:
        results_df: DataFrame from backtest() with outcome, pnl columns.

    Returns:
        Dict with p_value, confidence_intervals, sample_size_assessment,
        is_significant, warnings.
    """
    report_warnings: list[str] = []

    if len(results_df) == 0:
        return {
            "p_value": 1.0,
            "confidence_intervals": {},
            "sample_size_assessment": "No trades",
            "is_significant": False,
            "warnings": ["No trades to analyze"],
        }

    outcomes = results_df["outcome"]
    wins = int((outcomes == "WIN").sum())
    total = len(outcomes)
    win_rate = wins / total if total > 0 else 0.0

    # P-value
    p_value = calculate_p_value(win_rate, total)

    # Bootstrap CIs
    pnl = results_df["pnl"]
    pnl_ci = bootstrap_confidence_interval(pnl, confidence_level=0.95)
    roi_ci = (0.0, 0.0, 0.0)
    if "bet_size" in results_df.columns:
        total_wagered = results_df["bet_size"].sum()
        if total_wagered > 0:
            pnl_arr = pnl.values
            bet_arr = results_df["bet_size"].values
            per_bet_roi = pnl_arr / bet_arr
            rng = np.random.default_rng(42)
            roi_boot = []
            for _ in range(10_000):
                idx = rng.integers(0, len(pnl_arr), size=len(pnl_arr))
                roi_boot.append(float(np.mean(per_bet_roi[idx])))
            roi_boot = np.array(roi_boot)
            roi_ci = (
                float(np.percentile(roi_boot, 2.5)),
                float(pnl_arr.sum() / total_wagered),
                float(np.percentile(roi_boot, 97.5)),
            )

    # Sample size assessment
    min_needed = minimum_sample_size(expected_edge=0.05, power=0.80, alpha=0.01)
    if total < min_needed:
        assessment = f"INSUFFICIENT: {total} trades < {min_needed} needed (for 5% edge detection)"
        report_warnings.append(
            f"Sample size too small. Need ~{min_needed} bets to detect a 5% edge "
            f"at p<0.01 with 80% power. Got {total}."
        )
    else:
        assessment = f"ADEQUATE: {total} trades >= {min_needed} needed"

    if total < 30:
        report_warnings.append(
            f"With only {total} trades, the 95% CI on ROI is extremely wide. "
            f"Results are statistically unreliable."
        )

    return {
        "p_value": p_value,
        "confidence_intervals": {
            "mean_pnl_95ci": pnl_ci,
            "roi_95ci": roi_ci,
        },
        "sample_size_assessment": assessment,
        "is_significant": p_value < 0.01,
        "n_trades": total,
        "win_rate": win_rate,
        "min_sample_needed": min_needed,
        "warnings": report_warnings,
    }


# ---------------------------------------------------------------------------
# S4: Overfitting Protection
# ---------------------------------------------------------------------------


def bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[bool]:
    """Apply Bonferroni correction for multiple testing.

    Args:
        p_values: List of p-values from multiple strategy tests.
        alpha: Family-wise error rate.

    Returns:
        List of bools: True if significant after correction.
    """
    n = len(p_values)
    if n == 0:
        return []
    adjusted_alpha = alpha / n
    return [p < adjusted_alpha for p in p_values]


def holm_bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[bool]:
    """Holm-Bonferroni step-down procedure (less conservative than Bonferroni).

    Args:
        p_values: List of p-values.
        alpha: Family-wise error rate.

    Returns:
        List of bools: True if significant after correction.
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with original indices
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    significant = [False] * n

    for rank, (orig_idx, p) in enumerate(indexed):
        adjusted_alpha = alpha / (n - rank)
        if p < adjusted_alpha:
            significant[orig_idx] = True
        else:
            # Once a test fails, all subsequent (larger p) also fail
            break

    return significant


def deflated_sharpe_ratio(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    sharpe_std: float = 1.0,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014).

    Adjusts for multiple testing by estimating the probability that the
    observed Sharpe ratio exceeds what we'd expect from the best of
    n_trials random strategies.

    Uses the full standard error formula from the paper that accounts for
    non-normality via skewness and kurtosis terms. This is important for
    binary betting returns which are typically highly skewed (skew -1 to -3)
    with excess kurtosis (5+).

    Args:
        observed_sharpe: The observed annualized Sharpe ratio.
        n_trials: Number of strategies tested (e.g., 55 for 11 members * 5 each).
        n_observations: Number of return observations.
        sharpe_std: Assumed standard deviation of Sharpe ratios across trials.
        skewness: Skewness of returns. Default 0.0 (Gaussian). Binary betting
            returns typically have skewness -1 to -3.
        kurtosis: Kurtosis of returns (not excess). Default 3.0 (Gaussian).
            Binary betting returns typically have kurtosis 5+.

    Returns:
        DSR p-value (probability that observed Sharpe is due to chance).
        Lower is better (more likely genuine).
    """
    if n_trials <= 0 or n_observations <= 0:
        return 1.0

    # Expected maximum Sharpe from n_trials random strategies (Euler-Mascheroni)
    euler_mascheroni = 0.5772156649
    expected_max_sharpe = sharpe_std * (
        (1 - euler_mascheroni) * stats.norm.ppf(1 - 1 / n_trials)
        + euler_mascheroni * stats.norm.ppf(1 - 1 / (n_trials * math.e))
    )

    # Standard error of the Sharpe ratio — full formula from Bailey & LdP (2014)
    # SE(SR) = sqrt( (1 - skew*SR + (kurtosis-1)/4 * SR^2) / (n-1) )
    # Where kurtosis is standard kurtosis (3 for Gaussian)
    sr2 = observed_sharpe ** 2
    se_sharpe = math.sqrt(
        (1 - skewness * observed_sharpe + ((kurtosis - 1) / 4) * sr2) / max(n_observations - 1, 1)
    )

    if se_sharpe < 1e-10:
        return 1.0

    # Probability of observing this Sharpe or higher by chance
    z = (observed_sharpe - expected_max_sharpe) / se_sharpe
    p_value = 1 - stats.norm.cdf(z)

    return float(p_value)


def probability_of_backtest_overfitting(
    sharpe_ratios_in_sample: list[float],
    sharpe_ratios_out_of_sample: list[float],
) -> float:
    """Simplified overfitting probability estimate.

    NOTE: This is a simplified single-split rank test, NOT the full
    Combinatorial Symmetric Cross-Validation (CSCV) algorithm from
    Bailey et al. (2017). The full CSCV algorithm uses all possible
    train/test partition combinations and a logit model. This simplified
    version gives a coarse estimate from a single IS/OOS split.

    For N strategies, output is quantized to multiples of 1/(N-1).
    For rigorous PBO, use combinatorial_purged_cv() from walk_forward.py
    with multiple split combinations.

    Estimates the probability that the best in-sample strategy
    underperforms out-of-sample by checking what fraction of other
    strategies beat it OOS.

    Args:
        sharpe_ratios_in_sample: In-sample Sharpe for each strategy.
        sharpe_ratios_out_of_sample: Out-of-sample Sharpe for same strategies.

    Returns:
        Overfitting estimate (0-1). Higher means more likely overfitting.
        Quantized to 1/(N-1) increments.
    """
    if len(sharpe_ratios_in_sample) != len(sharpe_ratios_out_of_sample):
        raise ValueError("IS and OOS lists must have same length")

    n = len(sharpe_ratios_in_sample)
    if n < 2:
        return 0.0

    # Find the strategy with the best in-sample Sharpe
    best_is_idx = int(np.argmax(sharpe_ratios_in_sample))
    best_is_oos = sharpe_ratios_out_of_sample[best_is_idx]

    # Count how many strategies had better OOS performance
    n_better_oos = sum(
        1 for i in range(n)
        if i != best_is_idx and sharpe_ratios_out_of_sample[i] > best_is_oos
    )

    # Fraction of strategies that beat the "best" IS strategy OOS
    pbo = n_better_oos / (n - 1) if n > 1 else 0.0
    return float(pbo)


def overfitting_report(
    strategy_results: list[dict[str, Any]],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Generate overfitting report for a set of strategies.

    Args:
        strategy_results: List of dicts, each with keys:
            - name (str): Strategy name
            - sharpe (float): Sharpe ratio
            - p_value (float): P-value from significance test
            - n_trades (int): Number of trades
        alpha: Family-wise error rate for corrections.

    Returns:
        Dict with corrected_p_values, significant_after_correction,
        deflated_sharpes, warnings.
    """
    report_warnings: list[str] = []
    n_strategies = len(strategy_results)

    if n_strategies == 0:
        return {
            "n_strategies": 0,
            "corrected_significant": [],
            "deflated_sharpes": [],
            "warnings": ["No strategies to analyze"],
        }

    p_values = [sr.get("p_value", 1.0) for sr in strategy_results]
    names = [sr.get("name", f"Strategy_{i}") for i, sr in enumerate(strategy_results)]

    # Bonferroni correction
    bonferroni_sig = bonferroni_correction(p_values, alpha)

    # Holm-Bonferroni correction
    holm_sig = holm_bonferroni_correction(p_values, alpha)

    # Deflated Sharpe Ratios
    deflated = []
    for sr in strategy_results:
        dsr = deflated_sharpe_ratio(
            observed_sharpe=sr.get("sharpe", 0.0),
            n_trials=n_strategies,
            n_observations=sr.get("n_trades", 100),
        )
        deflated.append(dsr)

    # Expected false positives
    expected_false = n_strategies * alpha
    n_significant_raw = sum(1 for p in p_values if p < alpha)

    if n_significant_raw > 0 and n_significant_raw <= expected_false * 2:
        report_warnings.append(
            f"{n_significant_raw} strategies appear significant at alpha={alpha}, "
            f"but ~{expected_false:.1f} are expected by chance alone with "
            f"{n_strategies} tests."
        )

    n_bonferroni = sum(bonferroni_sig)
    n_holm = sum(holm_sig)

    return {
        "n_strategies": n_strategies,
        "strategy_names": names,
        "raw_p_values": p_values,
        "bonferroni_significant": bonferroni_sig,
        "holm_significant": holm_sig,
        "n_significant_raw": n_significant_raw,
        "n_significant_bonferroni": n_bonferroni,
        "n_significant_holm": n_holm,
        "deflated_sharpe_pvalues": deflated,
        "expected_false_positives": expected_false,
        "warnings": report_warnings,
    }


__all__ = [
    "calculate_p_value",
    "bootstrap_confidence_interval",
    "minimum_sample_size",
    "significance_report",
    "bonferroni_correction",
    "holm_bonferroni_correction",
    "deflated_sharpe_ratio",
    "probability_of_backtest_overfitting",
    "overfitting_report",
]
