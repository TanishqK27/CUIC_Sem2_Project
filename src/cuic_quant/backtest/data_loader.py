"""Data loader for NBA backtesting.

Loads and aligns NBA game data, pre-game features, and odds into the
X (features), Y (outcomes), O (odds) format used by the backtest engine.

If pre-built CSVs are not found, a synthetic dataset is generated so the
backtester can still run end-to-end for demonstration purposes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name constants
# ---------------------------------------------------------------------------
GAME_DATE_COL = "game_date"
GAME_ID_COL = "game_id"
HOME_TEAM_COL = "home_team_id"
AWAY_TEAM_COL = "away_team_id"
HOME_WIN_COL = "home_win"          # 1 = home won, 0 = away won
HOME_ODDS_COL = "home_odds"        # decimal odds for home win
AWAY_ODDS_COL = "away_odds"        # decimal odds for away win


class BacktestDataset(NamedTuple):
    """Container for the three aligned matrices used by the backtest engine.

    Attributes:
        X: Feature matrix (n_games x n_features). Index = game_id.
        Y: Outcome series (n_games,). Values: 1 = home win, 0 = away win.
        O: Odds DataFrame (n_games x 2). Columns: home_odds, away_odds.
        dates: DatetimeIndex aligned with X/Y/O rows.
    """

    X: pd.DataFrame
    Y: pd.Series
    O: pd.DataFrame
    dates: pd.DatetimeIndex


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------

def load_nba_dataset(
    data_dir: str | Path = "data/nba_collection",
    processed_dir: str | Path | None = None,
    odds_path: str | Path | None = None,
    min_games: int = 50,
    real_odds_only: bool = False,
) -> BacktestDataset:
    """Load NBA data into X/Y/O format for backtesting.

    Tries to load from pre-built CSVs first.  If the required files are
    missing or contain fewer than ``min_games`` rows the function falls back
    to a deterministic synthetic dataset so the backtester can still run.

    Args:
        data_dir: Root directory of the raw nba_collection data.
        processed_dir: Directory for processed/feature CSVs.  Defaults to
            ``data_dir / "processed"``.
        odds_path: Path to game_odds.csv (game_id, home_odds, away_odds).
            Defaults to ``data/odds/game_odds.csv``.
        min_games: Minimum number of games required before falling back to
            synthetic data.
        real_odds_only: If True, only return games that have real bookmaker
            odds (filters out games with synthetic 1.91/1.91 odds).

    Returns:
        BacktestDataset with aligned X, Y, O and dates.
    """
    data_dir = Path(data_dir)
    processed_dir = Path(processed_dir) if processed_dir else data_dir.parent / "processed"
    odds_path = Path(odds_path) if odds_path else Path("data/odds/game_odds.csv")

    dataset = _try_load_real(data_dir, processed_dir, min_games)
    if dataset is not None:
        dataset = _merge_real_odds(dataset, odds_path, real_odds_only)
        logger.info("Loaded real NBA dataset: %d games", len(dataset.X))
        return dataset

    logger.warning(
        "Real NBA data not found or too small — using synthetic dataset."
    )
    return _generate_synthetic(n_games=500, seed=42)


# ---------------------------------------------------------------------------
# Real data loading
# ---------------------------------------------------------------------------

def _merge_real_odds(
    dataset: BacktestDataset,
    odds_path: Path,
    real_odds_only: bool,
) -> BacktestDataset:
    """Merge real bookmaker odds into a dataset, falling back to 1.91/1.91.

    Args:
        dataset: Existing BacktestDataset (may have synthetic odds).
        odds_path: Path to game_odds.csv with columns game_id, home_odds, away_odds.
        real_odds_only: If True, filter dataset to only games with real odds.

    Returns:
        BacktestDataset with odds updated where real data is available.
    """
    if not odds_path.exists():
        logger.info("No game_odds.csv found at %s — using synthetic odds", odds_path)
        return dataset

    try:
        real_odds = pd.read_csv(odds_path)
        real_odds["game_id"] = real_odds["game_id"].astype(str)
        real_odds = real_odds.set_index("game_id")[["home_odds", "away_odds"]]
    except Exception as exc:
        logger.warning("Failed to load game_odds.csv: %s", exc)
        return dataset

    # Update O with real odds where available
    O = dataset.O.copy()
    O.update(real_odds)

    n_real = real_odds.index.isin(O.index).sum()
    logger.info("Merged real odds for %d / %d games", n_real, len(O))
    print(f"Real bookmaker odds loaded for {n_real} games "
          f"({n_real/len(O):.0%} of dataset)")

    if real_odds_only:
        mask = O.index.isin(real_odds.index)
        X = dataset.X.loc[mask]
        Y = dataset.Y.loc[mask]
        O = O.loc[mask]
        dates = dataset.dates[mask]
        print(f"Filtered to {len(X)} games with real odds")
        return BacktestDataset(X=X, Y=Y, O=O, dates=dates)

    return BacktestDataset(X=dataset.X, Y=dataset.Y, O=O, dates=dataset.dates)


def _try_load_real(
    data_dir: Path,
    processed_dir: Path,
    min_games: int,
) -> BacktestDataset | None:
    """Attempt to load real data; return None if files are missing/small."""
    games_path = data_dir / "nba_games.csv"
    features_path = processed_dir / "pregame_team.csv"

    if not games_path.exists():
        logger.debug("nba_games.csv not found at %s", games_path)
        return None

    try:
        games = pd.read_csv(games_path, low_memory=False)
    except Exception as exc:
        logger.warning("Failed to read nba_games.csv: %s", exc)
        return None

    # Normalise column names to lowercase
    games.columns = [c.lower().strip() for c in games.columns]

    # Identify home-win column — common names used by NBA API wrappers
    home_win_candidates = ["home_win", "wl_home", "home_team_win"]
    outcome_col = next((c for c in home_win_candidates if c in games.columns), None)

    if outcome_col is None:
        # Try to derive from pts columns
        if "pts_home" in games.columns and "pts_away" in games.columns:
            games["home_win"] = (games["pts_home"] > games["pts_away"]).astype(int)
            outcome_col = "home_win"
        elif "home_pts" in games.columns and "away_pts" in games.columns:
            games["home_win"] = (games["home_pts"] > games["away_pts"]).astype(int)
            outcome_col = "home_win"
        else:
            logger.warning("Cannot determine game outcomes from nba_games.csv columns: %s", list(games.columns))
            return None

    # Normalise outcome to int
    games[HOME_WIN_COL] = pd.to_numeric(games[outcome_col], errors="coerce")
    games = games.dropna(subset=[HOME_WIN_COL])
    games[HOME_WIN_COL] = games[HOME_WIN_COL].astype(int).clip(0, 1)

    # Date column
    date_col = next((c for c in ["game_date", "date", "game_date_est"] if c in games.columns), None)
    if date_col is None:
        logger.warning("No date column found in nba_games.csv")
        return None

    games[GAME_DATE_COL] = pd.to_datetime(games[date_col], errors="coerce")
    games = games.dropna(subset=[GAME_DATE_COL]).sort_values(GAME_DATE_COL)

    if len(games) < min_games:
        logger.warning("Only %d games found (need %d)", len(games), min_games)
        return None

    # Game ID
    game_id_col = next((c for c in ["game_id", "gameid", "id"] if c in games.columns), None)
    if game_id_col:
        games[GAME_ID_COL] = games[game_id_col].astype(str)
    else:
        games[GAME_ID_COL] = [f"G{i:05d}" for i in range(len(games))]

    games = games.set_index(GAME_ID_COL)

    # Odds: look for odds columns or use implied 50/50
    home_odds_col = next((c for c in ["home_odds", "home_ml", "home_moneyline"] if c in games.columns), None)
    away_odds_col = next((c for c in ["away_odds", "away_ml", "away_moneyline"] if c in games.columns), None)

    if home_odds_col and away_odds_col:
        O = games[[home_odds_col, away_odds_col]].copy()
        O.columns = [HOME_ODDS_COL, AWAY_ODDS_COL]
        O = O.apply(pd.to_numeric, errors="coerce")
    else:
        # No odds available — synthesise ~2.0 odds with slight vig
        logger.info("No odds columns found; using synthetic ~2.0 odds with vig")
        O = pd.DataFrame(
            {"home_odds": 1.91, "away_odds": 1.91},
            index=games.index,
        )

    # Features: try pregame_team.csv, then rolling stats, then fallback
    X = _load_features(features_path, games)

    Y = games[HOME_WIN_COL].rename("home_win")
    dates = pd.DatetimeIndex(games[GAME_DATE_COL])

    return BacktestDataset(X=X, Y=Y, O=O, dates=dates)


def _load_features(features_path: Path, games: pd.DataFrame) -> pd.DataFrame:
    """Load pregame features, or fall back to basic team-stats features."""
    if features_path.exists():
        try:
            feats = pd.read_csv(features_path, low_memory=False)
            feats.columns = [c.lower().strip() for c in feats.columns]
            game_id_col = next(
                (c for c in ["game_id", "gameid"] if c in feats.columns), None
            )
            if game_id_col:
                feats = feats.set_index(game_id_col)
                feats.index = feats.index.astype(str)
                # Keep only numeric feature columns, aligned to games index
                numeric_feats = feats.select_dtypes(include="number")
                aligned = numeric_feats.reindex(games.index).fillna(0.0)
                if not aligned.empty:
                    return aligned
        except Exception as exc:
            logger.warning("Failed to load pregame features: %s", exc)

    # Fallback: compute rolling pre-game features from past results.
    # All stats are lagged so no game knows its own outcome (no lookahead).
    rolling = _build_rolling_features(games)
    if not rolling.empty:
        return rolling

    # Last resort: constant feature
    return pd.DataFrame({"const": 1.0}, index=games.index)


def _build_rolling_features(games: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Compute rolling pre-game features from historical game stats.

    All features are computed from *past* games only (shifted by 1) so the
    model never sees information from the game it is predicting.

    Features per game:
        home_win_rate_N, away_win_rate_N      rolling win rate (last N games)
        home_pts_avg_N,  away_pts_avg_N       rolling avg points scored
        home_pts_con_N,  away_pts_con_N       rolling avg points conceded
        home_rest_days,  away_rest_days        days since last game (capped 7)
        home_is_b2b,     away_is_b2b           1 if playing on consecutive days

    Args:
        games: Games DataFrame (index=game_id, must include game_date,
               home_team_id, away_team_id, home_score, away_score, home_win).
        window: Rolling window size in games.

    Returns:
        Feature DataFrame aligned to games.index, or empty DataFrame if
        the required columns are missing.
    """
    required = {"game_date", "home_team_id", "away_team_id", "home_win"}
    has_scores = {"home_score", "away_score"}.issubset(games.columns)
    if not required.issubset(games.columns):
        return pd.DataFrame()

    g = games.copy().reset_index()  # game_id back as column
    g["game_date"] = pd.to_datetime(g["game_date"])
    g = g.sort_values("game_date").reset_index(drop=True)

    # Build a per-team game log (one row per team per game)
    home_log = g[["game_id", "game_date", "home_team_id", "home_win"]].copy()
    home_log.columns = ["game_id", "game_date", "team_id", "win"]
    if has_scores:
        home_log["pts_for"] = g["home_score"]
        home_log["pts_against"] = g["away_score"]

    away_log = g[["game_id", "game_date", "away_team_id", "home_win"]].copy()
    away_log.columns = ["game_id", "game_date", "team_id", "win"]
    away_log["win"] = 1 - away_log["win"]  # away win = home_win flipped
    if has_scores:
        away_log["pts_for"] = g["away_score"]
        away_log["pts_against"] = g["home_score"]

    team_log = pd.concat([home_log, away_log], ignore_index=True)
    team_log = team_log.sort_values(["team_id", "game_date"]).reset_index(drop=True)

    # Rolling stats (shift 1 so current game is excluded)
    grp = team_log.groupby("team_id")
    team_log[f"roll_win_{window}"] = (
        grp["win"].transform(lambda s: s.shift(1).rolling(window, min_periods=3).mean())
    )
    if has_scores:
        team_log[f"roll_pts_for_{window}"] = (
            grp["pts_for"].transform(lambda s: s.shift(1).rolling(window, min_periods=3).mean())
        )
        team_log[f"roll_pts_con_{window}"] = (
            grp["pts_against"].transform(lambda s: s.shift(1).rolling(window, min_periods=3).mean())
        )

    # Rest days (days since previous game, capped at 7)
    team_log["prev_date"] = grp["game_date"].transform(lambda s: s.shift(1))
    team_log["rest_days"] = (
        (team_log["game_date"] - team_log["prev_date"]).dt.days.clip(upper=7).fillna(7)
    )
    team_log["is_b2b"] = (team_log["rest_days"] == 1).astype(int)

    # Keep only the columns we want to pivot
    stat_cols = [f"roll_win_{window}", "rest_days", "is_b2b"]
    if has_scores:
        stat_cols += [f"roll_pts_for_{window}", f"roll_pts_con_{window}"]

    team_stats = team_log[["game_id", "team_id"] + stat_cols].copy()

    # Join home and away stats back to the game table
    home_stats = (
        g[["game_id", "home_team_id"]]
        .merge(team_stats, left_on=["game_id", "home_team_id"], right_on=["game_id", "team_id"], how="left")
        .drop(columns=["team_id", "home_team_id"])
        .rename(columns={c: f"home_{c}" for c in stat_cols})
        .set_index("game_id")
    )
    away_stats = (
        g[["game_id", "away_team_id"]]
        .merge(team_stats, left_on=["game_id", "away_team_id"], right_on=["game_id", "team_id"], how="left")
        .drop(columns=["team_id", "away_team_id"])
        .rename(columns={c: f"away_{c}" for c in stat_cols})
        .set_index("game_id")
    )

    features = pd.concat([home_stats, away_stats], axis=1)
    features.index = features.index.astype(str)

    # Align to original games index and fill early NaNs with league average
    aligned = features.reindex(games.index)
    aligned = aligned.fillna(aligned.mean())
    return aligned.astype(float)


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def _generate_synthetic(n_games: int = 500, seed: int = 42) -> BacktestDataset:
    """Generate a reproducible synthetic NBA-style dataset.

    The synthetic data has a mild built-in home-court edge (~55% home win
    rate) so that a strategy with correct edge will show profit.

    Args:
        n_games: Number of synthetic games.
        seed: Random seed for reproducibility.

    Returns:
        BacktestDataset ready for backtesting.
    """
    rng = np.random.default_rng(seed)

    # Dates: one game per day starting 2023-10-01
    start = pd.Timestamp("2023-10-01")
    dates = pd.DatetimeIndex(
        [start + pd.Timedelta(days=i) for i in range(n_games)]
    )

    game_ids = [f"SYN{i:05d}" for i in range(n_games)]

    # Home win probability: varies slightly per game around 0.55
    true_home_p = rng.normal(0.55, 0.05, n_games).clip(0.35, 0.75)
    outcomes = (rng.random(n_games) < true_home_p).astype(int)

    # Odds with vig: bookmaker slightly underestimates true prob
    bookie_home_p = true_home_p - rng.normal(0.02, 0.01, n_games)  # slight edge to us
    bookie_home_p = bookie_home_p.clip(0.3, 0.7)
    bookie_away_p = 1 - bookie_home_p

    # Add vig (~4.5%): divide true prob by (1 + vig)
    vig = 0.045
    home_odds = (1.0 / (bookie_home_p * (1 + vig))).clip(1.1, 5.0).round(2)
    away_odds = (1.0 / (bookie_away_p * (1 + vig))).clip(1.1, 5.0).round(2)

    # Features: 10 predictive + 5 noise
    team_strength = rng.normal(0, 1, (n_games, 5))
    noise_feats = rng.normal(0, 1, (n_games, 5))

    # Make features partially predictive of home win
    for i in range(5):
        team_strength[:, i] += (true_home_p - 0.5) * rng.uniform(1, 3)

    feature_names = (
        [f"home_roll5_pts_{i}" for i in range(3)]
        + [f"away_roll5_pts_{i}" for i in range(2)]
        + [f"noise_{i}" for i in range(5)]
    )
    X_data = np.hstack([team_strength, noise_feats])

    X = pd.DataFrame(X_data, index=game_ids, columns=feature_names)
    Y = pd.Series(outcomes, index=game_ids, name="home_win")
    O = pd.DataFrame(
        {"home_odds": home_odds, "away_odds": away_odds}, index=game_ids
    )

    return BacktestDataset(X=X, Y=Y, O=O, dates=dates)
