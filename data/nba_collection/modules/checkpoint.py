"""Checkpoint system for resumable NBA data collection."""

from __future__ import annotations

import json
from pathlib import Path


class Checkpoint:
    """Track collection progress for resume capability.

    Persists state to a JSON file so long-running collection
    can be interrupted and resumed without re-collecting data.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.last_update: str | None = None
        self.seasons_completed: list[str] = []
        self.games_collected: dict[str, list[str]] = {}
        self.total_api_calls: int = 0
        self.errors: list[str] = []

        if self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text())
        self.last_update = data.get("last_update")
        self.seasons_completed = data.get("seasons_completed", [])
        self.games_collected = data.get("games_collected", {})
        self.total_api_calls = data.get("total_api_calls", 0)
        self.errors = data.get("errors", [])

    def save(self) -> None:
        """Persist current state to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_update": self.last_update,
            "seasons_completed": self.seasons_completed,
            "games_collected": self.games_collected,
            "total_api_calls": self.total_api_calls,
            "errors": self.errors,
        }
        self.path.write_text(json.dumps(data, indent=2))

    def mark_season_completed(self, season: str) -> None:
        if season not in self.seasons_completed:
            self.seasons_completed.append(season)

    def is_season_completed(self, season: str) -> bool:
        return season in self.seasons_completed

    def mark_game_collected(self, category: str, game_id: str) -> None:
        if category not in self.games_collected:
            self.games_collected[category] = []
        if game_id not in self.games_collected[category]:
            self.games_collected[category].append(game_id)

    def is_game_collected(self, category: str, game_id: str) -> bool:
        return game_id in self.games_collected.get(category, [])

    def increment_api_calls(self, count: int = 1) -> None:
        self.total_api_calls += count

    def add_error(self, error: str) -> None:
        self.errors.append(error)
