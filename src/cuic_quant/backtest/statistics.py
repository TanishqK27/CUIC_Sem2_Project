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
from itertools import combinations
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

    # P-value — S2: use implied win rate from odds as null, not 0.5
    null_h = 0.5
    if "odds" in results_df.columns:
        implied = 1.0 / results_df["odds"].astype(float)
        implied_mean = float(implied.mean())
        if 0.0 < implied_mean < 1.0:
            null_h = implied_mean
    p_value = calculate_p_value(win_rate, total, null_hypothesis=null_h)

    # Bootstrap CIs
    pnl = results_df["pnl"]
    pnl_ci = bootstrap_confidence_interval(pnl, confidence_level=0.95)
    roi_ci = (0.0, 0.0, 0.0)
    if "bet_size" in results_df.columns:
        total_wagered = results_df["bet_size"].sum()
        if total_wagered > 0:
            pnl_arr = pnl.values
            bet_arr = results_df["bet_size"].values
            rng = np.random.default_rng(42)
            roi_boot = []
            for _ in range(10_000):
                idx = rng.integers(0, len(pnl_arr), size=len(pnl_arr))
                wager = bet_arr[idx].sum()
                if wager > 0:
                    roi_boot.append(pnl_arr[idx].sum() / wager)
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


def benjamini_hochberg_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[bool]:
    """Benjamini-Hochberg FDR correction for multiple testing.

    Controls the false discovery rate (expected proportion of false
    positives among rejections). Less conservative than Bonferroni/Holm
    for large strategy pools.

    Algorithm (Benjamini & Hochberg, 1995):
      1. Sort p-values ascending with rank i (1-indexed)
      2. Threshold for rank i: (i / n) * alpha
      3. Find largest k where p[k] <= threshold[k]
      4. Reject all hypotheses with rank <= k

    Args:
        p_values: List of p-values from multiple strategy tests.
        alpha: False discovery rate to control.

    Returns:
        List of bools: True if significant after FDR correction.
    """
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values with original indices
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])

    # Find largest rank k where p[k] <= (k/n) * alpha
    max_k = -1
    for rank_0, (_orig_idx, p) in enumerate(indexed):
        rank_1 = rank_0 + 1  # BH uses 1-indexed ranks
        if p <= (rank_1 / n) * alpha:
            max_k = rank_0

    # Reject all hypotheses with rank <= max_k
    significant = [False] * n
    for rank_0, (orig_idx, _p) in enumerate(indexed):
        if rank_0 <= max_k:
            significant[orig_idx] = True

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
    radicand = (1 - skewness * observed_sharpe + ((kurtosis - 1) / 4) * sr2) / max(n_observations - 1, 1)
    if radicand <= 0:
        return 1.0
    se_sharpe = math.sqrt(radicand)

    if se_sharpe < 1e-10:
        return 1.0

    # Probability of observing this Sharpe or higher by chance
    z = (observed_sharpe - expected_max_sharpe) / se_sharpe
    p_value = 1 - stats.norm.cdf(z)

    return float(p_value)


def build_returns_matrix(
    strategy_results: list[pd.DataFrame],
    freq: str = "D",
) -> np.ndarray:
    """Build a (n_periods x n_strategies) returns matrix for CSCV PBO.

    Resamples trade-level PnL from multiple strategy backtests onto a
    common time grid, filling periods with no trades with 0.0.

    Args:
        strategy_results: List of DataFrames from backtest(), each with
            'timestamp' and 'pnl' columns.
        freq: Resample frequency. Default "D" (daily). Use "W" for weekly.

    Returns:
        2D numpy array (n_periods x n_strategies) suitable for
        probability_of_backtest_overfitting().

    Raises:
        ValueError: If fewer than 2 strategy results are provided, or
            if any DataFrame is missing required columns.
    """
    if len(strategy_results) < 2:
        raise ValueError("Need at least 2 strategy results to build returns matrix")

    resampled = []
    for i, df in enumerate(strategy_results):
        if "timestamp" not in df.columns or "pnl" not in df.columns:
            raise ValueError(f"Strategy result {i} missing 'timestamp' or 'pnl' column")
        series = df.set_index(pd.to_datetime(df["timestamp"]))["pnl"]
        resampled.append(series.resample(freq).sum())

    # Align all strategies to a common time index, fill missing with 0
    combined = pd.concat(resampled, axis=1).fillna(0.0)
    return combined.values


def probability_of_backtest_overfitting(
    returns_matrix: np.ndarray,
    n_groups: int = 16,
) -> dict[str, Any]:
    """Probability of Backtest Overfitting via CSCV (Bailey et al. 2017).

    Combinatorial Symmetric Cross-Validation: partition time series into
    S equal-sized groups, enumerate all C(S, S/2) train/test splits, and
    check how often the IS-optimal strategy underperforms OOS.

    Args:
        returns_matrix: 2D array (n_periods x n_strategies). Each column
            is a strategy's return series.
        n_groups: Number of time-series groups (must be even, >= 4).
            Default 16 gives C(16,8) = 12,870 combinations.

    Returns:
        Dict with:
            pbo: float — probability of overfitting [0, 1]
            logit_distribution: list[float] — logit of relative OOS rank
                for the IS-best strategy in each combination
            n_combinations: int — number of train/test splits tested

    Raises:
        ValueError: If n_groups is odd, < 4, or returns_matrix has
            fewer rows than n_groups.
    """
    returns_matrix = np.asarray(returns_matrix, dtype=float)
    if returns_matrix.ndim != 2:
        raise ValueError(f"returns_matrix must be 2D, got {returns_matrix.ndim}D")
    if not np.isfinite(returns_matrix).all():
        raise ValueError("returns_matrix contains NaN or inf values")

    n_periods, n_strategies = returns_matrix.shape
    if n_strategies < 2:
        return {"pbo": 0.0, "logit_distribution": [], "n_combinations": 0}

    if n_groups < 4 or n_groups % 2 != 0:
        raise ValueError(f"n_groups must be even and >= 4, got {n_groups}")

    if n_periods < n_groups:
        raise ValueError(
            f"Need at least {n_groups} rows for {n_groups} groups, got {n_periods}"
        )

    # Split rows into n_groups equal blocks (discard trailing rows)
    block_size = n_periods // n_groups
    blocks = [
        returns_matrix[i * block_size : (i + 1) * block_size]
        for i in range(n_groups)
    ]

    half = n_groups // 2
    from math import comb
    n_combos = comb(n_groups, half)
    if n_combos > 50_000:
        warnings.warn(
            f"CSCV with n_groups={n_groups} generates {n_combos:,} combinations. "
            f"This may take a while. Consider reducing n_groups.",
            stacklevel=2,
        )
    logits: list[float] = []

    for is_indices in combinations(range(n_groups), half):
        oos_indices = [i for i in range(n_groups) if i not in is_indices]

        # Concatenate blocks for IS and OOS
        is_returns = np.concatenate([blocks[i] for i in is_indices], axis=0)
        oos_returns = np.concatenate([blocks[i] for i in oos_indices], axis=0)

        # Compute Sharpe per strategy (mean / std, annualization not needed
        # since we only care about relative ranking)
        is_means = is_returns.mean(axis=0)
        is_stds = is_returns.std(axis=0, ddof=1)
        is_stds[is_stds < 1e-10] = 1e-10
        is_sharpes = is_means / is_stds

        oos_means = oos_returns.mean(axis=0)
        oos_stds = oos_returns.std(axis=0, ddof=1)
        oos_stds[oos_stds < 1e-10] = 1e-10
        oos_sharpes = oos_means / oos_stds

        # Find IS-best strategy
        best_is_idx = int(np.argmax(is_sharpes))

        # Rank of IS-best in OOS (1 = best, N = worst)
        # Use negative to sort descending
        oos_ranks = np.argsort(np.argsort(-oos_sharpes)) + 1  # 1-indexed ranks
        oos_rank = int(oos_ranks[best_is_idx])

        # Logit of relative rank: log(rank / (N + 1 - rank))
        # Positive logit → IS-best underperforms OOS (below median)
        denom = n_strategies + 1 - oos_rank
        logit = math.log(oos_rank / max(denom, 1))
        logits.append(logit)

    # PBO = fraction of combinations where logit > 0
    pbo = sum(1 for lg in logits if lg > 0) / len(logits) if logits else 0.0

    return {
        "pbo": float(pbo),
        "logit_distribution": logits,
        "n_combinations": len(logits),
    }


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
            - skewness (float, optional): Return skewness for DSR. Default 0.0.
            - kurtosis (float, optional): Return kurtosis for DSR. Default 3.0.
        alpha: Family-wise error rate for corrections.

    Returns:
        Dict with bonferroni_significant, holm_significant,
        benjamini_hochberg_significant, n_significant_bh,
        deflated_sharpe_pvalues, warnings, and more.
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

    # Benjamini-Hochberg FDR correction
    bh_sig = benjamini_hochberg_correction(p_values, alpha)

    # Deflated Sharpe Ratios
    deflated = []
    for sr in strategy_results:
        dsr = deflated_sharpe_ratio(
            observed_sharpe=sr.get("sharpe", 0.0),
            n_trials=n_strategies,
            n_observations=sr.get("n_trades", 100),
            skewness=sr.get("skewness", 0.0),
            kurtosis=sr.get("kurtosis", 3.0),
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
    n_bh = sum(bh_sig)

    return {
        "n_strategies": n_strategies,
        "strategy_names": names,
        "raw_p_values": p_values,
        "bonferroni_significant": bonferroni_sig,
        "holm_significant": holm_sig,
        "benjamini_hochberg_significant": bh_sig,
        "n_significant_raw": n_significant_raw,
        "n_significant_bonferroni": n_bonferroni,
        "n_significant_holm": n_holm,
        "n_significant_bh": n_bh,
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
    "benjamini_hochberg_correction",
    "deflated_sharpe_ratio",
    "probability_of_backtest_overfitting",
    "overfitting_report",
]
