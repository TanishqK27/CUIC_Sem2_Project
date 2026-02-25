"""NBA constants: team abbreviations, seasons, and configuration."""

from __future__ import annotations

SEASONS: list[str] = ["2021-22", "2022-23", "2023-24", "2024-25"]

CURRENT_SEASON: str = "2024-25"

REQUEST_DELAY: float = 1.0  # seconds between API calls

MAX_RETRIES: int = 3

STANDARD_TEAM_ABBRS: list[str] = [
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
]

# Map historical/variant abbreviations to the project standard
TEAM_ABBR_MAP: dict[str, str] = {
    "NJN": "BKN",   # New Jersey Nets -> Brooklyn Nets
    "CHO": "CHA",   # Charlotte (alt) -> Charlotte Hornets
    "CHH": "CHA",   # Charlotte Hornets (old)
    "NOH": "NOP",   # New Orleans Hornets -> Pelicans
    "NOK": "NOP",   # New Orleans/Oklahoma City Hornets
    "SEA": "OKC",   # Seattle SuperSonics -> OKC Thunder
    "PHO": "PHX",   # Phoenix (alt)
    "GS": "GSW",    # Golden State (2-letter)
    "SA": "SAS",    # San Antonio (2-letter)
    "NY": "NYK",    # New York (2-letter)
    "NO": "NOP",    # New Orleans (2-letter)
}

# CSV file names and their primary keys
CSV_CONFIG: dict[str, dict] = {
    "nba_games": {"file": "nba_games.csv", "pk": ["game_id"]},
    "nba_game_boxscores_team": {"file": "nba_game_boxscores_team.csv", "pk": ["game_id", "team_id", "period"]},
    "nba_game_boxscores_player": {"file": "nba_game_boxscores_player.csv", "pk": ["game_id", "player_id", "period"]},
    "nba_game_advanced_player": {"file": "nba_game_advanced_player.csv", "pk": ["game_id", "player_id", "period"]},
    "nba_game_hustle_player": {"file": "nba_game_hustle_player.csv", "pk": ["game_id", "player_id"]},
    "nba_game_tracking_player": {"file": "nba_game_tracking_player.csv", "pk": ["game_id", "player_id"]},
    "nba_team_stats": {"file": "nba_team_stats.csv", "pk": ["team_id", "season"]},
    "nba_player_stats": {"file": "nba_player_stats.csv", "pk": ["player_id", "season"]},
    "nba_rosters": {"file": "nba_rosters.csv", "pk": ["player_id", "team_id", "season"]},
    "nba_players": {"file": "nba_players.csv", "pk": ["player_id"]},
    "nba_teams": {"file": "nba_teams.csv", "pk": ["team_id"]},
    "nba_injuries": {"file": "nba_injuries.csv", "pk": ["player_id", "date"]},
    "nba_standings": {"file": "nba_standings.csv", "pk": ["team_id", "season"]},
}


def standardize_team_abbr(abbr: str) -> str:
    """Normalize a team abbreviation to the project standard.

    Args:
        abbr: Team abbreviation from any source.

    Returns:
        Standardized 3-letter abbreviation.

    Raises:
        ValueError: If abbreviation is not recognized.
    """
    if abbr in STANDARD_TEAM_ABBRS:
        return abbr
    if abbr in TEAM_ABBR_MAP:
        return TEAM_ABBR_MAP[abbr]
    raise ValueError(f"Unknown team abbreviation: {abbr}")
