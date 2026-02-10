# How to Run the NBA Data Collection Script

Hey Max - this script collects all NBA data for the project. Here's how to use it.

## Setup (one time)

```bash
# Make sure you're in the project root
cd CUIC_Sem2_Project

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies (includes nba_api)
pip install -e ".[nba,dev]"

# Verify nba_api works
python -c "from nba_api.stats.static import teams; print(len(teams.get_teams()), 'teams')"
# Should print: 30 teams
```

## Collecting Data

### First Run: Full Historical Collection (~17 hours)

This pulls ALL data for seasons 2021-22 through 2024-25. It's a lot of API calls so it takes a while. **Run it overnight.**

```bash
python scripts/collect_nba_stats.py --mode full --resume
```

Always use `--resume` so if it gets interrupted (laptop sleeps, internet drops), you can just run the same command again and it picks up where it left off.

**IMPORTANT:** This must run on your local machine (not cloud/university servers). NBA blocks cloud IPs.

### Daily Updates (~1-2 minutes)

After the first full run, use this to pull new games:

```bash
python scripts/collect_nba_stats.py --mode update
```

### Just One Season

```bash
python scripts/collect_nba_stats.py --mode full --seasons 2024-25 --resume
```

### See What It Would Do (No API Calls)

```bash
python scripts/collect_nba_stats.py --mode full --dry-run
```

## Output

After running, you'll find these CSVs in the `data/` folder:

| File | What It Contains | ~Rows |
|------|-----------------|-------|
| `nba_games.csv` | Every game with quarter scores | 5,000 |
| `nba_game_boxscores_player.csv` | Player stats per game per quarter | 500,000+ |
| `nba_game_boxscores_team.csv` | Team stats per game per quarter | 50,000 |
| `nba_game_advanced_player.csv` | Advanced stats per game per quarter | 500,000+ |
| `nba_game_hustle_player.csv` | Hustle stats (deflections, contested shots) | 120,000 |
| `nba_game_tracking_player.csv` | Tracking (speed, distance, touches) | 120,000 |
| `nba_team_stats.csv` | Team season averages | 120 |
| `nba_player_stats.csv` | Player season averages | 2,000 |
| `nba_rosters.csv` | Team rosters (position, height, weight) | 2,000 |
| `nba_players.csv` | Player master list | 600 |
| `nba_teams.csv` | Team reference (30 NBA teams) | 30 |
| `nba_injuries.csv` | Injury reports | 5,000+ |
| `nba_standings.csv` | Season standings | 120 |

All files use `team_abbr` (3-letter codes like LAL, BOS) so they join with Alfie's odds data.

## Giving Data to Dietrich

Once you have the CSVs, Dietrich can load them straight into the database. The files are in `data/` - just tell him they're ready.

## Troubleshooting

**"Connection timeout" or "429" errors:** The script handles these automatically with retries. If you see a lot of them, the NBA might be throttling you. Wait 30 min and try again with `--resume`.

**"No games found":** Make sure you're on a residential internet connection, not university/cloud.

**Interrupted mid-run:** Just run the same command again with `--resume`. It skips games already collected.

**Logs:** Check `logs/nba_collection.log` for detailed output.

## Questions?

Ask Tan or check the design doc: `docs/plans/2026-02-10-nba-data-collection-design.md`
