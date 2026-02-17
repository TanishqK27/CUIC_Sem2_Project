#!/usr/bin/env python3
"""Post-collection audit: report coverage gaps across all NBA datasets.

Usage:
    python scripts/audit_nba_collection.py
    python scripts/audit_nba_collection.py --data-dir data
    python scripts/audit_nba_collection.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Expected CSV files and their key columns
DATASETS = {
    "nba_games.csv": {"pk": ["game_id"], "label": "Games"},
    "nba_game_boxscores_player.csv": {"pk": ["game_id", "player_id", "period"], "label": "Traditional (Player)"},
    "nba_game_boxscores_team.csv": {"pk": ["game_id", "team_id", "period"], "label": "Traditional (Team)"},
    "nba_game_advanced_player.csv": {"pk": ["game_id", "player_id", "period"], "label": "Advanced (Player)"},
    "nba_game_hustle_player.csv": {"pk": ["game_id", "player_id"], "label": "Hustle (Player)"},
    "nba_game_tracking_player.csv": {"pk": ["game_id", "player_id"], "label": "Tracking (Player)"},
    "nba_team_stats.csv": {"pk": ["team_id", "season"], "label": "Team Season Stats"},
    "nba_player_stats.csv": {"pk": ["player_id", "season"], "label": "Player Season Stats"},
    "nba_rosters.csv": {"pk": ["player_id", "team_id", "season"], "label": "Rosters"},
    "nba_players.csv": {"pk": ["player_id"], "label": "Players Reference"},
    "nba_teams.csv": {"pk": ["team_id"], "label": "Teams Reference"},
    "nba_injuries.csv": {"pk": ["player_name", "team_abbr", "report_date"], "label": "Injuries"},
    "nba_standings.csv": {"pk": ["team_id", "season"], "label": "Standings"},
}

BOXSCORE_DATASETS = [
    "nba_game_boxscores_player.csv",
    "nba_game_boxscores_team.csv",
    "nba_game_advanced_player.csv",
    "nba_game_hustle_player.csv",
    "nba_game_tracking_player.csv",
]


def load_csv(data_dir: Path, filename: str) -> pd.DataFrame | None:
    path = data_dir / filename
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, dtype={"game_id": str})
    except Exception:
        return None


def audit_file_existence(data_dir: Path) -> dict[str, bool]:
    """Check which CSV files exist."""
    return {f: (data_dir / f).exists() for f in DATASETS}


def audit_row_counts(data_dir: Path) -> dict[str, int]:
    """Get row counts for each CSV."""
    counts = {}
    for filename in DATASETS:
        df = load_csv(data_dir, filename)
        counts[filename] = len(df) if df is not None else 0
    return counts


def audit_season_coverage(data_dir: Path, verbose: bool = False) -> dict[str, dict]:
    """Check per-season coverage for datasets that have a season column."""
    results = {}
    season_files = [
        ("nba_games.csv", "season"),
        ("nba_team_stats.csv", "season"),
        ("nba_player_stats.csv", "season"),
        ("nba_rosters.csv", "season"),
        ("nba_standings.csv", "season"),
    ]
    for filename, col in season_files:
        df = load_csv(data_dir, filename)
        if df is None or col not in df.columns:
            results[filename] = {}
            continue
        results[filename] = df.groupby(col).size().to_dict()
    return results


def audit_boxscore_coverage(data_dir: Path) -> dict[str, dict]:
    """Compare boxscore game_ids against the games master list."""
    games_df = load_csv(data_dir, "nba_games.csv")
    if games_df is None:
        return {"error": "nba_games.csv not found"}

    all_game_ids = set(games_df["game_id"].astype(str).unique())
    total_games = len(all_game_ids)

    # Per-season game counts for context
    season_counts = {}
    if "season" in games_df.columns:
        season_counts = games_df.groupby("season")["game_id"].nunique().to_dict()

    results = {"total_games": total_games, "season_counts": season_counts, "datasets": {}}

    for filename in BOXSCORE_DATASETS:
        df = load_csv(data_dir, filename)
        if df is None:
            results["datasets"][filename] = {
                "games_covered": 0,
                "coverage_pct": 0.0,
                "missing_count": total_games,
            }
            continue

        covered_ids = set(df["game_id"].astype(str).unique())
        covered = len(covered_ids & all_game_ids)
        missing = all_game_ids - covered_ids
        results["datasets"][filename] = {
            "games_covered": covered,
            "coverage_pct": round(100 * covered / total_games, 1) if total_games else 0,
            "missing_count": len(missing),
        }

    return results


def audit_checkpoint(data_dir: Path) -> dict:
    """Read checkpoint file and summarize completeness."""
    ckpt_path = data_dir / ".nba_checkpoint.json"
    if not ckpt_path.exists():
        return {"exists": False}

    data = json.loads(ckpt_path.read_text())
    incomplete = {}
    all_expected = {"traditional_player", "traditional_team", "advanced", "hustle", "tracking"}
    for game_id, datasets in data.get("game_datasets", {}).items():
        missing = all_expected - set(datasets)
        if missing:
            incomplete[game_id] = sorted(missing)

    return {
        "exists": True,
        "last_update": data.get("last_update"),
        "seasons_completed": data.get("seasons_completed", []),
        "games_in_checkpoint": len(data.get("games_collected", {}).get("boxscores", [])),
        "games_with_completeness": len(data.get("game_datasets", {})),
        "incomplete_games": len(incomplete),
        "error_count": len(data.get("errors", [])),
        "sample_errors": data.get("errors", [])[:5],
        "sample_incomplete": dict(list(incomplete.items())[:5]),
    }


def print_report(data_dir: Path, verbose: bool = False) -> bool:
    """Print full audit report. Returns True if all checks pass."""
    print(f"\n{'='*60}")
    print(f"  NBA Collection Audit — {data_dir.resolve()}")
    print(f"{'='*60}\n")

    all_ok = True

    # 1. File existence
    existence = audit_file_existence(data_dir)
    counts = audit_row_counts(data_dir)
    print("1. Dataset Files\n")
    print(f"  {'Dataset':<30} {'Rows':>10}  Status")
    print(f"  {'-'*30} {'-'*10}  {'-'*10}")
    for filename, info in DATASETS.items():
        exists = existence[filename]
        count = counts[filename]
        status = "OK" if exists and count > 0 else "MISSING"
        if status == "MISSING":
            all_ok = False
        print(f"  {info['label']:<30} {count:>10,}  {status}")
    print()

    # 2. Season coverage
    print("2. Season Coverage\n")
    season_cov = audit_season_coverage(data_dir, verbose)
    for filename, seasons in season_cov.items():
        label = DATASETS[filename]["label"]
        if not seasons:
            print(f"  {label}: no data")
            all_ok = False
        else:
            season_str = ", ".join(f"{s}: {c:,}" for s, c in sorted(seasons.items()))
            print(f"  {label}: {season_str}")
    print()

    # 3. Boxscore coverage
    print("3. Boxscore Coverage (per-game)\n")
    bs_cov = audit_boxscore_coverage(data_dir)
    if "error" in bs_cov:
        print(f"  {bs_cov['error']}")
        all_ok = False
    else:
        total = bs_cov["total_games"]
        print(f"  Total games in master list: {total:,}")
        if bs_cov.get("season_counts"):
            for s, c in sorted(bs_cov["season_counts"].items()):
                print(f"    {s}: {c:,} games")
        print()
        print(f"  {'Dataset':<30} {'Covered':>10} {'Missing':>10} {'Pct':>8}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8}")
        for filename, stats in bs_cov["datasets"].items():
            label = DATASETS[filename]["label"]
            pct = stats["coverage_pct"]
            if pct < 95:
                all_ok = False
            print(
                f"  {label:<30} {stats['games_covered']:>10,} "
                f"{stats['missing_count']:>10,} {pct:>7.1f}%"
            )
    print()

    # 4. Checkpoint status
    print("4. Checkpoint Status\n")
    ckpt = audit_checkpoint(data_dir)
    if not ckpt["exists"]:
        print("  No checkpoint file found.")
    else:
        print(f"  Last update: {ckpt['last_update']}")
        print(f"  Seasons completed: {', '.join(ckpt['seasons_completed']) or 'none'}")
        print(f"  Games in checkpoint: {ckpt['games_in_checkpoint']:,}")
        print(f"  Games with completeness data: {ckpt['games_with_completeness']:,}")
        print(f"  Incomplete games: {ckpt['incomplete_games']:,}")
        print(f"  Errors logged: {ckpt['error_count']:,}")
        if ckpt["sample_errors"] and verbose:
            print(f"\n  Sample errors:")
            for err in ckpt["sample_errors"]:
                print(f"    - {err}")
        if ckpt["sample_incomplete"] and verbose:
            print(f"\n  Sample incomplete games:")
            for gid, missing in ckpt["sample_incomplete"].items():
                print(f"    - {gid}: missing {', '.join(missing)}")
    print()

    # Summary
    print(f"{'='*60}")
    if all_ok:
        print("  RESULT: ALL CHECKS PASSED")
    else:
        print("  RESULT: ISSUES FOUND (see above)")
    print(f"{'='*60}\n")

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit NBA data collection completeness")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    parser.add_argument("--verbose", action="store_true", help="Show detailed error/gap info")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)

    ok = print_report(data_dir, verbose=args.verbose)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
