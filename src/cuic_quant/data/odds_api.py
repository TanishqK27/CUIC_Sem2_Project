"""The Odds API client for sports betting odds data.

The Odds API provides real-time and historical odds from multiple bookmakers
for various sports worldwide.

Example:
    >>> from cuic_quant.data import OddsAPIClient
    >>>
    >>> client = OddsAPIClient()  # Uses ODDS_API_KEY env var
    >>> sports = client.get_sports()
    >>> nba_odds = client.get_odds("basketball_nba")
    >>> for game in nba_odds:
    ...     print(f"{game.home_team} vs {game.away_team}")

Note:
    - Free tier: 500 requests/month
    - See https://the-odds-api.com/ for pricing
    - See docs/platforms/sports-betting-basics.md for odds fundamentals
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class Sport:
    """Represents a sport available in The Odds API."""

    key: str
    group: str
    title: str
    description: str
    active: bool
    has_outrights: bool


@dataclass
class Bookmaker:
    """Represents a bookmaker's odds for a game."""

    key: str
    title: str
    last_update: datetime
    markets: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GameOdds:
    """Represents odds for a single game/event."""

    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: list[Bookmaker] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> GameOdds:
        """Create GameOdds from API response data.

        Args:
            data: Raw API response dictionary.

        Returns:
            GameOdds instance.
        """
        bookmakers = []
        for b in data.get("bookmakers", []):
            last_update = datetime.now()
            if b.get("last_update"):
                try:
                    last_update = datetime.fromisoformat(
                        b["last_update"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            bookmakers.append(
                Bookmaker(
                    key=b.get("key", ""),
                    title=b.get("title", ""),
                    last_update=last_update,
                    markets=b.get("markets", []),
                )
            )

        commence_time = datetime.now()
        if data.get("commence_time"):
            try:
                commence_time = datetime.fromisoformat(
                    data["commence_time"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id", ""),
            sport_key=data.get("sport_key", ""),
            sport_title=data.get("sport_title", ""),
            commence_time=commence_time,
            home_team=data.get("home_team", ""),
            away_team=data.get("away_team", ""),
            bookmakers=bookmakers,
        )

    def get_best_odds(self, market: str = "h2h") -> dict[str, dict[str, float]]:
        """Get the best available odds across all bookmakers.

        Args:
            market: Market type (h2h, spreads, totals).

        Returns:
            Dict with best odds for each outcome.

        Example:
            >>> best = game.get_best_odds()
            >>> print(f"Best home: {best['home']['odds']} at {best['home']['bookmaker']}")
        """
        best: dict[str, dict[str, Any]] = {
            "home": {"odds": 0.0, "bookmaker": ""},
            "away": {"odds": 0.0, "bookmaker": ""},
        }

        for bookmaker in self.bookmakers:
            for mkt in bookmaker.markets:
                if mkt.get("key") != market:
                    continue

                for outcome in mkt.get("outcomes", []):
                    name = outcome.get("name", "")
                    price = float(outcome.get("price", 0))

                    if name == self.home_team and price > best["home"]["odds"]:
                        best["home"] = {"odds": price, "bookmaker": bookmaker.key}
                    elif name == self.away_team and price > best["away"]["odds"]:
                        best["away"] = {"odds": price, "bookmaker": bookmaker.key}

        return best


class OddsAPIClient:
    """Client for The Odds API.

    Provides access to real-time sports betting odds from multiple bookmakers.

    Args:
        api_key: API key from the-odds-api.com.

    Example:
        >>> client = OddsAPIClient()
        >>> sports = client.get_sports()
        >>> print(f"Available sports: {len(sports)}")

        >>> nba = client.get_odds("basketball_nba", markets=["h2h", "spreads"])
        >>> for game in nba:
        ...     best = game.get_best_odds()
        ...     print(f"{game.home_team}: {best['home']['odds']}")
    """

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize The Odds API client."""
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        self._session = requests.Session()
        self._requests_remaining: int | None = None
        self._requests_used: int | None = None

    @property
    def requests_remaining(self) -> int | None:
        """Get remaining API requests this month."""
        return self._requests_remaining

    @property
    def requests_used(self) -> int | None:
        """Get API requests used this month."""
        return self._requests_used

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            ValueError: If API key is not set.
            requests.HTTPError: If the request fails.
        """
        if not self.api_key:
            raise ValueError(
                "API key required. Set ODDS_API_KEY environment variable "
                "or pass api_key to constructor."
            )

        url = f"{self.BASE_URL}{endpoint}"

        request_params = {"apiKey": self.api_key}
        if params:
            request_params.update(params)

        response = self._session.get(url, params=request_params, timeout=30)

        # Track rate limits from response headers
        self._requests_remaining = int(response.headers.get("x-requests-remaining", 0))
        self._requests_used = int(response.headers.get("x-requests-used", 0))

        response.raise_for_status()

        return response.json()

    def get_sports(self, all_sports: bool = False) -> list[Sport]:
        """Get list of available sports.

        Args:
            all_sports: If True, include inactive sports.

        Returns:
            List of Sport objects.

        Example:
            >>> sports = client.get_sports()
            >>> for s in sports:
            ...     print(f"{s.key}: {s.title}")
        """
        params = {"all": "true"} if all_sports else {}
        data = self._request("/sports", params=params)

        return [
            Sport(
                key=s.get("key", ""),
                group=s.get("group", ""),
                title=s.get("title", ""),
                description=s.get("description", ""),
                active=s.get("active", False),
                has_outrights=s.get("has_outrights", False),
            )
            for s in data
        ]

    def get_odds(
        self,
        sport: str,
        regions: str = "us,uk,eu",
        markets: list[str] | None = None,
        odds_format: str = "decimal",
        bookmakers: list[str] | None = None,
    ) -> list[GameOdds]:
        """Get odds for upcoming games in a sport.

        Args:
            sport: Sport key (e.g., "basketball_nba", "soccer_epl").
            regions: Comma-separated regions for bookmakers.
            markets: Market types to include (h2h, spreads, totals).
            odds_format: Format for odds (decimal, american).
            bookmakers: Specific bookmakers to include.

        Returns:
            List of GameOdds objects.

        Example:
            >>> odds = client.get_odds(
            ...     "basketball_nba",
            ...     markets=["h2h", "spreads", "totals"],
            ... )
            >>> for game in odds:
            ...     print(f"{game.away_team} @ {game.home_team}")
        """
        params: dict[str, str] = {
            "regions": regions,
            "oddsFormat": odds_format,
        }

        if markets:
            params["markets"] = ",".join(markets)
        else:
            params["markets"] = "h2h"

        if bookmakers:
            params["bookmakers"] = ",".join(bookmakers)

        data = self._request(f"/sports/{sport}/odds", params=params)

        return [GameOdds.from_api_response(game) for game in data]

    def get_scores(
        self,
        sport: str,
        days_from: int = 1,
        completed_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get recent scores for a sport.

        Args:
            sport: Sport key.
            days_from: Number of days to look back.
            completed_only: If True, only return completed games.

        Returns:
            List of score data.
        """
        params: dict[str, Any] = {"daysFrom": days_from}
        if completed_only:
            params["dateFormat"] = "iso"

        return self._request(f"/sports/{sport}/scores", params=params)

    def get_historical_odds(
        self,
        sport: str,
        date: str,
        regions: str = "us",
        markets: str = "h2h",
    ) -> list[GameOdds]:
        """Get historical odds for a specific date.

        Args:
            sport: Sport key.
            date: Date in ISO format (YYYY-MM-DD).
            regions: Comma-separated regions.
            markets: Market types.

        Returns:
            List of GameOdds objects.

        Note:
            Historical data may require a paid plan.
        """
        params = {
            "regions": regions,
            "markets": markets,
            "date": date,
        }

        data = self._request(f"/historical/sports/{sport}/odds", params=params)

        # Historical endpoint returns nested data
        odds_data = data.get("data", data)
        if isinstance(odds_data, list):
            return [GameOdds.from_api_response(game) for game in odds_data]
        return []

    def find_arbitrage(
        self,
        sport: str,
        markets: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Find arbitrage opportunities in a sport.

        Args:
            sport: Sport key.
            markets: Markets to check (default: h2h).

        Returns:
            List of arbitrage opportunities.

        Example:
            >>> arbs = client.find_arbitrage("basketball_nba")
            >>> for arb in arbs:
            ...     print(f"{arb['game']}: {arb['profit_pct']:.2f}% profit")
        """
        odds = self.get_odds(sport, markets=markets or ["h2h"])
        opportunities = []

        for game in odds:
            best = game.get_best_odds()

            # Check if arbitrage exists
            if best["home"]["odds"] > 0 and best["away"]["odds"] > 0:
                implied_sum = (1 / best["home"]["odds"]) + (1 / best["away"]["odds"])

                if implied_sum < 1:
                    profit_pct = (1 - implied_sum) * 100
                    opportunities.append(
                        {
                            "game": f"{game.away_team} @ {game.home_team}",
                            "sport": sport,
                            "commence_time": game.commence_time,
                            "profit_pct": profit_pct,
                            "best_home": best["home"],
                            "best_away": best["away"],
                        }
                    )

        return sorted(opportunities, key=lambda x: x["profit_pct"], reverse=True)

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self) -> OddsAPIClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
