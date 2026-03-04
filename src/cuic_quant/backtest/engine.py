"""Core backtesting engine.

Implements the sports-betting framework pattern:
  - Strategy interface (pluggable classifiers / rule-based)
  - Value bet selection: bet when model P > implied P from odds
  - Kelly criterion position sizing
  - Transaction cost deduction per trade
  - 11-column output DataFrame for downstream analysis

The engine is intentionally stateless: given (X, Y, O, train_idx, test_idx)
it returns a trades DataFrame.  Walk-forward orchestration lives in
``walk_forward.py``.

References:
    - georgedouzas/sports-betting framework
    - Kelly (1956), "A New Interpretation of Information Rate"
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class BettingStrategy(ABC):
    """Abstract base for all betting strategies.

    Subclasses must implement ``fit`` and ``predict_proba``.  The engine
    calls ``fit`` on the training set and ``predict_proba`` on the test set
    to obtain P(home_win) for each game.
    """

    @abstractmethod
    def fit(self, X: pd.DataFrame, Y: pd.Series) -> "BettingStrategy":
        """Train the strategy on historical data.

        Args:
            X: Feature matrix (n_train x n_features).
            Y: Outcome series (1 = home win, 0 = away win).

        Returns:
            self
        """

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict P(home_win) for each row.

        Args:
            X: Feature matrix (n_test x n_features).

        Returns:
            1-D array of probabilities in [0, 1].
        """

    def get_params(self) -> dict[str, Any]:
        """Return strategy hyperparameters for logging."""
        return {}


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------


class LogisticRegressionStrategy(BettingStrategy):
    """Logistic regression classifier wrapped as a BettingStrategy.

    Args:
        C: Inverse regularisation strength (sklearn convention).
        max_iter: Maximum number of solver iterations.
        kwargs: Additional kwargs forwarded to LogisticRegression.
    """

    def __init__(self, C: float = 1.0, max_iter: int = 1000, **kwargs: Any) -> None:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        self._pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(C=C, max_iter=max_iter, **kwargs)),
            ]
        )
        self._C = C
        self._max_iter = max_iter

    def fit(self, X: pd.DataFrame, Y: pd.Series) -> "LogisticRegressionStrategy":
        self._pipeline.fit(X, Y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        proba = self._pipeline.predict_proba(X)
        # Column 1 = P(class=1) = P(home_win)
        return proba[:, 1]

    def get_params(self) -> dict[str, Any]:
        return {"C": self._C, "max_iter": self._max_iter}


class RandomForestStrategy(BettingStrategy):
    """Random forest classifier wrapped as a BettingStrategy.

    Args:
        n_estimators: Number of trees.
        max_depth: Maximum tree depth.
        kwargs: Additional kwargs forwarded to RandomForestClassifier.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = 5,
        **kwargs: Any,
    ) -> None:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        self._pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    random_state=42,
                    **kwargs,
                )),
            ]
        )
        self._n_estimators = n_estimators
        self._max_depth = max_depth

    def fit(self, X: pd.DataFrame, Y: pd.Series) -> "RandomForestStrategy":
        self._pipeline.fit(X, Y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        proba = self._pipeline.predict_proba(X)
        return proba[:, 1]

    def get_params(self) -> dict[str, Any]:
        return {"n_estimators": self._n_estimators, "max_depth": self._max_depth}


class HomeAdvantageBaseline(BettingStrategy):
    """Naive baseline: always predict historical home-win rate.

    Useful as a sanity-check benchmark.  A good model should beat this.
    """

    def __init__(self) -> None:
        self._home_win_rate: float = 0.55

    def fit(self, X: pd.DataFrame, Y: pd.Series) -> "HomeAdvantageBaseline":
        n_wins = int(Y.sum())
        if len(Y) > 0:
            self._home_win_rate = n_wins / len(Y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self._home_win_rate)

    def get_params(self) -> dict[str, Any]:
        return {"home_win_rate": self._home_win_rate}


class ValueBetBaseline(BettingStrategy):
    """Bet on whichever side has implied probability below a threshold.

    This is a rule-based strategy that bets on over-priced favourites —
    useful as a simple reference strategy.

    Args:
        implied_prob_threshold: Bet when implied P < threshold (default 0.5,
            i.e. bet on any side the market prices below fair coin flip).
    """

    def __init__(self, implied_prob_threshold: float = 0.52) -> None:
        self._threshold = implied_prob_threshold

    def fit(self, X: pd.DataFrame, Y: pd.Series) -> "ValueBetBaseline":
        return self  # stateless

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        # Return 0.52 for all games — engine will compare vs implied P
        return np.full(len(X), self._threshold)

    def get_params(self) -> dict[str, Any]:
        return {"implied_prob_threshold": self._threshold}


# ---------------------------------------------------------------------------
# Transaction cost model
# ---------------------------------------------------------------------------


@dataclass
class TransactionCosts:
    """Model for per-trade transaction costs.

    Costs are deducted from raw P&L after each bet.

    Attributes:
        commission_pct: Percentage of stake charged as commission (e.g. 0.02
            for 2%).
        flat_fee: Fixed fee per bet in currency units.
        spread_pct: Bid-ask spread as percentage of stake (models the cost
            of getting filled at sub-optimal odds).
    """

    commission_pct: float = 0.0
    flat_fee: float = 0.0
    spread_pct: float = 0.0

    def total_cost(self, stake: float) -> float:
        """Calculate total transaction cost for a given stake.

        Args:
            stake: Bet size in currency units.

        Returns:
            Total cost deducted from gross P&L.
        """
        return stake * self.commission_pct + self.flat_fee + stake * self.spread_pct


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run.

    Attributes:
        initial_bankroll: Starting capital.
        kelly_fraction: Fraction of full Kelly to use (0.5 = half Kelly).
        max_bet_fraction: Hard cap on single bet as fraction of bankroll.
        min_edge: Minimum edge required to place a bet.
            Edge = model_P - implied_P.
        transaction_costs: Cost model applied to each trade.
        bet_side: Which side to bet. "value" = always bet value side,
            "home" = home only, "away" = away only.
    """

    initial_bankroll: float = 10_000.0
    kelly_fraction: float = 0.5
    max_bet_fraction: float = 0.10
    min_edge: float = 0.02
    transaction_costs: TransactionCosts = field(default_factory=TransactionCosts)
    bet_side: str = "value"  # "value" | "home" | "away"


def run_backtest(
    strategy: BettingStrategy,
    X_train: pd.DataFrame,
    Y_train: pd.Series,
    X_test: pd.DataFrame,
    Y_test: pd.Series,
    O_test: pd.DataFrame,
    config: BacktestConfig | None = None,
    dates_test: pd.DatetimeIndex | None = None,
    fold_id: int = 0,
) -> pd.DataFrame:
    """Run a single backtest fold and return a trades DataFrame.

    The engine:
    1. Fits the strategy on (X_train, Y_train).
    2. Predicts P(home_win) for X_test.
    3. For each game in the test set:
       - Computes implied probability from decimal odds (home & away).
       - Identifies value side: where model P > implied P by at least
         ``config.min_edge``.
       - Sizes the bet with Kelly criterion.
       - Deducts transaction costs.
       - Updates running bankroll and P&L.

    Args:
        strategy: Any BettingStrategy instance (will be fit in place).
        X_train: Training features.
        Y_train: Training outcomes.
        X_test: Test features.
        Y_test: Test outcomes (used for P&L calculation only, never for
            prediction — no lookahead bias).
        O_test: Test odds DataFrame with columns ``home_odds``, ``away_odds``.
        config: Backtest configuration.  Uses defaults if None.
        dates_test: Optional DatetimeIndex for test rows.
        fold_id: Fold number for multi-fold walk-forward runs.

    Returns:
        DataFrame with columns:
            game_id, date, fold, bet_side, odds, stake, model_prob,
            implied_prob, edge, outcome, pnl, bankroll, cumulative_pnl
    """
    if config is None:
        config = BacktestConfig()

    # --- fit ---
    if len(X_train) == 0:
        logger.warning("Fold %d: empty training set — skipping", fold_id)
        return _empty_trades_df()

    strategy.fit(X_train, Y_train)
    model_probs = strategy.predict_proba(X_test)  # P(home_win)

    # Align test data
    test_index = X_test.index
    y_arr = Y_test.reindex(test_index).values
    home_odds = pd.to_numeric(O_test["home_odds"].reindex(test_index), errors="coerce").values
    away_odds = pd.to_numeric(O_test["away_odds"].reindex(test_index), errors="coerce").values

    n_test = len(test_index)
    if dates_test is not None and len(dates_test) == n_test:
        date_arr = np.array(dates_test, dtype="datetime64[ns]")
    else:
        date_arr = np.array(["NaT"] * n_test, dtype="datetime64[ns]")

    # --- loop over test games ---
    bankroll = config.initial_bankroll
    cumulative_pnl = 0.0
    rows = []

    for i in range(n_test):
        game_id = test_index[i]
        date = pd.Timestamp(date_arr[i]) if date_arr[i] is not pd.NaT else pd.NaT
        actual_outcome = int(y_arr[i]) if not np.isnan(y_arr[i]) else None

        h_odds = float(home_odds[i]) if not np.isnan(home_odds[i]) else np.nan
        a_odds = float(away_odds[i]) if not np.isnan(away_odds[i]) else np.nan
        model_home_p = float(model_probs[i])

        # Skip if odds are invalid
        if np.isnan(h_odds) or np.isnan(a_odds) or h_odds <= 1.0 or a_odds <= 1.0:
            continue

        # Implied probabilities (removing vig via normalisation)
        raw_home_implied = 1.0 / h_odds
        raw_away_implied = 1.0 / a_odds
        total_implied = raw_home_implied + raw_away_implied
        home_implied = raw_home_implied / total_implied
        away_implied = raw_away_implied / total_implied

        model_away_p = 1.0 - model_home_p

        # Determine value side
        home_edge = model_home_p - home_implied
        away_edge = model_away_p - away_implied

        if config.bet_side == "home":
            bet = "home" if home_edge >= config.min_edge else None
        elif config.bet_side == "away":
            bet = "away" if away_edge >= config.min_edge else None
        else:  # "value"
            if home_edge >= config.min_edge and home_edge >= away_edge:
                bet = "home"
            elif away_edge >= config.min_edge:
                bet = "away"
            else:
                bet = None

        if bet is None:
            continue

        # Kelly sizing
        if bet == "home":
            kelly_f = calculate_kelly_fraction(
                win_probability=model_home_p,
                decimal_odds=h_odds,
                kelly_fraction=config.kelly_fraction,
                max_fraction=config.max_bet_fraction,
            )
            bet_odds = h_odds
            edge = home_edge
            won = actual_outcome == 1
            model_p = model_home_p
            implied_p = home_implied
        else:
            kelly_f = calculate_kelly_fraction(
                win_probability=model_away_p,
                decimal_odds=a_odds,
                kelly_fraction=config.kelly_fraction,
                max_fraction=config.max_bet_fraction,
            )
            bet_odds = a_odds
            edge = away_edge
            won = actual_outcome == 0
            model_p = model_away_p
            implied_p = away_implied

        if kelly_f <= 0.0:
            continue

        stake = max(0.0, bankroll * kelly_f)
        stake = min(stake, bankroll)  # can't bet more than bankroll

        # P&L
        cost = config.transaction_costs.total_cost(stake)
        if won:
            gross_pnl = stake * (bet_odds - 1.0)
            outcome_str = "WIN"
        else:
            gross_pnl = -stake
            outcome_str = "LOSS"

        net_pnl = gross_pnl - cost
        bankroll += net_pnl
        cumulative_pnl += net_pnl

        rows.append({
            "game_id": game_id,
            "date": date,
            "fold": fold_id,
            "bet_side": bet,
            "odds": round(bet_odds, 4),
            "stake": round(stake, 4),
            "model_prob": round(model_p, 6),
            "implied_prob": round(implied_p, 6),
            "edge": round(edge, 6),
            "outcome": outcome_str,
            "pnl": round(net_pnl, 4),
            "bankroll": round(bankroll, 4),
            "cumulative_pnl": round(cumulative_pnl, 4),
        })

    if not rows:
        return _empty_trades_df()

    return pd.DataFrame(rows)


def _empty_trades_df() -> pd.DataFrame:
    """Return an empty trades DataFrame with correct schema."""
    return pd.DataFrame(
        columns=[
            "game_id", "date", "fold", "bet_side", "odds", "stake",
            "model_prob", "implied_prob", "edge", "outcome", "pnl",
            "bankroll", "cumulative_pnl",
        ]
    )
