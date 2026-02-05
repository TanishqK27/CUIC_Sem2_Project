# Task: NBA Team Stats Collection

**Owner:** Miran
**Deadline:** Feb 12 (Week 1)
**Priority:** High — models need this data

---

## What You're Building

A Python script that collects NBA team statistics using the `nba_api` library and saves them to CSV files.

---

## Why This Matters

Our models need team stats to make predictions: win percentage, points per game, defensive rating, etc. The `nba_api` library gives us free access to official NBA.com statistics.

---

## Exactly What You Must Deliver

### 1. Install nba_api

```bash
pip install nba_api
```

### 2. Create Collection Script

Create `scripts/collect_nba_team_stats.py`:

```python
"""Collect NBA team statistics using nba_api."""

import pandas as pd
from nba_api.stats.endpoints import leaguedashteamstats
from nba_api.stats.static import teams
import time
from datetime import datetime
from pathlib import Path

def get_all_teams() -> list:
    """Get list of all NBA teams."""
    return teams.get_teams()

def get_team_stats(season: str = "2025-26") -> pd.DataFrame:
    """
    Get team statistics for a season.

    Args:
        season: Season string like "2025-26"

    Returns:
        DataFrame with team stats
    """
    print(f"Fetching team stats for {season}...")

    # Add delay to avoid rate limiting
    time.sleep(1)

    # Fetch from NBA API
    stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame"  # Per-game averages
    )

    df = stats.get_data_frames()[0]

    # Select and rename columns we need
    columns_we_want = {
        'TEAM_ID': 'team_id',
        'TEAM_NAME': 'team_name',
        'GP': 'games_played',
        'W': 'wins',
        'L': 'losses',
        'W_PCT': 'win_pct',
        'PTS': 'ppg',               # Points per game
        'REB': 'rpg',               # Rebounds per game
        'AST': 'apg',               # Assists per game
        'STL': 'spg',               # Steals per game
        'BLK': 'bpg',               # Blocks per game
        'TOV': 'topg',              # Turnovers per game
        'FG_PCT': 'fg_pct',         # Field goal %
        'FG3_PCT': 'fg3_pct',       # 3-point %
        'FT_PCT': 'ft_pct',         # Free throw %
        'PLUS_MINUS': 'plus_minus', # Plus/minus per game
    }

    df = df[list(columns_we_want.keys())].rename(columns=columns_we_want)

    # Add metadata
    df['season'] = season
    df['collected_at'] = datetime.now()

    return df

def get_opponent_stats(season: str = "2025-26") -> pd.DataFrame:
    """
    Get opponent (defensive) statistics.

    This tells us how well teams defend.
    """
    print(f"Fetching opponent stats for {season}...")
    time.sleep(1)

    stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Opponent"  # Opponent stats
    )

    df = stats.get_data_frames()[0]

    columns = {
        'TEAM_ID': 'team_id',
        'TEAM_NAME': 'team_name',
        'OPP_PTS': 'opp_ppg',       # Opponent points per game
        'OPP_REB': 'opp_rpg',
        'OPP_AST': 'opp_apg',
        'OPP_FG_PCT': 'opp_fg_pct',
    }

    # Check what columns are actually available
    available = [c for c in columns.keys() if c in df.columns]
    df = df[available].rename(columns={k: v for k, v in columns.items() if k in available})

    return df

def collect_and_save(season: str = "2025-26", output_dir: str = "data/nba") -> str:
    """
    Collect all team stats and save to CSV.

    Returns:
        Path to output file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get team stats
    team_stats = get_team_stats(season)
    print(f"  Got {len(team_stats)} teams")

    # Try to get opponent stats (may fail depending on API)
    try:
        opp_stats = get_opponent_stats(season)
        # Merge on team_id
        team_stats = team_stats.merge(
            opp_stats[['team_id', 'opp_ppg']],
            on='team_id',
            how='left'
        )
        print(f"  Added opponent stats")
    except Exception as e:
        print(f"  Could not get opponent stats: {e}")
        team_stats['opp_ppg'] = None

    # Calculate net rating
    if 'opp_ppg' in team_stats.columns and team_stats['opp_ppg'].notna().any():
        team_stats['net_rating'] = team_stats['ppg'] - team_stats['opp_ppg']
    else:
        team_stats['net_rating'] = None

    # Save
    output_file = f"{output_dir}/team_stats_{season.replace('-', '_')}.csv"
    team_stats.to_csv(output_file, index=False)
    print(f"  Saved to {output_file}")

    return output_file

def main():
    """Collect team stats for current season."""
    print("=" * 50)
    print("NBA Team Stats Collection")
    print("=" * 50)

    # Current season
    output = collect_and_save("2025-26")

    print("\n" + "=" * 50)
    print("Collection complete!")
    print(f"Output: {output}")

    # Show preview
    df = pd.read_csv(output)
    print(f"\nPreview (top 5 by win %):")
    print(df.nlargest(5, 'win_pct')[['team_name', 'wins', 'losses', 'win_pct', 'ppg']])

if __name__ == "__main__":
    main()
```

### 3. Test the Script

```bash
# Run collection
python scripts/collect_nba_team_stats.py

# Check output
cat data/nba/team_stats_2025_26.csv | head -5
```

Expected output:
```
==============================================
NBA Team Stats Collection
==============================================
Fetching team stats for 2025-26...
  Got 30 teams
  Added opponent stats
  Saved to data/nba/team_stats_2025_26.csv

==============================================
Collection complete!
Output: data/nba/team_stats_2025_26.csv

Preview (top 5 by win %):
        team_name  wins  losses  win_pct    ppg
0  Boston Celtics    35      10    0.778  120.5
1   Denver Nuggets    32      14    0.696  115.2
...
```

### 4. Document the Data

Create `team/miran/work/notes/nba-team-stats-fields.md`:

```markdown
# NBA Team Stats Fields

## Columns Collected

| Column | Description | Example |
|--------|-------------|---------|
| team_id | NBA API team ID | 1610612747 |
| team_name | Full team name | Los Angeles Lakers |
| games_played | Games played this season | 45 |
| wins | Total wins | 28 |
| losses | Total losses | 17 |
| win_pct | Win percentage (0-1) | 0.622 |
| ppg | Points per game | 112.5 |
| rpg | Rebounds per game | 44.2 |
| apg | Assists per game | 26.1 |
| opp_ppg | Opponent points per game | 108.3 |
| net_rating | ppg - opp_ppg | 4.2 |
| fg_pct | Field goal percentage | 0.471 |
| season | Season identifier | 2025-26 |
| collected_at | When data was collected | 2026-02-10 14:00 |

## Data Source

- NBA.com via `nba_api` library
- Official statistics

## Update Frequency

- Should be collected daily during season
- Games played late evening, stats update overnight
```

---

## Done Checklist

- [ ] Script created at `scripts/collect_nba_team_stats.py`
- [ ] `nba_api` installed and working
- [ ] Script fetches all 30 NBA teams
- [ ] Includes offensive stats (ppg, rpg, apg)
- [ ] Includes win/loss record
- [ ] Saves to CSV with timestamp
- [ ] Data fields documented
- [ ] CSV file exists with real data

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Run the script
2. Show the CSV output
3. Show top 5 teams by win percentage
4. Explain what columns are available

**Duration:** 2 minutes max

---

## Resources

- nba_api docs: https://github.com/swar/nba_api
- nba_api examples: https://github.com/swar/nba_api/tree/master/docs/examples

---

## Common Issues

**Issue:** API rate limiting (too many requests)
**Fix:** Add `time.sleep(1)` between requests

**Issue:** Season not found
**Fix:** Check season format is "YYYY-YY" (e.g., "2025-26")

**Issue:** Import error for nba_api
**Fix:** `pip install nba_api --upgrade`

---

## Who To Ask If Stuck

1. Google "nba_api team stats example"
2. Check nba_api GitHub issues
3. Vansheeka — she's doing player stats, similar work
4. Tan — if completely stuck
