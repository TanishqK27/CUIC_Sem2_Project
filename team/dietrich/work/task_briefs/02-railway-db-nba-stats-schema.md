# Task: Railway DB Schema for NBA Stats

**Owner:** Dietrich
**Deadline:** Feb 12 (Week 1)
**Priority:** High — blocks Miran and Vansheeka's data loading

---

## What You're Building

Create database tables in Railway PostgreSQL to store NBA team and player statistics from the `nba_api` library. This data will be used as features for prediction models.

---

## Why This Matters

NBA stats (team records, player performance) are key features for predicting game outcomes. Models need this data joined with odds data.

---

## Exactly What You Must Deliver

### 1. Database Tables

Create tables for team and player stats:

```sql
-- Team stats per game
CREATE TABLE nba_team_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    game_date DATE NOT NULL,
    team_id INT NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    is_home BOOLEAN NOT NULL,
    pts INT,
    reb INT,
    ast INT,
    stl INT,
    blk INT,
    fg_pct DECIMAL(5,3),
    fg3_pct DECIMAL(5,3),
    ft_pct DECIMAL(5,3),
    plus_minus INT,
    win BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Player stats per game
CREATE TABLE nba_player_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    game_date DATE NOT NULL,
    player_id INT NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    team_id INT NOT NULL,
    minutes INT,
    pts INT,
    reb INT,
    ast INT,
    stl INT,
    blk INT,
    fg_pct DECIMAL(5,3),
    fg3_pct DECIMAL(5,3),
    plus_minus INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_team_stats_date ON nba_team_stats(game_date);
CREATE INDEX idx_team_stats_team ON nba_team_stats(team_id);
CREATE INDEX idx_player_stats_date ON nba_player_stats(game_date);
CREATE INDEX idx_player_stats_player ON nba_player_stats(player_id);
```

### 2. Schema Documentation

Create `docs/reference/nba-stats-schema.md` with:
- Table descriptions
- Column descriptions
- Example queries
- How to join with sportsbook_odds and price_snapshots

### 3. Working Proof

- INSERT sample rows
- SELECT them back
- JOIN with sportsbook_matches on date + team

---

## Done Checklist

- [ ] Team stats table created
- [ ] Player stats table created
- [ ] Indexes added
- [ ] Schema documented in `docs/reference/nba-stats-schema.md`
- [ ] Example INSERT/SELECT working
- [ ] Can JOIN with sportsbook and Polymarket tables

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. SELECT from nba_team_stats
2. JOIN team stats with sportsbook_odds for same game
3. Quick walkthrough of schema doc

**Duration:** 2 minutes max

---

## Resources

- `nba_api` docs: https://github.com/swar/nba_api
- Ask Miran/Vansheeka what columns they're pulling

---

## Who To Ask If Stuck

1. Miran — what team stats columns does nba_api provide?
2. Vansheeka — what player stats columns?
3. Tan — architecture decisions
