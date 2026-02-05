# Week 1: Database Setup + Polymarket EDA

**Owner:** Dietrich
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL

---

## Your Role

You own Railway PostgreSQL. People give you formatted CSVs, you load them. Wrong format = send it back.

---

## Task 1: Database Setup (Mon-Tue)

### Tables to Create

| Table | Key Columns | Constraints |
|-------|-------------|-------------|
| sportsbook_matches | external_id, home_team, away_team, commence_time | external_id UNIQUE |
| sportsbook_odds | match_id (FK), bookmaker, home_odds, away_odds | FK to matches |
| nba_team_stats | team_name, season, wins, losses, win_pct, ppg | UNIQUE(team_name, season) |
| nba_player_stats | player_name, team_abbr, season, ppg, rpg, apg | UNIQUE(player_name, season) |

**Indexes:** Add on foreign keys and commonly queried columns (commence_time, team names)

---

### CSV Loader Script

**Location:** `scripts/load_csv_to_railway.py`

**CLI:** `python load_csv_to_railway.py <type> <csv_path>`

**Required Functions:**

| Function | Expected CSV Columns |
|----------|---------------------|
| `load_sportsbook_matches(path)` | external_id, home_team, away_team, commence_time |
| `load_sportsbook_odds(path)` | external_id, bookmaker, home_odds, away_odds |
| `load_nba_team_stats(path)` | team_name, season, games_played, wins, losses, win_pct, ppg |
| `load_nba_player_stats(path)` | player_name, team_abbr, season, games_played, ppg, rpg, apg |

**All loaders must:**
- Handle duplicates with ON CONFLICT
- Print row counts
- Use `DATABASE_URL` env var

---

### Document CSV Formats

**Location:** `docs/reference/csv-formats.md`

Document exact columns, types, and examples for each CSV type. This is the contract.

---

## Task 2: Polymarket EDA (Tue-Thu)

While waiting for CSVs, analyze existing `price_snapshots` data.

### Analysis Areas

| Area | Questions |
|------|-----------|
| Price movement | Mean reversion? Smooth or jumpy? |
| Volatility | Time of day effects? Event proximity? |
| Gap persistence | How long do price gaps last? |

### Deliverable

**Location:** `research/notebooks/analysis/polymarket_eda.ipynb`

**Sections:**
1. Key Findings (bullet points)
2. Visualizations (price paths, volatility, gaps)
3. Intuition (why might this happen?)
4. Questions for team

### STAY IN YOUR LANE

**DO:** Descriptive stats, visualizations, hypothesize
**DON'T:** Build models, create strategies, backtest

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Alfie | Receives his CSVs | Wed |
| Max | He validates after you load | After load |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`

**Libraries:**
- psycopg2: https://www.psycopg.org/docs/
- Railway: https://docs.railway.app/databases/postgresql

---

## Done Checklist

**Database:**
- [ ] 4 tables created
- [ ] Loader script works
- [ ] CSV formats documented

**EDA:**
- [ ] Notebook created
- [ ] 3+ findings documented
- [ ] Visualizations included

---

## Thursday Presentation (3 min)

1. Show tables, run one load (1 min)
2. Show 2-3 Polymarket findings (2 min)
