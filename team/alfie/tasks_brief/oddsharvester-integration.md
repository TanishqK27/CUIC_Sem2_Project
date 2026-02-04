# OddsHarvester Integration Brief

## What is OddsHarvester?

A free, open-source Python tool that scrapes sports betting odds from oddsportal.com. It collects odds from 30-50 bookmakers across multiple sports and markets.

**GitHub:** https://github.com/jordantete/OddsHarvester

## End Goal

Build a data pipeline that:
1. **Collects** historical NBA odds (2021-present) using OddsHarvester
2. **Stores** the data in a SQLite database (`sports_odds.db`)
3. **Queries** the data easily from Jupyter notebooks via a `SportsOddsRepository`

This replaces The Odds API (which has a 500 request/month limit) with unlimited free scraping.

## What Success Looks Like

- A SQLite database with ~5,000 NBA matches and ~7-10 million odds rows
- A Python class that lets you do:
  ```python
  from cuic_quant.database.repositories import SportsOddsRepository

  repo = SportsOddsRepository("data/sports_odds.db")
  df = repo.get_odds_df(league="nba", start_date="2024-01-01")
  ```
- Data that can be joined with Polymarket data for cross-platform analysis

## Example Steps

1. Install OddsHarvester and test the CLI works
2. Design database tables (matches, odds_snapshots, bookmakers)
3. Create a wrapper class that calls the CLI and parses JSON output
4. Create a collector class that runs scraping jobs and saves to database
5. Create a repository class with DataFrame query methods
6. Run historical backfill for NBA seasons

## Resources

- Full plan: `team/tan/plans_for_team_tasks/oddsharvester-integration-plan.md`
- Existing Polymarket collector to reference: `src/cuic_quant/collector/polymarket_collector.py`
- Existing repository pattern: `src/cuic_quant/database/repositories/market_repo.py`

## Notes

- Work with Max on this - split the work between you
- Ask Tan if you get stuck on architecture decisions
- Mirror the Polymarket infrastructure patterns where possible
