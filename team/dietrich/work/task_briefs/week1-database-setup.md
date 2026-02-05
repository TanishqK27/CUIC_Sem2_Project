# Week 1: Database Setup

**Owner:** Dietrich
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL

---

## Your Role

You own Railway PostgreSQL. People give you formatted CSVs, you load them. Wrong format = send it back.

---

## Task 1: Database Setup (Mon-Tue)

### Tables to Create

Create these 4 tables in Railway. Use Claude Code to help generate the SQL:

1. **sportsbook_matches** - Games with external_id (unique), home_team, away_team, commence_time
2. **sportsbook_odds** - Odds per match per bookmaker (FK to matches)
3. **nba_team_stats** - Team stats by season (unique on team_name + season)
4. **nba_player_stats** - Player stats by season (unique on player_name + season)

**Prompt for Claude:** "Create PostgreSQL tables for sportsbook matches, odds, NBA team stats, and player stats with appropriate indexes and constraints"

### CSV Loader Script

Create `scripts/load_csv_to_railway.py` that:
- Takes CSV type and path as args
- Loads matches, odds, team_stats, player_stats
- Handles duplicates with ON CONFLICT
- Prints row counts

**Prompt for Claude:** "Write a Python script using psycopg2 to load CSVs into PostgreSQL with upsert logic"

### Document CSV Formats

Create `docs/reference/csv-formats.md` specifying exact columns for each CSV type. This is the contract - Alfie/others must match this exactly.

---

## Task 2: Polymarket Data Analysis (Tue-Thu)

**While waiting for CSVs**, analyze the existing Polymarket data in Railway.

### What To Explore

Use the existing `price_snapshots` data (90K+ rows) to find:

1. **Price movement patterns**
   - How do probabilities change over time for a typical event?
   - Do prices move smoothly or in jumps?
   - Is there mean reversion? (prices that spike tend to come back?)

2. **Volatility analysis**
   - Which types of events have most price movement?
   - Time of day effects? (more volatility at certain hours?)
   - How does volatility change as event approaches?

3. **Gap persistence**
   - When PM price differs from implied fair value, how long does gap last?
   - Do gaps close gradually or suddenly?

### What To Document

Create `research/notebooks/analysis/polymarket_eda.ipynb`:

```markdown
# Polymarket Exploratory Data Analysis

## Key Findings
- [Bullet points of interesting patterns]

## Visualizations
- Price paths for sample events
- Volatility over time
- Gap distribution histogram

## Intuition
- Why might these patterns exist?
- How could this inform trading? (speculation only)

## Questions for Team
- [Things that need more investigation]
```

### IMPORTANT: Stay In Your Lane

**DO:**
- Descriptive statistics
- Visualizations
- Document interesting patterns
- Hypothesize why patterns exist

**DON'T:**
- Build predictive models
- Create trading strategies
- Backtest anything
- Go down rabbit holes

This is EDA only. Models come in Week 4.

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Alfie | Receives his CSVs | Wed |
| Max | He validates after you load | After load |
| Miran | She confirms CSVs are ready | Wed |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`
- `docs/SOPs/team-sops.md`

**For DB Setup:**
- Railway docs: https://docs.railway.app/databases/postgresql
- psycopg2: https://www.psycopg.org/docs/

**For Analysis:**
- Existing PM data: query `price_snapshots` table
- pandas/matplotlib for analysis

**Claude Code Prompts:**
- "Create PostgreSQL schema for sports betting data"
- "Write CSV loader with upsert for PostgreSQL"
- "Analyze time series data for mean reversion patterns"
- "Create volatility analysis for price data"

---

## Done Checklist

**Database:**
- [ ] 4 tables created in Railway
- [ ] Loader script works
- [ ] CSV formats documented
- [ ] Test load with Alfie's dummy CSV

**Analysis:**
- [ ] EDA notebook created
- [ ] 3+ interesting findings documented
- [ ] Visualizations included
- [ ] Stayed descriptive (no models)

---

## Thursday Presentation (3 min)

1. Show tables exist, run one load (1 min)
2. Show 2-3 interesting Polymarket findings (2 min)
