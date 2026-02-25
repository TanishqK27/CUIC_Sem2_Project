# NBA Data Collection Scripts

All code used to pull NBA data (box scores, stats, rosters, injuries, standings, pre-game features) from the NBA Stats API via the `nba_api` Python package.

## Structure

```
nba_collection/
├── modules/          # Python modules (the actual collectors)
│   ├── api_helper.py     # Rate-limited NBA API wrapper with retry + proxy support
│   ├── boxscores.py      # Traditional, Advanced, Hustle, Tracking box scores
│   ├── checkpoint.py     # JSON-based resume/checkpoint system
│   ├── collector.py      # NBACollector orchestrator (runs all phases)
│   ├── constants.py      # Team mappings, seasons list, CSV schema config
│   ├── csv_writer.py     # CSV persistence with append + dedup on primary keys
│   ├── games.py          # Game discovery + quarter scores
│   ├── injuries.py       # Injury report collection
│   ├── rosters.py        # Roster data + player reference
│   ├── season_stats.py   # Player and team season-wide stats
│   ├── standings.py      # Standings
│   └── teams.py          # Teams reference
│
└── scripts/          # Orchestration scripts (invoke the modules)
    ├── parallel_nba_collect.py   # Main: parallel collection with proxy rotation
    ├── merge_nba_workers.py      # Merge parallel worker outputs + dedup
    ├── audit_nba_collection.py   # Coverage audit (gaps per season/game)
    ├── run_remaining_phases.py   # Phases 5-9 (stats, rosters, injuries, etc.)
    ├── run_nba_collection.sh     # Shell wrapper with auto-resume
    ├── cron_nba_collect.sh       # Cron one-shot wrapper
    └── nba_live_update.sh        # Incremental live updates (loop or launchd)
```

## Quick Start

```bash
# Install dependency
pip install nba_api

# Full parallel collection (needs proxies for large runs)
python data/nba_collection/scripts/parallel_nba_collect.py \
    --proxy-file proxies.txt --seasons 2024-25

# Or use the orchestrator directly
python -c "
from data.nba_collection.modules.collector import NBACollector
c = NBACollector(output_dir='data', seasons=['2024-25'])
c.run()
"

# Merge worker outputs
python data/nba_collection/scripts/merge_nba_workers.py --cleanup

# Audit coverage
python data/nba_collection/scripts/audit_nba_collection.py --verbose
```

## Output CSVs

| File | Primary Key | Description |
|------|-------------|-------------|
| `nba_games.csv` | game_id | Master game list with scores |
| `nba_game_boxscores_player.csv` | game_id, player_id, period | Traditional player stats |
| `nba_game_boxscores_team.csv` | game_id, team_id, period | Traditional team stats |
| `nba_game_advanced_player.csv` | game_id, player_id, period | Advanced player stats |
| `nba_game_hustle_player.csv` | game_id, player_id | Hustle stats |
| `nba_game_tracking_player.csv` | game_id, player_id | Player tracking data |
| `nba_team_stats.csv` | team_id, season | Season-wide team stats |
| `nba_player_stats.csv` | player_id, season | Season-wide player stats |
| `nba_rosters.csv` | player_id, team_id, season | Roster assignments |
| `nba_players.csv` | player_id | Player reference |
| `nba_teams.csv` | team_id | Team reference |
| `nba_injuries.csv` | player_name, team_abbr, report_date | Injury reports |
| `nba_standings.csv` | team_id, season | Standings |
| `pregame_team.csv` | game_id, team_id | Pre-game team features |
| `pregame_player.csv` | game_id, player_id | Pre-game player features |
| `pregame_availability.csv` | game_id, player_id | Player availability |

## Notes

- These modules were originally at `src/cuic_quant/data/nba/` and were removed from git during a cleanup. Restored from commit `1791e10`.
- The feature engineering module (`features.py`) that builds pre-game features still lives at `src/cuic_quant/data/nba/features.py`.
- Data source: `nba_api` package (NBA official stats API). Seasons 2021-22 through 2025-26.
- Proxy support: SOCKS5h format. Use webshare.io or similar for large collection runs.
- Checkpoint: `.nba_checkpoint.json` tracks progress for resume capability.
