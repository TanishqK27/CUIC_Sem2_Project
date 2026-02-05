# Task: Load NBA Team Stats to Railway DB

**Owner:** Miran
**Deadline:** Feb 19 (Week 2)
**Priority:** Medium — models need this data in DB

---

## What You're Building

A script that loads the team stats CSV files into Dietrich's Railway PostgreSQL database.

---

## Why This Matters

CSV files are fine for quick analysis, but models and backtester need data in the database. This makes team stats available to everyone's queries.

---

## Exactly What You Must Deliver

### 1. Understand Dietrich's Schema

Dietrich will create this table (from his Task 02):

```sql
CREATE TABLE nba_team_stats (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbr VARCHAR(10),
    season VARCHAR(10) NOT NULL,
    games_played INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_pct DECIMAL(4,3),
    ppg DECIMAL(5,2),
    rpg DECIMAL(5,2),
    apg DECIMAL(5,2),
    opp_ppg DECIMAL(5,2),
    net_rating DECIMAL(5,2),
    fg_pct DECIMAL(4,3),
    fg3_pct DECIMAL(4,3),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_name, season)
);
```

### 2. Create Loading Script

Create `scripts/load_team_stats_to_railway.py`:

```python
"""Load NBA team stats CSV to Railway PostgreSQL."""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from pathlib import Path

def get_connection():
    """Get Railway database connection."""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_team_stats(csv_path: str) -> dict:
    """
    Load team stats from CSV into Railway DB.

    Args:
        csv_path: Path to team stats CSV

    Returns:
        Summary of operation
    """
    print(f"Loading {csv_path}...")

    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"  Read {len(df)} rows")

    # Map CSV columns to database columns
    # Adjust based on actual CSV column names
    column_mapping = {
        'team_name': 'team_name',
        'season': 'season',
        'games_played': 'games_played',
        'wins': 'wins',
        'losses': 'losses',
        'win_pct': 'win_pct',
        'ppg': 'ppg',
        'rpg': 'rpg',
        'apg': 'apg',
        'opp_ppg': 'opp_ppg',
        'net_rating': 'net_rating',
        'fg_pct': 'fg_pct',
        'fg3_pct': 'fg3_pct',
    }

    # Only keep columns that exist in CSV
    available_cols = [c for c in column_mapping.keys() if c in df.columns]
    df = df[available_cols].rename(columns={k: column_mapping[k] for k in available_cols})

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
                INSERT INTO nba_team_stats (team_name, season, games_played, wins, losses,
                    win_pct, ppg, rpg, apg, opp_ppg, net_rating, fg_pct, fg3_pct)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (team_name, season)
                DO UPDATE SET
                    games_played = EXCLUDED.games_played,
                    wins = EXCLUDED.wins,
                    losses = EXCLUDED.losses,
                    win_pct = EXCLUDED.win_pct,
                    ppg = EXCLUDED.ppg,
                    rpg = EXCLUDED.rpg,
                    apg = EXCLUDED.apg,
                    opp_ppg = EXCLUDED.opp_ppg,
                    net_rating = EXCLUDED.net_rating,
                    fg_pct = EXCLUDED.fg_pct,
                    fg3_pct = EXCLUDED.fg3_pct,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) as inserted
            """, (
                row.get('team_name'),
                row.get('season'),
                row.get('games_played'),
                row.get('wins'),
                row.get('losses'),
                row.get('win_pct'),
                row.get('ppg'),
                row.get('rpg'),
                row.get('apg'),
                row.get('opp_ppg'),
                row.get('net_rating'),
                row.get('fg_pct'),
                row.get('fg3_pct'),
            ))

            result = cursor.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1

        except Exception as e:
            print(f"  Error loading {row.get('team_name')}: {e}")
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

def load_all_team_stats(directory: str = "data/nba") -> list:
    """Load all team stats CSVs in directory."""
    results = []
    for path in Path(directory).glob("team_stats_*.csv"):
        result = load_team_stats(str(path))
        results.append(result)
    return results

def verify_load():
    """Check data was loaded correctly."""
    conn = get_connection()

    # Count rows
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM nba_team_stats")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows in nba_team_stats: {count}")

    # Show sample
    cursor.execute("""
        SELECT team_name, season, wins, losses, win_pct, ppg
        FROM nba_team_stats
        ORDER BY win_pct DESC
        LIMIT 5
    """)

    print("\nTop 5 teams by win %:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[2]}-{row[3]} ({row[4]:.3f}) - {row[5]} PPG")

    conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Load specific file
        load_team_stats(sys.argv[1])
    else:
        # Load all files
        results = load_all_team_stats()
        print(f"\nLoaded {len(results)} files")

    verify_load()
```

### 3. Test the Script

```bash
# Make sure DATABASE_URL is set
export DATABASE_URL="postgresql://..."

# Load your CSV from Week 1
python scripts/load_team_stats_to_railway.py data/nba/team_stats_2025_26.csv

# Verify in database
psql $DATABASE_URL -c "SELECT team_name, win_pct FROM nba_team_stats ORDER BY win_pct DESC LIMIT 5;"
```

### 4. Create Verification Notebook

Create `tools/verify_team_stats.ipynb`:

```python
# Cell 1: Connect and verify
import pandas as pd
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])

# Count
count = pd.read_sql("SELECT COUNT(*) FROM nba_team_stats", engine).iloc[0, 0]
print(f"Total teams in DB: {count}")

# Cell 2: Show standings
query = """
    SELECT team_name, wins, losses, win_pct, ppg, opp_ppg, net_rating
    FROM nba_team_stats
    WHERE season = '2025-26'
    ORDER BY win_pct DESC
"""
pd.read_sql(query, engine)

# Cell 3: Join with matches
query = """
    SELECT
        m.home_team,
        m.away_team,
        h.win_pct as home_win_pct,
        a.win_pct as away_win_pct
    FROM sportsbook_matches m
    JOIN nba_team_stats h ON m.home_team = h.team_name
    JOIN nba_team_stats a ON m.away_team = a.team_name
    WHERE h.season = '2025-26'
    LIMIT 10
"""
pd.read_sql(query, engine)
```

---

## Done Checklist

- [ ] Script created at `scripts/load_team_stats_to_railway.py`
- [ ] Handles duplicate teams (UPSERT)
- [ ] Logs inserted vs updated counts
- [ ] Verification notebook created
- [ ] Data visible in Railway DB
- [ ] Can JOIN with sportsbook_matches table

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the loader script
2. Show output (inserted/updated counts)
3. Query the database for top teams
4. Show a JOIN with matches table

**Duration:** 2 minutes max

---

## Resources

- Your Week 1 collection script output
- Dietrich's schema: `team/dietrich/work/task_briefs/02-railway-db-nba-stats-schema.md`
- psycopg2 docs: https://www.psycopg.org/docs/

---

## Who To Ask If Stuck

1. Dietrich — database schema questions
2. Check if table exists: `\d nba_team_stats` in psql
3. Vansheeka — she's doing similar work with player stats
4. Tan — if connection issues
