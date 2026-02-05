# Task: Sportsbook Query Example Notebook

**Owner:** Alfie
**Deadline:** Feb 26 (Week 3)
**Priority:** Medium — documentation for team

---

## What You're Building

A notebook showing how to query sportsbook data from Railway and compare it with Polymarket data.

---

## Why This Matters

This notebook is the "how to use the data" guide for the team. Anyone building models or strategies needs to know how to get odds data. Your notebook is their reference.

---

## Exactly What You Must Deliver

### 1. Query Example Notebook

Create `tools/sportsbook_data_guide.ipynb`:

```python
# Cell 1: Introduction
"""
# Sportsbook Data Guide

This notebook shows how to query NBA odds data from Railway PostgreSQL.

**What you'll learn:**
1. Connect to Railway database
2. Query matches and odds
3. Compare sportsbook odds to Polymarket
4. Calculate implied probabilities
"""

# Cell 2: Setup
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta

# Connect to Railway
engine = create_engine(os.environ['DATABASE_URL'])

# Cell 3: Basic Queries
"""
## Basic Queries

### Get all matches
"""

matches = pd.read_sql("""
    SELECT id, home_team, away_team, commence_time, sport
    FROM sportsbook_matches
    ORDER BY commence_time DESC
    LIMIT 50
""", engine)

print(f"Total matches in DB: {len(matches)}")
matches.head(10)

# Cell 4: Get Odds for a Match
"""
### Get odds for specific matches
"""

def get_match_odds(home_team: str, away_team: str = None):
    """Get all odds for games involving home_team."""
    query = f"""
        SELECT
            m.home_team,
            m.away_team,
            m.commence_time,
            o.bookmaker,
            o.home_odds,
            o.away_odds,
            o.scraped_at
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
        WHERE m.home_team ILIKE '%{home_team}%'
        ORDER BY m.commence_time DESC, o.bookmaker
    """
    return pd.read_sql(query, engine)

# Example: Lakers odds
get_match_odds('Lakers').head(20)

# Cell 5: Compare Bookmakers
"""
## Compare Odds Across Bookmakers

Same game, different odds = arbitrage opportunity?
"""

def compare_bookmaker_odds(match_id: int):
    """Compare odds from all bookmakers for one match."""
    query = f"""
        SELECT
            m.home_team,
            m.away_team,
            o.bookmaker,
            o.home_odds,
            o.away_odds,
            -- Implied probability
            1.0 / o.home_odds as home_implied_prob,
            1.0 / o.away_odds as away_implied_prob,
            -- Vig (overround)
            (1.0/o.home_odds + 1.0/o.away_odds - 1) * 100 as vig_percent
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
        WHERE m.id = {match_id}
        ORDER BY o.home_odds DESC
    """
    return pd.read_sql(query, engine)

# Get odds comparison for first match
sample_match_id = matches.iloc[0]['id']
compare_bookmaker_odds(sample_match_id)

# Cell 6: Best Odds
"""
## Find Best Odds

For each match, find the bookmaker with best odds for each side.
"""

query = """
    WITH ranked_home AS (
        SELECT
            m.id,
            m.home_team,
            m.away_team,
            m.commence_time,
            o.bookmaker as best_home_book,
            o.home_odds as best_home_odds,
            ROW_NUMBER() OVER (PARTITION BY m.id ORDER BY o.home_odds DESC) as rn
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
    ),
    ranked_away AS (
        SELECT
            m.id,
            o.bookmaker as best_away_book,
            o.away_odds as best_away_odds,
            ROW_NUMBER() OVER (PARTITION BY m.id ORDER BY o.away_odds DESC) as rn
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
    )
    SELECT
        h.home_team,
        h.away_team,
        h.commence_time,
        h.best_home_book,
        h.best_home_odds,
        a.best_away_book,
        a.best_away_odds
    FROM ranked_home h
    JOIN ranked_away a ON h.id = a.id AND a.rn = 1
    WHERE h.rn = 1
    ORDER BY h.commence_time DESC
    LIMIT 20
"""

pd.read_sql(query, engine)

# Cell 7: Implied Probability Calculation
"""
## Converting Odds to Probability

Sportsbook decimal odds contain a "vig" (bookmaker margin).
We remove it to get true implied probability.
"""

def odds_to_probability(home_odds: float, away_odds: float) -> tuple:
    """
    Convert decimal odds to probability, removing vig.

    Args:
        home_odds: Decimal odds for home team
        away_odds: Decimal odds for away team

    Returns:
        (home_prob, away_prob) that sum to 1.0
    """
    # Raw implied probs (sum > 1 due to vig)
    home_implied = 1 / home_odds
    away_implied = 1 / away_odds
    total = home_implied + away_implied

    # Normalize to remove vig
    home_prob = home_implied / total
    away_prob = away_implied / total

    return home_prob, away_prob

# Example
home_p, away_p = odds_to_probability(1.95, 2.05)
print(f"Home: {home_p:.1%}, Away: {away_p:.1%}")

# Cell 8: Merge with Polymarket
"""
## Compare Sportsbook vs Polymarket

Join our odds data with Polymarket snapshots.
"""

# This query assumes Polymarket data exists in price_snapshots
# Adjust column names based on actual schema

query = """
    SELECT
        sb.home_team,
        sb.away_team,
        sb.commence_time,
        so.bookmaker,
        so.home_odds,
        -- Calculate sportsbook implied probability
        1.0 / so.home_odds / (1.0/so.home_odds + 1.0/so.away_odds) as sb_home_prob,
        -- Polymarket probability (from Dietrich's price_snapshots)
        -- pm.home_prob as pm_home_prob,
        -- Gap
        -- (sb_implied - pm.home_prob) as gap
    FROM sportsbook_matches sb
    JOIN sportsbook_odds so ON sb.id = so.match_id
    -- JOIN price_snapshots pm ON ...  -- need to match on game
    WHERE so.bookmaker = 'fanduel'  -- Pick one bookmaker
    ORDER BY sb.commence_time DESC
    LIMIT 50
"""

pd.read_sql(query, engine)

# Cell 9: Data Quality Check
"""
## Data Quality

Check for issues in our data.
"""

# Matches without odds
query = """
    SELECT COUNT(*)
    FROM sportsbook_matches m
    LEFT JOIN sportsbook_odds o ON m.id = o.match_id
    WHERE o.id IS NULL
"""
orphan_matches = pd.read_sql(query, engine).iloc[0, 0]
print(f"Matches without odds: {orphan_matches}")

# Bookmaker coverage
query = """
    SELECT
        bookmaker,
        COUNT(*) as odds_count,
        MIN(scraped_at) as first_scraped,
        MAX(scraped_at) as last_scraped
    FROM sportsbook_odds
    GROUP BY bookmaker
    ORDER BY odds_count DESC
"""
pd.read_sql(query, engine)

# Cell 10: Helper Functions
"""
## Helper Functions for Your Code

Copy these into your notebooks/scripts.
"""

def get_odds_for_game(home_team: str, game_date: str, bookmaker: str = 'fanduel'):
    """
    Get odds for a specific game.

    Args:
        home_team: Home team name (partial match OK)
        game_date: Date string like '2026-02-10'
        bookmaker: Which bookmaker to use

    Returns:
        DataFrame with odds
    """
    query = f"""
        SELECT *
        FROM sportsbook_matches m
        JOIN sportsbook_odds o ON m.id = o.match_id
        WHERE m.home_team ILIKE '%{home_team}%'
          AND DATE(m.commence_time) = '{game_date}'
          AND o.bookmaker = '{bookmaker}'
    """
    return pd.read_sql(query, engine)

def get_average_odds(match_id: int) -> tuple:
    """Get average odds across all bookmakers for a match."""
    query = f"""
        SELECT AVG(home_odds), AVG(away_odds)
        FROM sportsbook_odds
        WHERE match_id = {match_id}
    """
    result = pd.read_sql(query, engine)
    return result.iloc[0, 0], result.iloc[0, 1]
```

---

## Done Checklist

- [ ] Notebook created at `tools/sportsbook_data_guide.ipynb`
- [ ] All cells run without errors
- [ ] Basic queries documented (matches, odds)
- [ ] Bookmaker comparison example
- [ ] Implied probability calculation explained
- [ ] Helper functions provided for team use
- [ ] Data quality checks included

---

## What You Will Present (Thursday Feb 26)

**Live demo showing:**
1. Query matches from database
2. Compare odds across bookmakers
3. Show the implied probability calculation
4. Demonstrate one helper function

**Duration:** 2 minutes max

---

## Resources

- Your loading script from Week 2
- Dietrich's database schema
- Odds conversion guide: `docs/reference/sports-betting.md`

---

## Who To Ask If Stuck

1. Dietrich — database schema questions
2. Run your queries in psql first to debug
3. Tan — SQL optimization questions
