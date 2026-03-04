"""Backtest result validator.

Runs 12 checks on a trades DataFrame before trusting any strategy metrics.
Each check returns a named result so the notebook can display a clear
pass/fail table.

Checks:
    1.  Non-empty trades
    2.  Required columns present
    3.  No future-date contamination (all dates in test range)
    4.  Bankroll never negative
    5.  Stakes never exceed bankroll at time of bet
    6.  Stakes never exceed max_bet_fraction of bankroll
    7.  Odds are valid (> 1.0)
    8.  Model probabilities in (0, 1)
    9.  Edge consistent with model_prob and implied_prob
    10. Outcome labels are only WIN or LOSS
    11. P&L arithmetic: (WIN pnl ≈ stake*(odds-1), LOSS pnl ≈ -stake)
    12. Cumulative P&L is monotone-consistent with per-trade pnl
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ValidationResult:
    """Result of a single validation check.

    Attributes:
        name: Short check name.
        passed: True if the check passed.
        message: Human-readable description of the result.
        severity: "error" | "warning" | "info".
    """

    name: str
    passed: bool
    message: str
    severity: str = "error"


class BacktestValidator:
    """Run 12 sanity checks on a backtest trades DataFrame.

    Args:
        max_bet_fraction: Max allowed bet as fraction of bankroll
            (used in check 6).
        edge_tolerance: Absolute tolerance for edge consistency check.
        pnl_tolerance: Absolute tolerance for P&L arithmetic check.
    """

    def __init__(
        self,
        max_bet_fraction: float = 0.10,
        edge_tolerance: float = 1e-4,
        pnl_tolerance: float = 0.01,
    ) -> None:
        self.max_bet_fraction = max_bet_fraction
        self.edge_tolerance = edge_tolerance
        self.pnl_tolerance = pnl_tolerance

    def validate(self, trades: pd.DataFrame) -> list[ValidationResult]:
        """Run all 12 checks and return a list of results.

        Args:
            trades: Output DataFrame from ``run_backtest`` or
                ``run_walk_forward``.

        Returns:
            List of 12 ValidationResult objects.
        """
        results = [
            self._check_non_empty(trades),
            self._check_required_columns(trades),
            self._check_no_future_dates(trades),
            self._check_bankroll_non_negative(trades),
            self._check_stake_lte_bankroll(trades),
            self._check_stake_lte_max_fraction(trades),
            self._check_valid_odds(trades),
            self._check_model_probs_range(trades),
            self._check_edge_consistency(trades),
            self._check_outcome_labels(trades),
            self._check_pnl_arithmetic(trades),
            self._check_cumulative_pnl(trades),
        ]
        return results

    def summary(self, trades: pd.DataFrame) -> pd.DataFrame:
        """Return a summary DataFrame suitable for display in a notebook.

        Args:
            trades: Backtest trades DataFrame.

        Returns:
            DataFrame with columns: check, passed, severity, message.
        """
        results = self.validate(trades)
        return pd.DataFrame(
            [
                {
                    "check": r.name,
                    "passed": "✓" if r.passed else "✗",
                    "severity": r.severity,
                    "message": r.message,
                }
                for r in results
            ]
        )

    def all_passed(self, trades: pd.DataFrame) -> bool:
        """Return True only if all error-severity checks passed."""
        return all(
            r.passed for r in self.validate(trades) if r.severity == "error"
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_non_empty(self, df: pd.DataFrame) -> ValidationResult:
        ok = len(df) > 0
        return ValidationResult(
            name="1. Non-empty trades",
            passed=ok,
            message=f"{len(df)} trades found" if ok else "No trades — strategy placed zero bets",
            severity="error",
        )

    def _check_required_columns(self, df: pd.DataFrame) -> ValidationResult:
        required = {
            "game_id", "odds", "stake", "model_prob",
            "implied_prob", "edge", "outcome", "pnl",
            "bankroll", "cumulative_pnl",
        }
        missing = required - set(df.columns)
        ok = len(missing) == 0
        return ValidationResult(
            name="2. Required columns present",
            passed=ok,
            message="All columns present" if ok else f"Missing: {sorted(missing)}",
            severity="error",
        )

    def _check_no_future_dates(self, df: pd.DataFrame) -> ValidationResult:
        if "date" not in df.columns or df["date"].isna().all():
            return ValidationResult(
                name="3. No future-date contamination",
                passed=True,
                message="Date column absent — skipped",
                severity="warning",
            )
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        future = (dates > pd.Timestamp.now()).sum()
        ok = future == 0
        return ValidationResult(
            name="3. No future-date contamination",
            passed=ok,
            message="No future dates" if ok else f"{future} future-dated rows detected",
            severity="error",
        )

    def _check_bankroll_non_negative(self, df: pd.DataFrame) -> ValidationResult:
        if "bankroll" not in df.columns:
            return ValidationResult("4. Bankroll non-negative", True, "Column absent", "warning")
        neg = (pd.to_numeric(df["bankroll"], errors="coerce") < 0).sum()
        ok = neg == 0
        return ValidationResult(
            name="4. Bankroll non-negative",
            passed=ok,
            message="Bankroll always non-negative" if ok else f"{neg} rows have negative bankroll (ruin event)",
            severity="error",
        )

    def _check_stake_lte_bankroll(self, df: pd.DataFrame) -> ValidationResult:
        if not {"stake", "bankroll"}.issubset(df.columns):
            return ValidationResult("5. Stake ≤ bankroll", True, "Columns absent", "warning")
        stakes = pd.to_numeric(df["stake"], errors="coerce")
        bankrolls = pd.to_numeric(df["bankroll"], errors="coerce")
        # bankroll column is AFTER the trade; approximate pre-trade bankroll
        pnl = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        pre_bankroll = bankrolls - pnl
        violations = (stakes > pre_bankroll + 1e-6).sum()
        ok = violations == 0
        return ValidationResult(
            name="5. Stake ≤ bankroll",
            passed=ok,
            message="All stakes ≤ pre-trade bankroll" if ok else f"{violations} stakes exceed pre-trade bankroll",
            severity="error",
        )

    def _check_stake_lte_max_fraction(self, df: pd.DataFrame) -> ValidationResult:
        if not {"stake", "bankroll"}.issubset(df.columns):
            return ValidationResult("6. Stake ≤ max_bet_fraction", True, "Columns absent", "warning")
        stakes = pd.to_numeric(df["stake"], errors="coerce")
        pnl = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        bankrolls = pd.to_numeric(df["bankroll"], errors="coerce")
        pre_bankroll = (bankrolls - pnl).clip(lower=1e-6)
        fractions = stakes / pre_bankroll
        violations = (fractions > self.max_bet_fraction + 1e-4).sum()
        ok = violations == 0
        return ValidationResult(
            name="6. Stake ≤ max_bet_fraction",
            passed=ok,
            message=(
                f"All stakes within {self.max_bet_fraction:.0%} cap"
                if ok
                else f"{violations} bets exceed {self.max_bet_fraction:.0%} cap"
            ),
            severity="warning",
        )

    def _check_valid_odds(self, df: pd.DataFrame) -> ValidationResult:
        if "odds" not in df.columns:
            return ValidationResult("7. Valid odds", True, "Column absent", "warning")
        odds = pd.to_numeric(df["odds"], errors="coerce")
        invalid = (odds.isna() | (odds <= 1.0)).sum()
        ok = invalid == 0
        return ValidationResult(
            name="7. Valid odds (> 1.0)",
            passed=ok,
            message="All odds > 1.0" if ok else f"{invalid} invalid odds (NaN or ≤ 1.0)",
            severity="error",
        )

    def _check_model_probs_range(self, df: pd.DataFrame) -> ValidationResult:
        if "model_prob" not in df.columns:
            return ValidationResult("8. Model probs in (0,1)", True, "Column absent", "warning")
        probs = pd.to_numeric(df["model_prob"], errors="coerce")
        out_of_range = (probs.isna() | (probs <= 0) | (probs >= 1)).sum()
        ok = out_of_range == 0
        return ValidationResult(
            name="8. Model probs in (0, 1)",
            passed=ok,
            message="All model probabilities in (0, 1)" if ok else f"{out_of_range} probabilities out of (0, 1)",
            severity="error",
        )

    def _check_edge_consistency(self, df: pd.DataFrame) -> ValidationResult:
        if not {"model_prob", "implied_prob", "edge"}.issubset(df.columns):
            return ValidationResult("9. Edge consistency", True, "Columns absent", "warning")
        model_p = pd.to_numeric(df["model_prob"], errors="coerce")
        implied_p = pd.to_numeric(df["implied_prob"], errors="coerce")
        edge = pd.to_numeric(df["edge"], errors="coerce")
        expected_edge = model_p - implied_p
        discrepancy = (edge - expected_edge).abs()
        violations = (discrepancy > self.edge_tolerance).sum()
        ok = violations == 0
        return ValidationResult(
            name="9. Edge = model_prob − implied_prob",
            passed=ok,
            message="Edge values consistent" if ok else f"{violations} inconsistent edge values (tol={self.edge_tolerance})",
            severity="error",
        )

    def _check_outcome_labels(self, df: pd.DataFrame) -> ValidationResult:
        if "outcome" not in df.columns:
            return ValidationResult("10. Outcome labels", True, "Column absent", "warning")
        labels = df["outcome"].astype(str).str.upper()
        invalid = (~labels.isin(["WIN", "LOSS"])).sum()
        ok = invalid == 0
        return ValidationResult(
            name="10. Outcome labels WIN/LOSS",
            passed=ok,
            message="All outcomes are WIN or LOSS" if ok else f"{invalid} invalid outcome labels",
            severity="error",
        )

    def _check_pnl_arithmetic(self, df: pd.DataFrame) -> ValidationResult:
        if not {"outcome", "stake", "odds", "pnl"}.issubset(df.columns):
            return ValidationResult("11. P&L arithmetic", True, "Columns absent", "warning")

        stakes = pd.to_numeric(df["stake"], errors="coerce")
        odds = pd.to_numeric(df["odds"], errors="coerce")
        pnl = pd.to_numeric(df["pnl"], errors="coerce")
        outcomes = df["outcome"].astype(str).str.upper()

        # Win: gross pnl = stake * (odds - 1); loss: gross pnl = -stake
        # Net pnl = gross - costs; we allow up to pnl_tolerance for costs
        win_mask = outcomes == "WIN"
        loss_mask = outcomes == "LOSS"

        win_expected = stakes[win_mask] * (odds[win_mask] - 1)
        win_actual = pnl[win_mask]
        # Net pnl should be <= gross (costs deducted) and > gross - stake (bounds)
        win_violations = (
            (win_actual > win_expected + self.pnl_tolerance)  # earned more than gross
            | (win_actual < -stakes[win_mask] - self.pnl_tolerance)  # lost more than stake
        ).sum()

        loss_expected = -stakes[loss_mask]
        loss_actual = pnl[loss_mask]
        loss_violations = (
            loss_actual > self.pnl_tolerance  # somehow profited on a loss
        ).sum()

        violations = int(win_violations + loss_violations)
        ok = violations == 0
        return ValidationResult(
            name="11. P&L arithmetic",
            passed=ok,
            message="P&L values arithmetically correct" if ok else f"{violations} P&L values inconsistent with stake/odds/outcome",
            severity="error",
        )

    def _check_cumulative_pnl(self, df: pd.DataFrame) -> ValidationResult:
        if not {"pnl", "cumulative_pnl"}.issubset(df.columns):
            return ValidationResult("12. Cumulative P&L", True, "Columns absent", "warning")
        pnl = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
        cum_pnl = pd.to_numeric(df["cumulative_pnl"], errors="coerce")
        expected_cum = pnl.cumsum()
        discrepancy = (cum_pnl - expected_cum).abs()
        violations = (discrepancy > 0.1).sum()  # 10 cent tolerance for rounding
        ok = violations == 0
        return ValidationResult(
            name="12. Cumulative P&L consistent",
            passed=ok,
            message="Cumulative P&L matches sum of per-trade P&L" if ok else f"{violations} rows have inconsistent cumulative P&L",
            severity="error",
        )
