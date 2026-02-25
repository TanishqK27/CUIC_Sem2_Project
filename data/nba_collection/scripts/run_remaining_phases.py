#!/usr/bin/env python3
"""Run remaining collection phases (5-9) on already-collected box score data.

Skips games/boxscores since those were done via parallel_nba_collect.py.
Collects: season stats, rosters, injuries, standings, then builds features.

Usage:
    .venv/bin/python scripts/run_remaining_phases.py
    .venv/bin/python scripts/run_remaining_phases.py --proxy-file proxies.txt
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cuic_quant.data.nba.constants import CSV_CONFIG, SEASONS
from cuic_quant.data.nba.csv_writer import save_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run remaining NBA collection phases")
    parser.add_argument("--proxy-file", help="Proxy file for faster API calls")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Enable proxy rotation if provided
    if args.proxy_file:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from parallel_nba_collect import parse_proxy_file
        from cuic_quant.data.nba.api_helper import set_proxy_rotation
        import os

        proxies = parse_proxy_file(args.proxy_file)
        set_proxy_rotation(proxies)
        os.environ["NBA_REQUEST_DELAY"] = "0.5"
        print(f"  Proxy rotation enabled: {len(proxies)} proxies, 0.5s delay")

    start = time.monotonic()

    # Phase 5: Season stats
    print("\n[Phase 5/9] Season stats...")
    from cuic_quant.data.nba.season_stats import collect_player_stats, collect_team_stats
    team_stats = collect_team_stats(SEASONS)
    save_csv(team_stats, out / CSV_CONFIG["nba_team_stats"]["file"], CSV_CONFIG["nba_team_stats"]["pk"])
    print(f"  -> {len(team_stats)} team stat rows")

    player_stats = collect_player_stats(SEASONS)
    save_csv(player_stats, out / CSV_CONFIG["nba_player_stats"]["file"], CSV_CONFIG["nba_player_stats"]["pk"])
    print(f"  -> {len(player_stats)} player stat rows")

    # Phase 6: Rosters
    print("\n[Phase 6/9] Rosters...")
    from cuic_quant.data.nba.rosters import build_players_reference, collect_rosters
    rosters = collect_rosters(SEASONS)
    save_csv(rosters, out / CSV_CONFIG["nba_rosters"]["file"], CSV_CONFIG["nba_rosters"]["pk"])
    players = build_players_reference(rosters)
    save_csv(players, out / CSV_CONFIG["nba_players"]["file"], CSV_CONFIG["nba_players"]["pk"])
    print(f"  -> {len(rosters)} roster entries, {len(players)} unique players")

    # Phase 7: Injuries
    print("\n[Phase 7/9] Injuries...")
    from cuic_quant.data.nba.injuries import collect_injuries
    injuries = collect_injuries(SEASONS)
    save_csv(injuries, out / CSV_CONFIG["nba_injuries"]["file"], CSV_CONFIG["nba_injuries"]["pk"])
    print(f"  -> {len(injuries)} injury records")

    # Phase 8: Standings
    print("\n[Phase 8/9] Standings...")
    from cuic_quant.data.nba.standings import collect_standings
    standings = collect_standings(SEASONS)
    save_csv(standings, out / CSV_CONFIG["nba_standings"]["file"], CSV_CONFIG["nba_standings"]["pk"])
    print(f"  -> {len(standings)} standing rows")

    # Phase 9: Pre-game features
    print("\n[Phase 9/9] Pre-game features...")
    from cuic_quant.data.nba.features import PreGameFeatureBuilder
    builder = PreGameFeatureBuilder(out)
    counts = builder.run()
    for name, count in counts.items():
        print(f"  -> {name}: {count:,} rows")

    elapsed = (time.monotonic() - start) / 60
    print(f"\nDone in {elapsed:.1f} minutes")


if __name__ == "__main__":
    main()
