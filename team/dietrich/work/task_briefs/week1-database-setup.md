# Week 1: Database Setup

**Owner:** Dietrich
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL — everyone depends on this

---

## Your Role

You own the Railway PostgreSQL database. Everyone gives YOU formatted CSVs, you load them. You don't chase data — they bring it to you in the right format.

---

## This Week's Deliverables

### 1. Create All Database Tables

Run these in Railway PostgreSQL:

```sql
-- Sportsbook matches
CREATE TABLE sportsbook_matches (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    sport VARCHAR(50) DEFAULT 'basketball_nba',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_matches_time ON sportsbook_matches(commence_time);
CREATE INDEX idx_matches_teams ON sportsbook_matches(home_team, away_team);

-- Sportsbook odds
CREATE TABLE sportsbook_odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES sportsbook_matches(id),
    bookmaker VARCHAR(50) NOT NULL,
    home_odds DECIMAL(6,3) NOT NULL,
    away_odds DECIMAL(6,3) NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_odds_match ON sportsbook_odds(match_id);

-- NBA team stats
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
    opp_ppg DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_name, season)
);

-- NBA player stats
CREATE TABLE nba_player_stats (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_abbr VARCHAR(10),
    season VARCHAR(10) NOT NULL,
    games_played INTEGER,
    ppg DECIMAL(4,1),
    rpg DECIMAL(4,1),
    apg DECIMAL(4,1),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, season)
);
```

### 2. Create CSV Loading Script

Create `scripts/load_csv_to_railway.py`:

```python
"""Load formatted CSVs into Railway PostgreSQL."""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys

def get_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def load_sportsbook_matches(csv_path: str):
    """Load matches CSV. Expected columns: external_id, home_team, away_team, commence_time"""
    df = pd.read_csv(csv_path)
    conn = get_connection()
    cur = conn.cursor()

    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO sportsbook_matches (external_id, home_team, away_team, commence_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING
            """, (row['external_id'], row['home_team'], row['away_team'], row['commence_time']))
            inserted += cur.rowcount
        except Exception as e:
            print(f"Error: {e}")

    conn.commit()
    print(f"Loaded {inserted} matches")
    conn.close()

def load_sportsbook_odds(csv_path: str):
    """Load odds CSV. Expected columns: external_id, bookmaker, home_odds, away_odds"""
    df = pd.read_csv(csv_path)
    conn = get_connection()
    cur = conn.cursor()

    inserted = 0
    for _, row in df.iterrows():
        # Get match_id from external_id
        cur.execute("SELECT id FROM sportsbook_matches WHERE external_id = %s", (row['external_id'],))
        result = cur.fetchone()
        if not result:
            continue
        match_id = result[0]

        cur.execute("""
            INSERT INTO sportsbook_odds (match_id, bookmaker, home_odds, away_odds)
            VALUES (%s, %s, %s, %s)
        """, (match_id, row['bookmaker'], row['home_odds'], row['away_odds']))
        inserted += 1

    conn.commit()
    print(f"Loaded {inserted} odds records")
    conn.close()

def load_nba_team_stats(csv_path: str):
    """Load team stats CSV."""
    df = pd.read_csv(csv_path)
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO nba_team_stats (team_name, team_abbr, season, games_played, wins, losses, win_pct, ppg, opp_ppg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (team_name, season) DO UPDATE SET
                games_played = EXCLUDED.games_played,
                wins = EXCLUDED.wins,
                losses = EXCLUDED.losses,
                win_pct = EXCLUDED.win_pct,
                ppg = EXCLUDED.ppg,
                opp_ppg = EXCLUDED.opp_ppg,
                updated_at = CURRENT_TIMESTAMP
        """, (row['team_name'], row.get('team_abbr'), row['season'],
              row['games_played'], row['wins'], row['losses'],
              row['win_pct'], row['ppg'], row.get('opp_ppg')))

    conn.commit()
    print(f"Loaded {len(df)} team stats")
    conn.close()

def load_nba_player_stats(csv_path: str):
    """Load player stats CSV."""
    df = pd.read_csv(csv_path)
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO nba_player_stats (player_name, team_abbr, season, games_played, ppg, rpg, apg)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_name, season) DO UPDATE SET
                team_abbr = EXCLUDED.team_abbr,
                games_played = EXCLUDED.games_played,
                ppg = EXCLUDED.ppg,
                rpg = EXCLUDED.rpg,
                apg = EXCLUDED.apg,
                updated_at = CURRENT_TIMESTAMP
        """, (row['player_name'], row['team_abbr'], row['season'],
              row['games_played'], row['ppg'], row['rpg'], row['apg']))

    conn.commit()
    print(f"Loaded {len(df)} player stats")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python load_csv_to_railway.py <type> <csv_path>")
        print("Types: matches, odds, team_stats, player_stats")
        sys.exit(1)

    data_type = sys.argv[1]
    csv_path = sys.argv[2]

    loaders = {
        'matches': load_sportsbook_matches,
        'odds': load_sportsbook_odds,
        'team_stats': load_nba_team_stats,
        'player_stats': load_nba_player_stats,
    }

    if data_type in loaders:
        loaders[data_type](csv_path)
    else:
        print(f"Unknown type: {data_type}")
```

### 3. Document CSV Formats

Create `docs/reference/csv-formats.md` — tell people EXACTLY what columns you need:

```markdown
# CSV Formats for Database Loading

## sportsbook_matches.csv
| Column | Type | Required | Example |
|--------|------|----------|---------|
| external_id | string | YES | "nba_20260210_lal_bos" |
| home_team | string | YES | "Los Angeles Lakers" |
| away_team | string | YES | "Boston Celtics" |
| commence_time | datetime | YES | "2026-02-10 19:00:00" |

## sportsbook_odds.csv
| Column | Type | Required | Example |
|--------|------|----------|---------|
| external_id | string | YES | "nba_20260210_lal_bos" |
| bookmaker | string | YES | "fanduel" |
| home_odds | decimal | YES | 1.95 |
| away_odds | decimal | YES | 2.05 |

## nba_team_stats.csv
| Column | Type | Required | Example |
|--------|------|----------|---------|
| team_name | string | YES | "Los Angeles Lakers" |
| team_abbr | string | NO | "LAL" |
| season | string | YES | "2025-26" |
| games_played | int | YES | 45 |
| wins | int | YES | 28 |
| losses | int | YES | 17 |
| win_pct | decimal | YES | 0.622 |
| ppg | decimal | YES | 112.5 |
| opp_ppg | decimal | NO | 108.3 |

## nba_player_stats.csv
| Column | Type | Required | Example |
|--------|------|----------|---------|
| player_name | string | YES | "LeBron James" |
| team_abbr | string | YES | "LAL" |
| season | string | YES | "2025-26" |
| games_played | int | YES | 40 |
| ppg | decimal | YES | 25.3 |
| rpg | decimal | YES | 7.8 |
| apg | decimal | YES | 8.1 |
```

---

## Who You Work With

| Person | What They Give You | When |
|--------|-------------------|------|
| Alfie | sportsbook_matches.csv, sportsbook_odds.csv | By Wed |
| Miran | Confirms CSVs match your schema | By Wed |
| Vansheeka | Team name list (for validation) | By Tue |
| Max | Runs validation after you load | After load |

**Your job:** Load what they give you. If CSV is wrong format, send it back.

---

## Done Checklist

- [ ] All 4 tables created in Railway
- [ ] Loading script works for all 4 data types
- [ ] CSV format documentation published
- [ ] At least one test load completed
- [ ] Max has run validation on loaded data

---

## Thursday Presentation (2 min)

1. Show tables exist: `\dt` in psql
2. Run loading script on a sample CSV
3. Query to show data: `SELECT * FROM sportsbook_matches LIMIT 5`
4. Confirm Max validated the data
