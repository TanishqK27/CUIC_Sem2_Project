# Week 1: NBA Stats Collection + Data Validation

**Owner:** Max
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL

---

## Your Role

Two tasks this week:
1. **NBA Stats Collection** — gather every NBA stat possible at maximum granularity (Mon-Wed)
2. **Data Validation** — validate CSVs before Dietrich loads them (ongoing)

You and Alfie are the two data collectors. He gets odds, you get NBA stats.

---

## ⚠️ START COLLECTING MONDAY — DON'T WAIT

**You have zero dependencies. Start pulling NBA data Day 1.**

---

## Task 1: NBA Stats Collection (Mon-Wed)

### Scope: MAXIMUM GRANULARITY

Pull **every stat available** from the 2021-22 season onwards (when Polymarket started NBA markets).

### Data to Collect

#### Team Stats (`data/nba_team_stats.csv`)

| Column | Description |
|--------|-------------|
| team_id | NBA team ID |
| team_name | Full team name |
| team_abbr | 3-letter abbreviation |
| season | e.g., "2024-25" |
| games_played | Games played |
| wins | Total wins |
| losses | Total losses |
| win_pct | Win percentage |
| home_wins | Home wins |
| home_losses | Home losses |
| away_wins | Away wins |
| away_losses | Away losses |
| ppg | Points per game |
| oppg | Opponent points per game |
| rpg | Rebounds per game |
| apg | Assists per game |
| spg | Steals per game |
| bpg | Blocks per game |
| topg | Turnovers per game |
| fg_pct | Field goal % |
| fg3_pct | 3-point % |
| ft_pct | Free throw % |
| off_rating | Offensive rating |
| def_rating | Defensive rating |
| net_rating | Net rating |
| pace | Pace |

#### Player Stats (`data/nba_player_stats.csv`)

| Column | Description |
|--------|-------------|
| player_id | NBA player ID |
| player_name | Full name |
| team_abbr | Current team |
| season | e.g., "2024-25" |
| games_played | Games played |
| games_started | Games started |
| mpg | Minutes per game |
| ppg | Points per game |
| rpg | Rebounds per game |
| apg | Assists per game |
| spg | Steals per game |
| bpg | Blocks per game |
| topg | Turnovers per game |
| fg_pct | Field goal % |
| fg3_pct | 3-point % |
| ft_pct | Free throw % |
| plus_minus | Plus/minus |
| per | Player efficiency rating |

#### Game Logs (`data/nba_game_logs.csv`) — MOST IMPORTANT

| Column | Description |
|--------|-------------|
| game_id | Unique game ID |
| game_date | Date of game |
| season | e.g., "2024-25" |
| home_team_id | Home team ID |
| home_team_abbr | Home team abbreviation |
| away_team_id | Away team ID |
| away_team_abbr | Away team abbreviation |
| home_score | Home team final score |
| away_score | Away team final score |
| home_win | 1 if home won, 0 if away won |
| home_q1 | Home Q1 score |
| home_q2 | Home Q2 score |
| home_q3 | Home Q3 score |
| home_q4 | Home Q4 score |
| away_q1 | Away Q1 score |
| away_q2 | Away Q2 score |
| away_q3 | Away Q3 score |
| away_q4 | Away Q4 score |

### Historical Range

**Seasons to collect:** 2021-22, 2022-23, 2023-24, 2024-25 (current)

This covers when Polymarket started NBA markets.

### Required Script

**Location:** `scripts/collect_nba_stats.py`

**Functions:**
- `collect_team_stats(seasons) -> pd.DataFrame`
- `collect_player_stats(seasons) -> pd.DataFrame`
- `collect_game_logs(seasons) -> pd.DataFrame`
- `save_all_stats(output_dir="data")`

**Flow:**
1. Loop through seasons
2. Pull data from nba_api
3. Handle rate limits (sleep between requests)
4. Save to CSV in Dietrich's format

---

## Resources for NBA Data

**Primary: nba_api (Python)**
- Repo: https://github.com/swar/nba_api
- Docs: https://github.com/swar/nba_api/tree/master/docs
- Examples: https://github.com/swar/nba_api/tree/master/docs/examples

**Key Endpoints:**
```
from nba_api.stats.endpoints import (
    leaguegamefinder,      # Game logs
    teamyearbyyearstats,   # Team season stats
    leaguedashteamstats,   # Team advanced stats
    leaguedashplayerstats, # Player stats
    playergamelog,         # Player game logs
)
```

**Rate Limiting:**
- Add `time.sleep(0.6)` between API calls
- NBA blocks aggressive scraping

**Alternative Sources (if nba_api fails):**
- Basketball Reference: https://www.basketball-reference.com/
- NBA Stats: https://www.nba.com/stats/

---

## Task 2: Data Validation (Ongoing)

### Dummy Test CSVs to Create Monday

**1. Valid matches CSV** (`data/test_valid_matches.csv`)
- 5 rows with correct columns and values

**2. Invalid matches CSV** (`data/test_invalid_matches.csv`)
- Missing columns, NULL values, bad dates

**3. Valid odds CSV** (`data/test_valid_odds.csv`)
- 10 rows with odds in range 1.01-50

**4. Invalid odds CSV** (`data/test_invalid_odds.csv`)
- Odds = 0.5, odds = 100, overround = 150%

### Validation Scripts

**Location:** `scripts/validate_csv.py`

**CLI:** `python validate_csv.py <type> <path>`

**Functions:**

#### `validate_matches_csv(path) -> list`
- Required columns: `external_id`, `home_team`, `away_team`, `commence_time`
- No NULL values, no duplicate external_id, datetime parseable

#### `validate_odds_csv(path) -> list`
- Required columns: `external_id`, `bookmaker`, `home_odds`, `away_odds`
- Odds in range 1.01-50, overround 100-120%

#### `validate_team_stats_csv(path) -> list`
- Required columns: `team_name`, `season`, `games_played`, `wins`, `losses`, `win_pct`, `ppg`
- 30 teams per season, win_pct 0-1, ppg 90-140

#### `validate_player_stats_csv(path) -> list`
- Required columns: `player_name`, `team_abbr`, `season`, `games_played`, `ppg`
- 200+ players, ppg 0-45

**Location:** `scripts/validate_database.py`

#### `validate_all() -> list`
- All tables exist and have data
- No orphaned records
- Row counts reasonable

---

## Data Flow

```
Max collects NBA stats → Self-validate → Give to Dietrich
Alfie collects odds → Miran checks → Max validates → Give to Dietrich
```

**Tracking doc:** `team/max/work/notes/data-flow-status.md`

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Alfie | Validate his odds CSVs | Tue-Wed |
| Miran | She helps check data | Tue-Wed |
| Dietrich | Give him validated CSVs (yours + Alfie's) | Wed-Thu |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`
- `docs/reference/csv-formats.md`

**Libraries:**
- nba_api: https://github.com/swar/nba_api
- pandas: https://pandas.pydata.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## Done Checklist

**NBA Stats Collection:**
- [ ] Script at `scripts/collect_nba_stats.py`
- [ ] `data/nba_team_stats.csv` with 4 seasons
- [ ] `data/nba_player_stats.csv` with 4 seasons
- [ ] `data/nba_game_logs.csv` with 4 seasons
- [ ] CSVs match Dietrich's format

**Data Validation:**
- [ ] CSV validation script at `scripts/validate_csv.py`
- [ ] Database validation script at `scripts/validate_database.py`
- [ ] Test CSVs created
- [ ] Data flow status doc maintained

---

## Thursday Presentation (3 min)

1. Show NBA data collected — row counts, date ranges (1 min)
2. Run validation on sample CSV (1 min)
3. Show data flow status (1 min)
