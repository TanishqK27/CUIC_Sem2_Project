# OddsHarvester Integration

## What is OddsHarvester?

A free, open-source Python tool that scrapes sports betting odds from oddsportal.com. It collects odds from 30-50 bookmakers across multiple sports and markets.

**GitHub:** https://github.com/jordantete/OddsHarvester

## End Goal

Build a data pipeline that:
1. **Collects** historical NBA odds (2021-present) using OddsHarvester
2. **Stores** the data in Dietrich's shared Railway PostgreSQL database
3. **Queries** the data easily from Jupyter notebooks alongside existing Polymarket data

This replaces The Odds API (which has a 500 request/month limit) with unlimited free scraping.

## What Success Looks Like

- Sports odds data integrated into the shared Railway database (~5,000 NBA matches)
- Data queryable alongside existing Polymarket data for cross-platform analysis
- Example query pattern:
  ```python
  # Connect to shared database (same as Polymarket data)
  df = query("SELECT * FROM sports_odds WHERE league = 'nba' AND date > '2024-01-01'")
  ```

## Example Steps

1. Install OddsHarvester and test the CLI works
2. Design database tables (matches, odds_snapshots, bookmakers)
3. Create a wrapper class that calls the CLI and parses JSON output
4. Create a collector class that runs scraping jobs and saves to database
5. Create a repository class with DataFrame query methods
6. Run historical backfill for NBA seasons

## Resources

- Full plan: `docs/plans/oddsharvester-integration.md`
- Database guide: `docs/reference/database-guide.md`
- Connection guide: `docs/guides/connecting-to-database.md`
- Data exploration tool: `tools/polymarket_data_exploration.ipynb`

## Notes

- Work with Max on this - split the work between you
- Work with Dietrich on how to integrate into his Railway database (he manages the shared PostgreSQL instance)
- Ask Tan if you get stuck on architecture decisions
- Goal is to have sports odds queryable alongside existing Polymarket data
