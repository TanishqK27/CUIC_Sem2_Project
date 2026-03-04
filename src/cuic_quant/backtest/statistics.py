"""Statistical tests for backtest results.

Provides:
  - Binomial test (is win rate significantly above implied probability?)
  - Bootstrap confidence intervals for key metrics
  - Bonferroni / Holm-Bonferroni multiple-testing correction
  - Deflated Sharpe Ratio (DSR) — corrects for multiple strategy trials
  - Probability of Backtest Overfitting (PBO) via CPCV rank statistics

All functions accept a trades DataFrame (output of run_walk_forward) and
return scalar values or DataFrames suitable for notebook display.

References:
    - Harvey, C.R. & Liu, Y. (2015). "Backtesting". Journal of Portfolio
      Management.
    - Bailey, D.H. et al. (2014). "Pseudo-Mathematics and Financial
      Charlatanism". Notices of the AMS.
    - Lopez de Prado, M. (2018). Advances in Financial Machine Learning.
"""

from __future__ import annotations

import math
import warnings
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Binomial test
# ---------------------------------------------------------------------------

def binomial_test(
    trades: pd.DataFrame,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Test whether the win rate is significantly above implied probability.

    H0: win_rate == mean(implied_prob)  (no edge)
    H1: win_rate > mean(implied_prob)   (positive edge)

    Uses a one-sided binomial test.

    Args:
        trades: Backtest trades DataFrame.
        alpha: Significance level.

    Returns:
        Dictionary with keys: wins, n_bets, win_rate, expected_rate,
        p_value, significant.
    """
    outcomes = trades["outcome"].astype(str).str.upper()
    wins = int((outcomes == "WIN").sum())
    n = len(outcomes)

    if n == 0:
        return {"wins": 0, "n_bets": 0, "win_rate": 0.0, "expected_rate": 0.0,
                "p_value": 1.0, "significant": False}

    if "implied_prob" in trades.columns:
        expected_rate = float(pd.to_numeric(trades["implied_prob"], errors="coerce").mean())
    else:
        expected_rate = 0.5

    result = stats.binomtest(wins, n, expected_rate, alternative="greater")
    p_value = float(result.pvalue)

    return {
        "wins": wins,
        "n_bets": n,
        "win_rate": round(wins / n, 4),
        "expected_rate": round(expected_rate, 4),
        "p_value": round(p_value, 6),
        "significant": p_value < alpha,
    }


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def bootstrap_ci(
    series: pd.Series,
    stat_fn: Callable[[pd.Series], float],
    n_bootstrap: int = 2000,
    ci_level: float = 0.95,
    seed: int = 42,
) -> dict[str, float]:
    """Compute bootstrap confidence interval for a scalar statistic.

    Args:
        series: Input data series.
        stat_fn: Function mapping a Series to a scalar float.
        n_bootstrap: Number of bootstrap samples.
        ci_level: Confidence level (e.g. 0.95 for 95% CI).
        seed: Random seed.

    Returns:
        Dictionary with keys: point_estimate, lower, upper, ci_level.
    """
    rng = np.random.default_rng(seed)
    data = pd.to_numeric(series, errors="coerce").dropna().values
    n = len(data)

    if n == 0:
        return {"point_estimate": 0.0, "lower": 0.0, "upper": 0.0, "ci_level": ci_level}

    point = stat_fn(pd.Series(data))
    bootstrap_stats = np.array([
        stat_fn(pd.Series(rng.choice(data, size=n, replace=True)))
        for _ in range(n_bootstrap)
    ])

    alpha = 1 - ci_level
    lower = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    upper = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))

    return {
        "point_estimate": round(point, 6),
        "lower": round(lower, 6),
        "upper": round(upper, 6),
        "ci_level": ci_level,
    }


# ---------------------------------------------------------------------------
# Multiple testing corrections
# ---------------------------------------------------------------------------

def bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction controls the family-wise error rate (FWER)
    by dividing the significance threshold by the number of tests.

    Args:
        p_values: List of p-values from individual strategy tests.
        alpha: Desired FWER level.

    Returns:
        DataFrame with columns: p_value, corrected_threshold, significant.
    """
    m = len(p_values)
    threshold = alpha / m if m > 0 else alpha
    return pd.DataFrame({
        "p_value": p_values,
        "corrected_threshold": [threshold] * m,
        "significant": [p < threshold for p in p_values],
    })


def holm_bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Apply Holm-Bonferroni stepwise correction.

    Less conservative than Bonferroni while still controlling FWER.
    Tests are ordered by p-value; threshold for the k-th smallest is
    alpha / (m - k + 1).

    Args:
        p_values: List of p-values.
        alpha: Desired FWER level.

    Returns:
        DataFrame indexed by original position with columns: p_value,
        rank, corrected_threshold, significant.
    """
    m = len(p_values)
    if m == 0:
        return pd.DataFrame(columns=["p_value", "rank", "corrected_threshold", "significant"])

    order = np.argsort(p_values)
    sorted_p = np.array(p_values)[order]
    thresholds = [alpha / (m - k) for k in range(m)]

    # Once a test fails, all subsequent also fail
    significant = []
    passed_so_far = True
    for p, t in zip(sorted_p, thresholds):
        if passed_so_far and p < t:
            significant.append(True)
        else:
            passed_so_far = False
            significant.append(False)

    result = pd.DataFrame({
        "original_index": order,
        "p_value": sorted_p,
        "rank": range(1, m + 1),
        "corrected_threshold": thresholds,
        "significant": significant,
    }).sort_values("original_index").reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# Deflated Sharpe Ratio
# ---------------------------------------------------------------------------

def deflated_sharpe_ratio(
    sharpe_ratio: float,
    n_trials: int,
    n_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """Compute the Deflated Sharpe Ratio (DSR).

    The DSR adjusts the observed Sharpe for the selection bias introduced
    by evaluating multiple strategies / parameter combinations.  It
    estimates the probability that the true Sharpe is positive.

    Formula (Bailey & Lopez de Prado, 2014):
        SR* = E[max SR over n_trials trials from standard normal]
        DSR = Phi( (SR_obs - SR*) * sqrt(N-1) / sqrt(1 - skew*SR + (kurt-1)/4 * SR^2) )

    Args:
        sharpe_ratio: Observed annualised Sharpe ratio.
        n_trials: Number of independent strategy trials tested.
        n_observations: Number of return observations.
        skewness: Skewness of the return distribution.
        kurtosis: Kurtosis of the return distribution (3 = normal).

    Returns:
        DSR in [0, 1]: probability the strategy has a true positive Sharpe.
    """
    if n_trials <= 0 or n_observations <= 1:
        return 0.0

    # Expected maximum Sharpe under repeated testing (standard normal)
    euler_mascheroni = 0.5772156649
    v = math.sqrt(2 * math.log(n_trials)) - (
        math.log(math.log(n_trials)) + math.log(4 * math.pi)
    ) / (2 * math.sqrt(2 * math.log(n_trials)))
    sr_star = v + euler_mascheroni / math.sqrt(2 * math.log(n_trials))

    # Variance correction for non-normal returns
    variance_correction = math.sqrt(
        max(
            1e-8,
            (1 - skewness * sharpe_ratio + (kurtosis - 1) / 4 * sharpe_ratio ** 2)
            / (n_observations - 1),
        )
    )

    z = (sharpe_ratio - sr_star) / variance_correction
    return float(stats.norm.cdf(z))


# ---------------------------------------------------------------------------
# Probability of Backtest Overfitting (PBO)
# ---------------------------------------------------------------------------

def probability_of_backtest_overfitting(
    fold_sharpes: list[float],
) -> float:
    """Estimate PBO from per-fold Sharpe ratios.

    PBO measures the fraction of CPCV path combinations where the in-sample
    best strategy degrades to below-median performance out-of-sample.

    This simplified implementation uses the rank-correlation approach:
    it computes what fraction of fold permutations see the best in-sample
    fold rank below the median out-of-sample.

    Args:
        fold_sharpes: List of per-fold Sharpe ratios (in chronological order).

    Returns:
        PBO estimate in [0, 1].  PBO > 0.5 suggests overfitting.
    """
    n = len(fold_sharpes)
    if n < 2:
        return 0.0

    sharpes = np.array(fold_sharpes, dtype=float)
    # Treat first half as in-sample, second half as out-of-sample
    split = n // 2
    in_sample = sharpes[:split]
    out_sample = sharpes[split:]

    if len(in_sample) == 0 or len(out_sample) == 0:
        return 0.0

    best_is_idx = int(np.argmax(in_sample))
    # Check if this fold's out-of-sample rank is below median
    if best_is_idx >= len(out_sample):
        oos_sharpe = np.nan
    else:
        oos_sharpe = out_sample[best_is_idx]

    if np.isnan(oos_sharpe):
        return 0.0

    median_oos = float(np.median(out_sample))
    return 1.0 if oos_sharpe < median_oos else 0.0


# ---------------------------------------------------------------------------
# Full statistics report
# ---------------------------------------------------------------------------

def compute_statistics_report(
    trades: pd.DataFrame,
    fold_sharpes: list[float] | None = None,
    n_trials: int = 1,
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
) -> dict[str, object]:
    """Compute the full statistical report for a backtest.

    Args:
        trades: Backtest trades DataFrame.
        fold_sharpes: Per-fold Sharpe ratios (for PBO/DSR).
        n_trials: Number of strategies tried (for DSR inflation).
        alpha: Significance level for hypothesis tests.
        n_bootstrap: Bootstrap samples for CI calculations.

    Returns:
        Dictionary with all statistical test results.
    """
    from cuic_quant.metrics import calculate_sharpe_ratio

    report: dict[str, object] = {}

    # Binomial test
    report["binomial_test"] = binomial_test(trades, alpha=alpha)

    # Bootstrap CI on total P&L
    if "pnl" in trades.columns and len(trades) > 0:
        pnl_mean = lambda s: float(s.mean())  # noqa: E731
        report["pnl_bootstrap_ci"] = bootstrap_ci(
            trades["pnl"], pnl_mean, n_bootstrap=n_bootstrap
        )

    # Sharpe ratio
    if "pnl" in trades.columns:
        sr = calculate_sharpe_ratio(trades["pnl"])
        report["sharpe_ratio"] = sr

        # DSR
        if fold_sharpes and n_trials > 0:
            pnl_series = pd.to_numeric(trades["pnl"], errors="coerce").dropna()
            sk = float(pnl_series.skew()) if len(pnl_series) > 2 else 0.0
            kurt = float(pnl_series.kurtosis() + 3) if len(pnl_series) > 3 else 3.0
            report["deflated_sharpe_ratio"] = deflated_sharpe_ratio(
                sr, n_trials, len(pnl_series), sk, kurt
            )

    # PBO
    if fold_sharpes:
        report["pbo"] = probability_of_backtest_overfitting(fold_sharpes)

    return report
