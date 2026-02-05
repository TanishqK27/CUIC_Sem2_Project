# Task: Load NBA Player Stats to Railway DB

**Owner:** Vansheeka
**Deadline:** Feb 19 (Week 2)
**Priority:** Medium — useful for advanced models

---

## What You're Building

A script that loads the player stats CSV files into Dietrich's Railway PostgreSQL database.

---

## Why This Matters

Player stats in the database means models can query "who's the best player on each team" and use that for predictions. This is especially useful for player prop bets.

---

## Exactly What You Must Deliver

### 1. Understand Dietrich's Schema

Dietrich will create this table (from his Task 02):

```sql
CREATE TABLE nba_player_stats (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    player_id INTEGER,
    team_name VARCHAR(100),
    team_abbr VARCHAR(10),
    season VARCHAR(10) NOT NULL,
    games_played INTEGER,
    mpg DECIMAL(4,1),
    ppg DECIMAL(4,1),
    rpg DECIMAL(4,1),
    apg DECIMAL(4,1),
    spg DECIMAL(3,1),
    bpg DECIMAL(3,1),
    topg DECIMAL(3,1),
    fg_pct DECIMAL(4,3),
    fg3_pct DECIMAL(4,3),
    ft_pct DECIMAL(4,3),
    plus_minus DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, season)
);
```

### 2. Create Loading Script

Create `scripts/load_player_stats_to_railway.py`:

```python
"""Load NBA player stats CSV to Railway PostgreSQL."""

import pandas as pd
import psycopg2
import os
from pathlib import Path

def get_connection():
    """Get Railway database connection."""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_player_stats(csv_path: str) -> dict:
    """
    Load player stats from CSV into Railway DB.

    Args:
        csv_path: Path to player stats CSV

    Returns:
        Summary of operation
    """
    print(f"Loading {csv_path}...")

    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"  Read {len(df)} rows")

    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    errors = 0

    for _, row in df.iterrows():
        try:
            # Use UPSERT to handle duplicates
            cursor.execute("""
                INSERT INTO nba_player_stats (
                    player_name, player_id, team_abbr, season,
                    games_played, mpg, ppg, rpg, apg, spg, bpg, topg,
                    fg_pct, fg3_pct, ft_pct, plus_minus
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name, season)
                DO UPDATE SET
                    player_id = EXCLUDED.player_id,
                    team_abbr = EXCLUDED.team_abbr,
                    games_played = EXCLUDED.games_played,
                    mpg = EXCLUDED.mpg,
                    ppg = EXCLUDED.ppg,
                    rpg = EXCLUDED.rpg,
                    apg = EXCLUDED.apg,
                    spg = EXCLUDED.spg,
                    bpg = EXCLUDED.bpg,
                    topg = EXCLUDED.topg,
                    fg_pct = EXCLUDED.fg_pct,
                    fg3_pct = EXCLUDED.fg3_pct,
                    ft_pct = EXCLUDED.ft_pct,
                    plus_minus = EXCLUDED.plus_minus,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) as inserted
            """, (
                row.get('player_name'),
                row.get('player_id'),
                row.get('team_abbr'),
                row.get('season'),
                row.get('games_played'),
                row.get('mpg'),
                row.get('ppg'),
                row.get('rpg'),
                row.get('apg'),
                row.get('spg'),
                row.get('bpg'),
                row.get('topg'),
                row.get('fg_pct'),
                row.get('fg3_pct'),
                row.get('ft_pct'),
                row.get('plus_minus'),
            ))

            result = cursor.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1

        except Exception as e:
            print(f"  Error loading {row.get('player_name')}: {e}")
            errors += 1
            continue

    conn.commit()
    conn.close()

    print(f"  Inserted: {inserted}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")

    return {
        'file': csv_path,
        'inserted': inserted,
        'updated': updated,
        'errors': errors
    }

def load_all_player_stats(directory: str = "data/nba") -> list:
    """Load all player stats CSVs in directory."""
    results = []
    for path in Path(directory).glob("player_stats_*.csv"):
        result = load_player_stats(str(path))
        results.append(result)
    return results

def verify_load():
    """Check data was loaded correctly."""
    conn = get_connection()
    cursor = conn.cursor()

    # Count rows
    cursor.execute("SELECT COUNT(*) FROM nba_player_stats")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows in nba_player_stats: {count}")

    # Top scorers
    cursor.execute("""
        SELECT player_name, team_abbr, ppg, rpg, apg
        FROM nba_player_stats
        WHERE season = '2025-26'
        ORDER BY ppg DESC
        LIMIT 10
    """)

    print("\nTop 10 scorers:")
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]}): {row[2]} PPG, {row[3]} RPG, {row[4]} APG")

    # Players by team
    cursor.execute("""
        SELECT team_abbr, COUNT(*) as players
        FROM nba_player_stats
        WHERE season = '2025-26'
        GROUP BY team_abbr
        ORDER BY players DESC
        LIMIT 5
    """)

    print("\nPlayers per team (top 5):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} players")

    conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        load_player_stats(sys.argv[1])
    else:
        results = load_all_player_stats()
        print(f"\nLoaded {len(results)} files")

    verify_load()
```

### 3. Test the Script

```bash
# Set database URL
export DATABASE_URL="postgresql://..."

# Load your CSV from Week 1
python scripts/load_player_stats_to_railway.py data/nba/player_stats_2025_26.csv

# Verify in database
psql $DATABASE_URL -c "SELECT player_name, ppg FROM nba_player_stats ORDER BY ppg DESC LIMIT 5;"
```

### 4. Create Useful Queries

Create `team/vansheeka/work/notes/player-stats-queries.md`:

```markdown
# Useful Player Stats Queries

## Best Player Per Team

```sql
SELECT DISTINCT ON (team_abbr)
    team_abbr, player_name, ppg
FROM nba_player_stats
WHERE season = '2025-26'
ORDER BY team_abbr, ppg DESC;
```

## Team's Total Star Power

```sql
SELECT
    team_abbr,
    SUM(ppg) as total_ppg,
    COUNT(*) as players,
    AVG(ppg) as avg_ppg
FROM nba_player_stats
WHERE season = '2025-26'
GROUP BY team_abbr
ORDER BY total_ppg DESC;
```

## Players with High Plus/Minus

```sql
SELECT player_name, team_abbr, ppg, plus_minus
FROM nba_player_stats
WHERE season = '2025-26' AND games_played >= 20
ORDER BY plus_minus DESC
LIMIT 20;
```

## Join with Matches

```sql
-- Get star players for upcoming games
SELECT
    m.home_team,
    m.away_team,
    hp.player_name as home_star,
    hp.ppg as home_star_ppg,
    ap.player_name as away_star,
    ap.ppg as away_star_ppg
FROM sportsbook_matches m
-- This needs team_abbr mapping...
```
```

---

## Done Checklist

- [ ] Script created at `scripts/load_player_stats_to_railway.py`
- [ ] Handles duplicate players (UPSERT)
- [ ] Logs inserted vs updated counts
- [ ] Verification queries work
- [ ] Data visible in Railway DB
- [ ] Useful queries documented

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the loader script
2. Show output (inserted/updated counts)
3. Query top scorers from database
4. Show players by team

**Duration:** 2 minutes max

---

## Resources

- Your Week 1 collection script output
- Dietrich's schema
- Miran's team stats loader (similar pattern)

---

## Who To Ask If Stuck

1. Dietrich — database schema questions
2. Miran — she's doing similar work
3. Tan — if connection issues
