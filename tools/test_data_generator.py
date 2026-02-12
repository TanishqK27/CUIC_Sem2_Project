from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd


COLUMNS = [
    "timestamp",
    "game",
    "home_team",
    "away_team",
    "home_odds",
    "away_odds",
    "home_win",
]

NBA_TEAMS = [
    "Atlanta Hawks",
    "Boston Celtics",
    "Brooklyn Nets",
    "Charlotte Hornets",
    "Chicago Bulls",
    "Cleveland Cavaliers",
    "Dallas Mavericks",
    "Denver Nuggets",
    "Detroit Pistons",
    "Golden State Warriors",
    "Houston Rockets",
    "Indiana Pacers",
    "LA Clippers",
    "Los Angeles Lakers",
    "Memphis Grizzlies",
    "Miami Heat",
    "Milwaukee Bucks",
    "Minnesota Timberwolves",
    "New Orleans Pelicans",
    "New York Knicks",
    "Oklahoma City Thunder",
    "Orlando Magic",
    "Philadelphia 76ers",
    "Phoenix Suns",
    "Portland Trail Blazers",
    "Sacramento Kings",
    "San Antonio Spurs",
    "Toronto Raptors",
    "Utah Jazz",
    "Washington Wizards",
]


def _build_row(
    timestamp: datetime,
    home_team: str,
    away_team: str,
    home_win: int,
    rng: np.random.Generator,
) -> Dict[str, object]:
    winner_odds = rng.uniform(1.5, 2.6)
    loser_odds = min(winner_odds + rng.uniform(0.05, 0.8), 3.0)

    if home_win == 1:
        home_odds = winner_odds
        away_odds = loser_odds
    else:
        home_odds = loser_odds
        away_odds = winner_odds

    return {
        "timestamp": timestamp,
        "game": f"{home_team} vs {away_team}",
        "home_team": home_team,
        "away_team": away_team,
        "home_odds": round(home_odds, 3),
        "away_odds": round(away_odds, 3),
        "home_win": home_win,
    }


def generate_test_data(
    n_games: int = 100,
    start_date: str = "2026-01-01",
    home_win_rate: float = 0.55,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start_dt = datetime.fromisoformat(start_date)

    rows = []
    for i in range(n_games):
        home_team, away_team = rng.choice(NBA_TEAMS, size=2, replace=False)
        home_win = int(rng.random() < home_win_rate)
        timestamp = start_dt + timedelta(minutes=i)

        rows.append(_build_row(timestamp, home_team, away_team, home_win, rng))

    return pd.DataFrame(rows, columns=COLUMNS)


def generate_perfect_test(n_games: int = 20) -> pd.DataFrame:
    start_dt = datetime.fromisoformat("2026-01-01")
    rows = []

    for i in range(n_games):
        home_team = NBA_TEAMS[i % len(NBA_TEAMS)]
        away_team = NBA_TEAMS[(i + 1) % len(NBA_TEAMS)]
        home_win = 1 if i % 2 == 0 else 0
        timestamp = start_dt + timedelta(minutes=i)

        rows.append(
            {
                "timestamp": timestamp,
                "game": f"{home_team} vs {away_team}",
                "home_team": home_team,
                "away_team": away_team,
                "home_odds": 2.0,
                "away_odds": 2.0,
                "home_win": home_win,
            }
        )

    return pd.DataFrame(rows, columns=COLUMNS)


def generate_edge_cases() -> Dict[str, pd.DataFrame]:
    empty = pd.DataFrame(columns=COLUMNS)
    single_game = generate_test_data(n_games=1)
    all_home_wins = generate_test_data(n_games=20, home_win_rate=1.0)
    all_away_wins = generate_test_data(n_games=20, home_win_rate=0.0)

    return {
        "empty": empty,
        "single_game": single_game,
        "all_home_wins": all_home_wins,
        "all_away_wins": all_away_wins,
    }


if __name__ == "__main__":
    df = generate_test_data()
    df.to_csv("data/test_games.csv", index=False)
