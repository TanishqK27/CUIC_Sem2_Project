# Design: S4 Overfitting Protection — Full Audit + CSCV PBO + BH-FDR

**Date:** 2026-03-04
**Author:** James
**Status:** Approved — ready for implementation

---

## Problem

The `statistics.py` module has 5 S4 functions (Bonferroni, Holm-Bonferroni, DSR,
PBO, overfitting_report) with 11 tests. Three gaps:

1. **Simplified PBO:** `probability_of_backtest_overfitting` uses a single IS/OOS
   split rank test. For N strategies it's quantized to 1/(N-1) increments. The real
   algorithm (Bailey et al. 2017, CSCV) enumerates all C(S, S/2) train/test
   partitions of time-series blocks. The simplified version is barely better than a
   coin flip.

2. **No FDR correction:** Bonferroni and Holm control family-wise error rate (FWER)
   but are overly conservative for 55 strategies. Benjamini-Hochberg controls the
   false discovery rate and is standard for large hypothesis pools.

3. **No integration:** `overfitting_report` is never called. Walk-forward report
   has a manual overfitting heuristic (IS profitable + OOS negative → warning) but
   doesn't use any S4 functions. DSR in `overfitting_report` ignores skewness and
   kurtosis parameters.

---

## Decision

1. Add Benjamini-Hochberg FDR correction
2. Replace simplified PBO with proper CSCV (Bailey et al. 2017)
3. Wire BH into `overfitting_report`, add skewness/kurtosis passthrough to DSR
4. Add 9 known-value tests

---

## Design

### New Function: `benjamini_hochberg_correction`

```python
def benjamini_hochberg_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[bool]:
    """Benjamini-Hochberg FDR correction.

    Controls false discovery rate (expected proportion of false positives
    among rejections) rather than family-wise error rate. More powerful
    than Bonferroni/Holm for large strategy pools.

    Algorithm:
      1. Sort p-values ascending
      2. For rank i (1-indexed), threshold = i/n * alpha
      3. Find largest k where p[k] <= k/n * alpha
      4. Reject all hypotheses with rank <= k
    """
    n = len(p_values)
    if n == 0:
        return []

    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    significant = [False] * n

    # Find largest k where p[k] <= (k/n) * alpha
    max_k = -1
    for rank_0, (orig_idx, p) in enumerate(indexed):
        rank_1 = rank_0 + 1  # 1-indexed
        if p <= (rank_1 / n) * alpha:
            max_k = rank_0

    # Reject all with rank <= max_k
    for rank_0, (orig_idx, p) in enumerate(indexed):
        if rank_0 <= max_k:
            significant[orig_idx] = True

    return significant
```

### Upgraded Function: `probability_of_backtest_overfitting` (CSCV)

```python
def probability_of_backtest_overfitting(
    returns_matrix: np.ndarray,
    n_groups: int = 16,
) -> dict[str, Any]:
    """Probability of Backtest Overfitting via CSCV (Bailey et al. 2017).

    Combinatorial Symmetric Cross-Validation: partition time series into
    S equal groups, enumerate all C(S, S/2) train/test splits, check
    how often the IS-optimal strategy underperforms OOS.

    Args:
        returns_matrix: 2D array (n_periods x n_strategies). Each column
            is a strategy's return series.
        n_groups: Number of time-series groups (must be even, default 16).

    Returns:
        Dict with:
            pbo: float — probability of overfitting [0, 1]
            logit_distribution: list[float] — logit of OOS rank for each combo
            n_combinations: int — number of train/test splits tested
    """
```

Algorithm:
1. Split `returns_matrix` rows into `n_groups` equal-sized blocks
2. Generate all `C(n_groups, n_groups/2)` combinations of blocks for IS
3. For each combination:
   - IS blocks → compute Sharpe per strategy → find IS-best index
   - OOS blocks (remaining) → compute Sharpe per strategy
   - Record OOS rank of IS-best strategy (1 = best, N = worst)
   - Compute logit: `log(rank / (N + 1 - rank))`
4. PBO = fraction of combinations where logit > 0 (IS-best is below median OOS)
5. Return `{pbo, logit_distribution, n_combinations}`

**Backward compatibility:** The old signature `(sharpe_ratios_in_sample, sharpe_ratios_out_of_sample) -> float` is not called anywhere in the codebase. Replace it entirely.

### Modified: `overfitting_report`

Add to output:
- `benjamini_hochberg_significant`: list[bool]
- `n_significant_bh`: int

Add optional `skewness` and `kurtosis` keys in strategy_results dicts.
Pass these to `deflated_sharpe_ratio` when available.

### Integration: walk-forward report

No changes to `walk_forward_report` — the overfitting report is a separate
concern (multiple strategies across team members, not per-fold). Users call
`overfitting_report` directly when comparing strategies.

---

## Test Coverage

All new tests in `tests/test_audit_fixes.py`.

### TestOverfittingProtection (9 tests)

1. `test_bh_basic` — 5 p-values [0.001, 0.01, 0.03, 0.04, 0.80], alpha=0.05: first 4 rejected
2. `test_bh_vs_bonferroni` — BH rejects >= Bonferroni (more powerful)
3. `test_bh_all_significant` — all small p-values → all rejected
4. `test_pbo_cscv_no_overfitting` — strategies where IS-best is also OOS-best → PBO near 0
5. `test_pbo_cscv_complete_overfitting` — IS-best is OOS-worst → PBO near 1
6. `test_pbo_cscv_known_value` — 4 groups, C(4,2)=6 combos, verify exact PBO
7. `test_pbo_cscv_n_combinations` — n_groups=8 → C(8,4)=70 combinations
8. `test_overfitting_report_with_bh` — BH results in report output
9. `test_overfitting_report_skewness_kurtosis` — DSR uses provided skew/kurt

---

## Files Changed

| File | Change |
|---|---|
| `src/cuic_quant/backtest/statistics.py` | Add BH-FDR, replace PBO with CSCV, update overfitting_report |
| `tests/test_audit_fixes.py` | `TestOverfittingProtection` (9 tests) |

---

## Out of Scope

- Changing walk_forward_report (overfitting report is separate concern)
- Adding permutation-based FDR (BH is sufficient)
- Full deflation adjustment for non-IID returns (YAGNI)

---

## References

- Bailey, Borwein, Lopez de Prado, Zhu (2017): "The Probability of Backtest Overfitting"
- Benjamini & Hochberg (1995): "Controlling the False Discovery Rate"
- Bailey & Lopez de Prado (2014): "The Deflated Sharpe Ratio"
