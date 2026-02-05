# Week 1: Database Setup + Polymarket EDA

**Owner:** Dietrich
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL

---

## Your Role

You own Railway PostgreSQL. People give you formatted CSVs, you load them. Wrong format = send it back.

---

## ⚠️ DO NOT WAIT FOR ALFIE'S CSVs — START MONDAY

**Create dummy CSVs to test your loader script immediately.**

### Dummy sportsbook_matches.csv (5 rows)

| external_id | home_team | away_team | commence_time |
|-------------|-----------|-----------|---------------|
| nba_20260210_lal_bos | Los Angeles Lakers | Boston Celtics | 2026-02-10 19:00:00 |
| nba_20260210_gsw_mia | Golden State Warriors | Miami Heat | 2026-02-10 20:00:00 |
| ... | ... | ... | ... |

### Dummy sportsbook_odds.csv (10 rows - 2 bookmakers per match)

| external_id | bookmaker | home_odds | away_odds |
|-------------|-----------|-----------|-----------|
| nba_20260210_lal_bos | fanduel | 1.95 | 2.05 |
| nba_20260210_lal_bos | draftkings | 1.91 | 2.10 |
| ... | ... | ... | ... |

**Save to:** `data/dummy_matches.csv`, `data/dummy_odds.csv`

Build and test your loader with dummy data Monday-Tuesday. When Alfie's real CSVs arrive Wednesday, they must match this exact format — plug and play.

---

## Task 1: Database Setup (Mon-Tue)

### Tables to Create

**5 tables total** — 2 from Alfie (odds), 3 from Max (NBA stats)

#### Sportsbook Tables (from Alfie)

| Table | Key Columns | Constraints |
|-------|-------------|-------------|
| sportsbook_matches | external_id, home_team, away_team, commence_time | external_id UNIQUE |
| sportsbook_odds | match_id (FK), bookmaker, home_odds, away_odds | FK to matches |

#### NBA Stats Tables (from Max) — MAXIMUM GRANULARITY

**nba_team_stats** — all columns:
```
team_id, team_name, team_abbr, season, games_played, wins, losses, win_pct,
home_wins, home_losses, away_wins, away_losses, ppg, oppg, rpg, apg, spg,
bpg, topg, fg_pct, fg3_pct, ft_pct, off_rating, def_rating, net_rating, pace
```
Constraint: `UNIQUE(team_id, season)`

**nba_player_stats** — all columns:
```
player_id, player_name, team_abbr, season, games_played, games_started,
mpg, ppg, rpg, apg, spg, bpg, topg, fg_pct, fg3_pct, ft_pct, plus_minus, per
```
Constraint: `UNIQUE(player_id, season)`

**nba_game_logs** — MOST IMPORTANT:
```
game_id, game_date, season, home_team_id, home_team_abbr, away_team_id,
away_team_abbr, home_score, away_score, home_win, home_q1, home_q2,
home_q3, home_q4, away_q1, away_q2, away_q3, away_q4
```
Constraint: `game_id UNIQUE`

**Indexes:** Add on foreign keys, game_date, season, team names

---

### CSV Loader Script

**Location:** `scripts/load_csv_to_railway.py`

**CLI:** `python load_csv_to_railway.py <type> <csv_path>`

**Required Functions:**

| Function | Source |
|----------|--------|
| `load_sportsbook_matches(path)` | Alfie |
| `load_sportsbook_odds(path)` | Alfie |
| `load_nba_team_stats(path)` | Max |
| `load_nba_player_stats(path)` | Max |
| `load_nba_game_logs(path)` | Max |

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
| Alfie | Receives his odds CSVs (2 files) | Wed |
| Max | Receives his NBA stats CSVs (3 files), validates DB after | Wed-Thu |

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
- [ ] 5 tables created (2 sportsbook + 3 NBA)
- [ ] Loader script works for all 5 types
- [ ] CSV formats documented

**EDA:**
- [ ] Notebook created
- [ ] 3+ findings documented
- [ ] Visualizations included

---

## Thursday Presentation (3 min)

1. Show tables, run one load (1 min)
2. Show 2-3 Polymarket findings (2 min)
