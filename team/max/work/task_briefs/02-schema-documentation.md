# Task: Database Schema Documentation

**Owner:** Max
**Deadline:** Feb 19 (Week 2)
**Priority:** Medium — helps everyone understand data

---

## What You're Building

Complete documentation of every table in Railway DB: what columns exist, what they mean, how tables relate to each other.

---

## Why This Matters

New team members shouldn't have to reverse-engineer the database. Clear documentation means anyone can write queries without asking Dietrich every time.

---

## Exactly What You Must Deliver

### 1. Schema Documentation

Create `docs/reference/database-schema.md`:

```markdown
# Database Schema Reference

## Overview

Our Railway PostgreSQL database contains data from:
- **Polymarket:** Prediction market probabilities
- **Sportsbooks:** Betting odds from FanDuel, DraftKings, etc.
- **NBA Stats:** Team and player statistics

## Entity Relationship Diagram

```
┌──────────────────────┐      ┌──────────────────────┐
│  sportsbook_matches  │      │   sportsbook_odds    │
├──────────────────────┤      ├──────────────────────┤
│ id (PK)              │──┐   │ id (PK)              │
│ external_id          │  │   │ match_id (FK)────────┼──┘
│ home_team            │  └───│ bookmaker            │
│ away_team            │      │ home_odds            │
│ commence_time        │      │ away_odds            │
│ sport                │      │ scraped_at           │
│ created_at           │      └──────────────────────┘
└──────────────────────┘

┌──────────────────────┐      ┌──────────────────────┐
│    nba_team_stats    │      │   nba_player_stats   │
├──────────────────────┤      ├──────────────────────┤
│ id (PK)              │      │ id (PK)              │
│ team_name            │      │ player_name          │
│ season               │      │ team_name (FK?)      │
│ games_played         │      │ season               │
│ wins                 │      │ games_played         │
│ losses               │      │ ppg                  │
│ win_pct              │      │ rpg                  │
│ ppg                  │      │ apg                  │
│ opp_ppg              │      │ ...                  │
│ ...                  │      └──────────────────────┘
└──────────────────────┘
```

## Tables

### sportsbook_matches

Stores information about each game.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| external_id | VARCHAR(100) | ID from scraper (unique) | "nba_20260210_lal_bos" |
| home_team | VARCHAR(100) | Home team name | "Los Angeles Lakers" |
| away_team | VARCHAR(100) | Away team name | "Boston Celtics" |
| commence_time | TIMESTAMP | Game start time (UTC) | 2026-02-10 19:00:00 |
| sport | VARCHAR(50) | Sport type | "basketball_nba" |
| created_at | TIMESTAMP | When record was created | 2026-02-09 14:30:00 |

**Indexes:**
- `external_id` (unique)
- `commence_time` (for date range queries)

**Common Queries:**
```sql
-- Get upcoming games
SELECT * FROM sportsbook_matches
WHERE commence_time > NOW()
ORDER BY commence_time;

-- Find games by team
SELECT * FROM sportsbook_matches
WHERE home_team ILIKE '%Lakers%' OR away_team ILIKE '%Lakers%';
```

---

### sportsbook_odds

Stores betting odds from each sportsbook for each match.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| match_id | INTEGER | FK to sportsbook_matches | 42 |
| bookmaker | VARCHAR(50) | Sportsbook name | "fanduel" |
| home_odds | DECIMAL(6,3) | Decimal odds for home | 1.952 |
| away_odds | DECIMAL(6,3) | Decimal odds for away | 2.050 |
| scraped_at | TIMESTAMP | When odds were collected | 2026-02-09 14:30:00 |

**Bookmaker Values:**
- `fanduel`
- `draftkings`
- `betmgm`
- `caesars`
- `pointsbet`

**Common Queries:**
```sql
-- Get best odds for a match
SELECT bookmaker, home_odds, away_odds
FROM sportsbook_odds
WHERE match_id = 42
ORDER BY home_odds DESC;

-- Compare odds across bookmakers
SELECT
    m.home_team,
    o.bookmaker,
    o.home_odds,
    1.0 / o.home_odds as implied_prob
FROM sportsbook_matches m
JOIN sportsbook_odds o ON m.id = o.match_id
WHERE m.id = 42;
```

---

### nba_team_stats

Team-level statistics for the NBA season.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| team_name | VARCHAR(100) | Full team name | "Los Angeles Lakers" |
| team_abbr | VARCHAR(10) | Abbreviation | "LAL" |
| season | VARCHAR(10) | Season identifier | "2025-26" |
| games_played | INTEGER | Games played | 45 |
| wins | INTEGER | Total wins | 28 |
| losses | INTEGER | Total losses | 17 |
| win_pct | DECIMAL(4,3) | Win percentage | 0.622 |
| ppg | DECIMAL(5,2) | Points per game | 112.5 |
| opp_ppg | DECIMAL(5,2) | Opponent PPG | 108.3 |
| updated_at | TIMESTAMP | Last update | 2026-02-09 |

**Common Queries:**
```sql
-- Get current standings
SELECT team_name, wins, losses, win_pct
FROM nba_team_stats
WHERE season = '2025-26'
ORDER BY win_pct DESC;

-- Get offensive/defensive ratings
SELECT
    team_name,
    ppg as offense,
    opp_ppg as defense,
    ppg - opp_ppg as net_rating
FROM nba_team_stats
WHERE season = '2025-26'
ORDER BY net_rating DESC;
```

---

### nba_player_stats

Individual player statistics.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | SERIAL | Primary key | 1 |
| player_name | VARCHAR(100) | Player name | "LeBron James" |
| team_name | VARCHAR(100) | Team | "Los Angeles Lakers" |
| season | VARCHAR(10) | Season | "2025-26" |
| games_played | INTEGER | Games played | 40 |
| ppg | DECIMAL(4,1) | Points per game | 25.3 |
| rpg | DECIMAL(4,1) | Rebounds per game | 7.8 |
| apg | DECIMAL(4,1) | Assists per game | 8.1 |
| fg_pct | DECIMAL(4,3) | Field goal % | 0.512 |
| updated_at | TIMESTAMP | Last update | 2026-02-09 |

---

## Joins

### Match + Odds + Probability
```sql
SELECT
    m.home_team,
    m.away_team,
    m.commence_time,
    o.bookmaker,
    o.home_odds,
    1.0 / o.home_odds / (1.0/o.home_odds + 1.0/o.away_odds) as sb_home_prob
FROM sportsbook_matches m
JOIN sportsbook_odds o ON m.id = o.match_id
WHERE m.commence_time > NOW()
ORDER BY m.commence_time, o.bookmaker;
```

### Match + Team Stats
```sql
SELECT
    m.home_team,
    m.away_team,
    h.win_pct as home_win_pct,
    a.win_pct as away_win_pct,
    h.win_pct - a.win_pct as win_pct_diff
FROM sportsbook_matches m
JOIN nba_team_stats h ON m.home_team = h.team_name
JOIN nba_team_stats a ON m.away_team = a.team_name
WHERE h.season = '2025-26' AND a.season = '2025-26';
```

## Data Sources

| Table | Source | Frequency |
|-------|--------|-----------|
| sportsbook_matches | OddsHarvester | Hourly |
| sportsbook_odds | OddsHarvester | Hourly |
| nba_team_stats | nba_api | Daily |
| nba_player_stats | nba_api | Daily |

## Connection

```python
import os
from sqlalchemy import create_engine

engine = create_engine(os.environ['DATABASE_URL'])
```

See `docs/guides/connecting-to-database.md` for full setup.
```

---

## Done Checklist

- [ ] Document created at `docs/reference/database-schema.md`
- [ ] All tables documented with columns
- [ ] Column types and descriptions accurate
- [ ] Example queries for each table
- [ ] ER diagram showing relationships
- [ ] Join examples included
- [ ] Verified against actual database

---

## What You Will Present (Thursday Feb 19)

**Walk through the doc:**
1. Show the ER diagram
2. Pick one table, explain columns
3. Run one of the example queries live
4. Show how to do a join

**Duration:** 2 minutes max

---

## Resources

- Ask Dietrich for table CREATE statements
- Query the database with `\d tablename` in psql
- SQLAlchemy inspection: `from sqlalchemy import inspect`

---

## Who To Ask If Stuck

1. Dietrich — he created the schemas
2. `psql $DATABASE_URL -c "\d"` to see tables
3. Tan — if schema seems wrong
