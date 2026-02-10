"""Main NBA data collection orchestrator."""

from __future__ import annotations

import datetime
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from cuic_quant.data.nba.boxscores import (
    collect_advanced_boxscore,
    collect_hustle_boxscore,
    collect_tracking_boxscore,
    collect_traditional_boxscore,
)
from cuic_quant.data.nba.checkpoint import Checkpoint
from cuic_quant.data.nba.constants import CSV_CONFIG, CURRENT_SEASON, SEASONS
from cuic_quant.data.nba.csv_writer import save_csv
from cuic_quant.data.nba.games import collect_quarter_scores, discover_games
from cuic_quant.data.nba.injuries import collect_injuries
from cuic_quant.data.nba.rosters import build_players_reference, collect_rosters
from cuic_quant.data.nba.season_stats import collect_player_stats, collect_team_stats
from cuic_quant.data.nba.standings import collect_standings
from cuic_quant.data.nba.teams import collect_teams

logger = logging.getLogger(__name__)


class NBACollector:
    """Orchestrates full and incremental NBA data collection."""

    def __init__(
        self,
        output_dir: str = "data",
        seasons: list[str] | None = None,
        resume: bool = False,
        retry_failed: bool = False,
        dry_run: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seasons = seasons or SEASONS
        self.resume = resume
        self.retry_failed = retry_failed
        self.dry_run = dry_run
        self.checkpoint = Checkpoint(self.output_dir / ".nba_checkpoint.json")

    def _csv_path(self, name: str) -> Path:
        return self.output_dir / CSV_CONFIG[name]["file"]

    def _pk(self, name: str) -> list[str]:
        return CSV_CONFIG[name]["pk"]

    def _save(self, name: str, df: pd.DataFrame) -> None:
        if df.empty:
            return
        save_csv(df, self._csv_path(name), self._pk(name))

    def run_full(self) -> None:
        """Run full historical collection for all configured seasons."""
        logger.info("Starting full collection for seasons: %s", self.seasons)

        if self.dry_run:
            self._print_plan()
            return

        # 1. Teams (static reference)
        logger.info("Phase 1/8: Teams")
        teams_df = collect_teams()
        self._save("nba_teams", teams_df)

        # 2. Games discovery
        logger.info("Phase 2/8: Game discovery")
        games_df = discover_games(seasons=self.seasons)
        if games_df.empty:
            logger.error("No games discovered. Aborting.")
            return

        # 3. Quarter scores
        logger.info("Phase 3/8: Quarter scores")
        games_df = collect_quarter_scores(games_df)
        self._save("nba_games", games_df)

        # 4. Box scores (the big one)
        logger.info("Phase 4/8: Box scores")
        self._collect_all_boxscores(games_df)

        # 5. Season stats
        logger.info("Phase 5/8: Season stats")
        self._save("nba_team_stats", collect_team_stats(self.seasons))
        self._save("nba_player_stats", collect_player_stats(self.seasons))

        # 6. Rosters
        logger.info("Phase 6/8: Rosters")
        rosters_df = collect_rosters(self.seasons)
        self._save("nba_rosters", rosters_df)
        self._save("nba_players", build_players_reference(rosters_df))

        # 7. Injuries
        logger.info("Phase 7/8: Injuries")
        self._save("nba_injuries", collect_injuries(self.seasons))

        # 8. Standings
        logger.info("Phase 8/8: Standings")
        self._save("nba_standings", collect_standings(self.seasons))

        # Update checkpoint
        self.checkpoint.last_update = datetime.date.today().isoformat()
        for season in self.seasons:
            self.checkpoint.mark_season_completed(season)
        self.checkpoint.save()

        self._print_summary()

    def run_update(self) -> None:
        """Run incremental update since last collection date."""
        since = self.checkpoint.last_update
        if since is None:
            logger.error("No checkpoint found. Run --mode full first.")
            return

        logger.info("Running incremental update since %s", since)

        if self.dry_run:
            print(f"Would collect games since {since}")
            return

        # Discover new games
        games_df = discover_games(seasons=[CURRENT_SEASON], since_date=since)
        if games_df.empty:
            logger.info("No new games since %s", since)
            return

        logger.info("Found %d new games since %s", len(games_df), since)

        # Quarter scores for new games
        games_df = collect_quarter_scores(games_df)
        self._save("nba_games", games_df)

        # Box scores for new games
        self._collect_all_boxscores(games_df)

        # Refresh current season aggregates
        self._save("nba_team_stats", collect_team_stats([CURRENT_SEASON]))
        self._save("nba_player_stats", collect_player_stats([CURRENT_SEASON]))
        self._save("nba_rosters", collect_rosters([CURRENT_SEASON]))
        self._save("nba_injuries", collect_injuries([CURRENT_SEASON]))
        self._save("nba_standings", collect_standings([CURRENT_SEASON]))

        # Update checkpoint
        self.checkpoint.last_update = datetime.date.today().isoformat()
        self.checkpoint.save()

        self._print_summary()

    def _collect_all_boxscores(self, games_df: pd.DataFrame) -> None:
        """Collect all box score variants for each game in games_df."""
        game_ids = games_df["game_id"].unique().tolist()
        logger.info("Collecting box scores for %d games", len(game_ids))

        trad_player_frames = []
        trad_team_frames = []
        adv_frames = []
        hustle_frames = []
        tracking_frames = []

        for game_id in tqdm(game_ids, desc="Box scores"):
            # Skip if already collected (resume mode)
            if self.resume and self.checkpoint.is_game_collected("boxscores", game_id):
                continue

            # Traditional (per quarter)
            player_df, team_df = collect_traditional_boxscore(game_id)
            if not player_df.empty:
                trad_player_frames.append(player_df)
            if not team_df.empty:
                trad_team_frames.append(team_df)

            # Advanced (per quarter)
            adv_df = collect_advanced_boxscore(game_id)
            if not adv_df.empty:
                adv_frames.append(adv_df)

            # Hustle (full game only)
            hustle_df = collect_hustle_boxscore(game_id)
            if not hustle_df.empty:
                hustle_frames.append(hustle_df)

            # Tracking (full game only)
            tracking_df = collect_tracking_boxscore(game_id)
            if not tracking_df.empty:
                tracking_frames.append(tracking_df)

            # Mark collected and save checkpoint periodically
            self.checkpoint.mark_game_collected("boxscores", game_id)
            if len(trad_player_frames) % 50 == 0 and trad_player_frames:
                self._flush_boxscores(
                    trad_player_frames, trad_team_frames,
                    adv_frames, hustle_frames, tracking_frames,
                )
                trad_player_frames.clear()
                trad_team_frames.clear()
                adv_frames.clear()
                hustle_frames.clear()
                tracking_frames.clear()
                self.checkpoint.save()

        # Final flush
        self._flush_boxscores(
            trad_player_frames, trad_team_frames,
            adv_frames, hustle_frames, tracking_frames,
        )
        self.checkpoint.save()

    def _flush_boxscores(
        self,
        trad_player: list[pd.DataFrame],
        trad_team: list[pd.DataFrame],
        advanced: list[pd.DataFrame],
        hustle: list[pd.DataFrame],
        tracking: list[pd.DataFrame],
    ) -> None:
        """Write accumulated box score data to CSVs."""
        if trad_player:
            self._save("nba_game_boxscores_player", pd.concat(trad_player, ignore_index=True))
        if trad_team:
            self._save("nba_game_boxscores_team", pd.concat(trad_team, ignore_index=True))
        if advanced:
            self._save("nba_game_advanced_player", pd.concat(advanced, ignore_index=True))
        if hustle:
            self._save("nba_game_hustle_player", pd.concat(hustle, ignore_index=True))
        if tracking:
            self._save("nba_game_tracking_player", pd.concat(tracking, ignore_index=True))

    def _print_plan(self) -> None:
        """Print what would be collected (dry run)."""
        print(f"\nDry run - collection plan:")
        print(f"  Seasons: {self.seasons}")
        print(f"  Output: {self.output_dir}")
        print(f"  Resume: {self.resume}")
        print(f"\n  Estimated phases:")
        print(f"    1. Teams (30 rows, 0 API calls)")
        print(f"    2. Games (~1,250/season x {len(self.seasons)} seasons)")
        print(f"    3. Quarter scores (~600 API calls)")
        print(f"    4. Box scores (~12 calls/game x ~5000 games)")
        print(f"    5. Season stats (~16 API calls)")
        print(f"    6. Rosters (~120 API calls)")
        print(f"    7. Injuries (via nbainjuries)")
        print(f"    8. Standings (~4 API calls)")

    def _print_summary(self) -> None:
        """Print collection summary."""
        print(f"\nCollection complete!")
        print(f"  Total API calls: {self.checkpoint.total_api_calls}")
        print(f"  Errors: {len(self.checkpoint.errors)}")
        print(f"\n  Output files:")
        for name, config in CSV_CONFIG.items():
            path = self._csv_path(name)
            if path.exists():
                df = pd.read_csv(path)
                print(f"    {config['file']}: {len(df):,} rows")
            else:
                print(f"    {config['file']}: not created")
