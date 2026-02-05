# Task: NBA Player Stats Collection

**Owner:** Vansheeka
**Deadline:** Feb 12 (Week 1)
**Priority:** Medium — useful for advanced models

---

## What You're Building

A Python script that collects NBA player statistics using the `nba_api` library and saves them to CSV files.

---

## Why This Matters

Player stats can improve predictions. If a team's best player is having a good season, they're more likely to win. The `nba_api` library gives us free access to official NBA.com player statistics.

---

## Exactly What You Must Deliver

### 1. Install nba_api

```bash
pip install nba_api
```

### 2. Create Collection Script

Create `scripts/collect_nba_player_stats.py`:

```python
"""Collect NBA player statistics using nba_api."""

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats
from nba_api.stats.static import players
import time
from datetime import datetime
from pathlib import Path

def get_all_players() -> list:
    """Get list of all NBA players."""
    return players.get_active_players()

def get_player_stats(season: str = "2025-26", min_games: int = 10) -> pd.DataFrame:
    """
    Get player statistics for a season.

    Args:
        season: Season string like "2025-26"
        min_games: Minimum games played to include

    Returns:
        DataFrame with player stats
    """
    print(f"Fetching player stats for {season}...")

    # Add delay to avoid rate limiting
    time.sleep(2)

    # Fetch from NBA API
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame"  # Per-game averages
    )

    df = stats.get_data_frames()[0]

    # Filter to players with minimum games
    df = df[df['GP'] >= min_games]

    # Select and rename columns we need
    columns_we_want = {
        'PLAYER_ID': 'player_id',
        'PLAYER_NAME': 'player_name',
        'TEAM_ID': 'team_id',
        'TEAM_ABBREVIATION': 'team_abbr',
        'GP': 'games_played',
        'MIN': 'mpg',              # Minutes per game
        'PTS': 'ppg',              # Points per game
        'REB': 'rpg',              # Rebounds per game
        'AST': 'apg',              # Assists per game
        'STL': 'spg',              # Steals per game
        'BLK': 'bpg',              # Blocks per game
        'TOV': 'topg',             # Turnovers per game
        'FG_PCT': 'fg_pct',        # Field goal %
        'FG3_PCT': 'fg3_pct',      # 3-point %
        'FT_PCT': 'ft_pct',        # Free throw %
        'PLUS_MINUS': 'plus_minus', # Plus/minus per game
    }

    # Only use columns that exist
    available = [c for c in columns_we_want.keys() if c in df.columns]
    df = df[available].rename(columns={k: columns_we_want[k] for k in available})

    # Add metadata
    df['season'] = season
    df['collected_at'] = datetime.now()

    return df

def collect_and_save(season: str = "2025-26", output_dir: str = "data/nba") -> str:
    """
    Collect all player stats and save to CSV.

    Returns:
        Path to output file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get player stats
    player_stats = get_player_stats(season)
    print(f"  Got {len(player_stats)} players")

    # Save
    output_file = f"{output_dir}/player_stats_{season.replace('-', '_')}.csv"
    player_stats.to_csv(output_file, index=False)
    print(f"  Saved to {output_file}")

    return output_file

def main():
    """Collect player stats for current season."""
    print("=" * 50)
    print("NBA Player Stats Collection")
    print("=" * 50)

    # Current season
    output = collect_and_save("2025-26")

    print("\n" + "=" * 50)
    print("Collection complete!")
    print(f"Output: {output}")

    # Show preview - top scorers
    df = pd.read_csv(output)
    print(f"\nTop 10 scorers:")
    print(df.nlargest(10, 'ppg')[['player_name', 'team_abbr', 'ppg', 'rpg', 'apg']])

if __name__ == "__main__":
    main()
```

### 3. Test the Script

```bash
# Run collection
python scripts/collect_nba_player_stats.py

# Check output
wc -l data/nba/player_stats_2025_26.csv  # Should be ~400+ players
```

Expected output:
```
==================================================
NBA Player Stats Collection
==================================================
Fetching player stats for 2025-26...
  Got 425 players
  Saved to data/nba/player_stats_2025_26.csv

==================================================
Collection complete!
Output: data/nba/player_stats_2025_26.csv

Top 10 scorers:
         player_name team_abbr   ppg   rpg   apg
0       Luka Doncic       DAL  33.2   8.9  10.1
1     Joel Embiid        PHI  31.5  11.2   5.8
...
```

### 4. Document the Data

Create `team/vansheeka/work/notes/nba-player-stats-fields.md`:

```markdown
# NBA Player Stats Fields

## Columns Collected

| Column | Description | Example |
|--------|-------------|---------|
| player_id | NBA API player ID | 203999 |
| player_name | Player full name | Nikola Jokic |
| team_id | NBA API team ID | 1610612743 |
| team_abbr | Team abbreviation | DEN |
| games_played | Games played | 45 |
| mpg | Minutes per game | 34.2 |
| ppg | Points per game | 26.1 |
| rpg | Rebounds per game | 12.8 |
| apg | Assists per game | 8.4 |
| spg | Steals per game | 1.2 |
| bpg | Blocks per game | 0.8 |
| topg | Turnovers per game | 3.2 |
| fg_pct | Field goal % | 0.583 |
| fg3_pct | 3-point % | 0.381 |
| ft_pct | Free throw % | 0.812 |
| plus_minus | Plus/minus per game | +8.5 |
| season | Season identifier | 2025-26 |
| collected_at | When collected | 2026-02-10 |

## Filtering

- Only includes players with 10+ games played
- Excludes inactive players

## Data Source

- NBA.com via `nba_api` library
- Official statistics

## Useful Aggregations

- Get team's best player: ORDER BY ppg DESC, LIMIT 1 per team
- Player impact: ORDER BY plus_minus DESC
```

---

## Done Checklist

- [ ] Script created at `scripts/collect_nba_player_stats.py`
- [ ] `nba_api` installed and working
- [ ] Script fetches player stats
- [ ] Filters to players with 10+ games
- [ ] Includes key stats (ppg, rpg, apg, plus_minus)
- [ ] Saves to CSV with timestamp
- [ ] Data fields documented
- [ ] CSV file exists with real data

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Run the script
2. Show the CSV output
3. Show top 10 scorers
4. Explain what columns are available

**Duration:** 2 minutes max

---

## Resources

- nba_api docs: https://github.com/swar/nba_api
- nba_api player stats: https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/leaguedashplayerstats.md

---

## Common Issues

**Issue:** API timeout
**Fix:** Add longer delay: `time.sleep(3)`

**Issue:** Too many players (overwhelming)
**Fix:** Increase `min_games` filter to 15 or 20

**Issue:** Missing columns
**Fix:** Print `df.columns` to see what's available

---

## Who To Ask If Stuck

1. Google "nba_api player stats example"
2. Miran — she's doing team stats, similar work
3. Check nba_api GitHub issues
4. Tan — if completely stuck
