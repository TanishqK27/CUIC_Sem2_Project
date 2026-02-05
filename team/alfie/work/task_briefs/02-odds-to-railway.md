# Task: Load Sportsbook Odds to Railway DB

**Owner:** Alfie
**Deadline:** Feb 19 (Week 2)
**Priority:** High — needed for backtesting

---

## What You're Building

A script that takes the OddsHarvester JSON output and loads it into Dietrich's Railway PostgreSQL database.

---

## Why This Matters

Raw JSON files don't scale. We need odds in the database so:
- Backtester can query historical odds
- We can JOIN with Polymarket data
- Multiple team members can access the same data

---

## Exactly What You Must Deliver

### 1. Understand Dietrich's Schema

Dietrich will create these tables (from his Task 01):

```sql
-- sportsbook_matches
CREATE TABLE sportsbook_matches (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    sport VARCHAR(50) DEFAULT 'basketball_nba',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- sportsbook_odds
CREATE TABLE sportsbook_odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES sportsbook_matches(id),
    bookmaker VARCHAR(50) NOT NULL,
    home_odds DECIMAL(6,3),
    away_odds DECIMAL(6,3),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Create Loading Script

Create `scripts/load_odds_to_railway.py`:

```python
"""Load OddsHarvester JSON data into Railway PostgreSQL."""

import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from pathlib import Path
import os

def get_connection():
    """Get Railway PostgreSQL connection."""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def parse_odds_json(json_path: str) -> tuple[list, list]:
    """
    Parse OddsHarvester JSON into database rows.

    Returns:
        (matches, odds) - lists of tuples ready for insert
    """
    with open(json_path) as f:
        data = json.load(f)

    matches = []
    odds = []

    for game in data:
        match = (
            game['id'],                    # external_id
            game['home_team'],             # home_team
            game['away_team'],             # away_team
            game['commence_time'],         # commence_time
            'basketball_nba'               # sport
        )
        matches.append(match)

        # Extract odds from each bookmaker
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':  # Moneyline odds
                    outcomes = {o['name']: o['price'] for o in market['outcomes']}
                    home_price = outcomes.get(game['home_team'])
                    away_price = outcomes.get(game['away_team'])

                    if home_price and away_price:
                        odd = (
                            game['id'],         # external_id (to link later)
                            bookmaker['key'],   # bookmaker
                            home_price,         # home_odds
                            away_price          # away_odds
                        )
                        odds.append(odd)

    return matches, odds

def insert_matches(conn, matches: list) -> dict:
    """
    Insert matches and return mapping of external_id -> db id.
    Handles duplicates by skipping.
    """
    cursor = conn.cursor()
    id_map = {}

    for match in matches:
        try:
            cursor.execute("""
                INSERT INTO sportsbook_matches
                    (external_id, home_team, away_team, commence_time, sport)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING
                RETURNING id, external_id
            """, match)

            result = cursor.fetchone()
            if result:
                id_map[result[1]] = result[0]
            else:
                # Get existing id
                cursor.execute(
                    "SELECT id FROM sportsbook_matches WHERE external_id = %s",
                    (match[0],)
                )
                id_map[match[0]] = cursor.fetchone()[0]

        except Exception as e:
            print(f"Error inserting match {match[0]}: {e}")
            continue

    conn.commit()
    return id_map

def insert_odds(conn, odds: list, id_map: dict) -> int:
    """
    Insert odds rows.

    Returns:
        Number of rows inserted
    """
    cursor = conn.cursor()
    inserted = 0

    for odd in odds:
        external_id, bookmaker, home_odds, away_odds = odd
        match_id = id_map.get(external_id)

        if not match_id:
            continue

        try:
            cursor.execute("""
                INSERT INTO sportsbook_odds
                    (match_id, bookmaker, home_odds, away_odds)
                VALUES (%s, %s, %s, %s)
            """, (match_id, bookmaker, home_odds, away_odds))
            inserted += 1
        except Exception as e:
            print(f"Error inserting odds for match {external_id}: {e}")
            continue

    conn.commit()
    return inserted

def load_odds_file(json_path: str) -> dict:
    """
    Load a single odds JSON file into Railway DB.

    Returns:
        Summary stats
    """
    print(f"Loading {json_path}...")

    matches, odds = parse_odds_json(json_path)
    print(f"  Parsed {len(matches)} matches, {len(odds)} odds records")

    conn = get_connection()
    try:
        id_map = insert_matches(conn, matches)
        print(f"  Inserted/found {len(id_map)} matches")

        inserted = insert_odds(conn, odds, id_map)
        print(f"  Inserted {inserted} odds records")

        return {
            'file': json_path,
            'matches': len(matches),
            'odds_inserted': inserted
        }
    finally:
        conn.close()

def load_all_odds(directory: str = "data/odds") -> list:
    """Load all JSON files in directory."""
    results = []
    for path in Path(directory).glob("*.json"):
        result = load_odds_file(str(path))
        results.append(result)
    return results

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Load specific file
        load_odds_file(sys.argv[1])
    else:
        # Load all files in default directory
        results = load_all_odds()
        print(f"\nLoaded {len(results)} files")
        print(f"Total matches: {sum(r['matches'] for r in results)}")
        print(f"Total odds: {sum(r['odds_inserted'] for r in results)}")
```

### 3. Test the Script

```bash
# Make sure DATABASE_URL is set
export DATABASE_URL="postgresql://..."  # Get from Dietrich

# Load sample file
python scripts/load_odds_to_railway.py data/nba_odds_sample.json

# Verify in database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM sportsbook_matches;"
psql $DATABASE_URL -c "SELECT * FROM sportsbook_odds LIMIT 5;"
```

### 4. Create Test Notebook

Create `tools/verify_odds_load.ipynb`:

```python
# Cell 1: Connect and check
import pandas as pd
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])

# Count records
print("Matches:", pd.read_sql("SELECT COUNT(*) FROM sportsbook_matches", engine).iloc[0,0])
print("Odds:", pd.read_sql("SELECT COUNT(*) FROM sportsbook_odds", engine).iloc[0,0])

# Cell 2: Sample data
query = """
SELECT
    m.home_team,
    m.away_team,
    m.commence_time,
    o.bookmaker,
    o.home_odds,
    o.away_odds
FROM sportsbook_matches m
JOIN sportsbook_odds o ON m.id = o.match_id
ORDER BY m.commence_time DESC
LIMIT 20
"""
pd.read_sql(query, engine)

# Cell 3: Odds by bookmaker
query = """
SELECT bookmaker, COUNT(*) as count
FROM sportsbook_odds
GROUP BY bookmaker
ORDER BY count DESC
"""
pd.read_sql(query, engine)
```

---

## Done Checklist

- [ ] Script created at `scripts/load_odds_to_railway.py`
- [ ] Parses OddsHarvester JSON correctly
- [ ] Handles duplicate matches (ON CONFLICT)
- [ ] Logs progress and errors
- [ ] Test notebook verifies data loaded
- [ ] At least 100 odds records in database

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the loader script on a JSON file
2. Show the output (how many inserted)
3. Query the database to show data
4. Show odds from different bookmakers

**Duration:** 2 minutes max

---

## Resources

- Dietrich's schema: `team/dietrich/work/task_briefs/01-railway-db-sportsbook-schema.md`
- psycopg2 docs: https://www.psycopg.org/docs/
- Railway connection guide: `docs/guides/connecting-to-database.md`

---

## Who To Ask If Stuck

1. Dietrich — database schema questions
2. Check your Week 1 OddsHarvester output format
3. Tan — if database connection issues
