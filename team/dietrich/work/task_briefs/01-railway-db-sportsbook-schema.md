# Task: Railway DB Schema for Sportsbook Odds

**Owner:** Dietrich
**Deadline:** Feb 12 (Week 1)
**Priority:** High — blocks Alfie and Max's data loading

---

## What You're Building

Create the database tables in Railway PostgreSQL to store historical sportsbook odds data from OddsHarvester. This data will be used alongside existing Polymarket data for cross-platform analysis.

---

## Why This Matters

Without proper tables, we can't store the odds data. Without stored data, no one can build models. You're unblocking the entire data pipeline.

---

## Exactly What You Must Deliver

### 1. Database Tables

Create tables in Railway DB with at minimum:

```sql
-- Suggested schema (adjust as needed)
CREATE TABLE sportsbook_matches (
    id SERIAL PRIMARY KEY,
    match_date DATE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    home_score INT,
    away_score INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sportsbook_odds (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES sportsbook_matches(id),
    bookmaker VARCHAR(100) NOT NULL,
    home_odds DECIMAL(10,4),
    away_odds DECIMAL(10,4),
    draw_odds DECIMAL(10,4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for common queries
CREATE INDEX idx_matches_date ON sportsbook_matches(match_date);
CREATE INDEX idx_odds_match ON sportsbook_odds(match_id);
```

### 2. Schema Documentation

Create `docs/reference/sportsbook-schema.md` with:
- Table descriptions
- Column descriptions and types
- Example INSERT statements
- Example SELECT queries
- How this joins with existing Polymarket tables

### 3. Working Proof

Demonstrate with:
- INSERT a few sample rows
- SELECT them back
- JOIN with existing price_snapshots table

---

## Done Checklist

- [ ] Tables created in Railway DB
- [ ] Proper indexes added
- [ ] Schema documented in `docs/reference/sportsbook-schema.md`
- [ ] Example INSERT working
- [ ] Example SELECT returns data
- [ ] Can JOIN with existing Polymarket data

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Connect to Railway DB
2. Run a SELECT on your new tables
3. Show a JOIN between sportsbook_odds and price_snapshots
4. Walk through the schema doc (30 seconds)

**Duration:** 2 minutes max

---

## Resources

- Existing schema: `docs/reference/database-guide.md`
- Connection info: `docs/guides/connecting-to-database.md`
- OddsHarvester output format: Ask Alfie or check https://github.com/jordantete/OddsHarvester

---

## Who To Ask If Stuck

1. Check OddsHarvester docs for data format
2. Ask Alfie what columns the scraped data has
3. Tan for architecture decisions
