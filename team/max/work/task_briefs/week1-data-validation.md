# Week 1: NBA Stats Collection

**Owner:** Max
**Deadline:** Thursday Feb 12
**Priority:** CRITICAL — fundamental data for all models

---

## Your Role

Collect **every NBA stat possible** at maximum granularity. You and Alfie are the two data collectors — he gets odds, you get NBA stats.

---

## ⚠️ START COLLECTING MONDAY — DON'T WAIT

**You have zero dependencies. Start pulling NBA data Day 1.**

---

## ⚠️ STANDARDIZE FOR MATCHING — COORDINATE WITH ALFIE

**All your CSVs must use `team_abbr` (3-letter code) as the standard team identifier.**

Alfie's odds data will also use `team_abbr`. This lets Dietrich join everything easily.

### Standard Team Abbreviations (use EXACTLY these)

| team_abbr | team_name |
|-----------|-----------|
| ATL | Atlanta Hawks |
| BOS | Boston Celtics |
| BKN | Brooklyn Nets |
| CHA | Charlotte Hornets |
| CHI | Chicago Bulls |
| CLE | Cleveland Cavaliers |
| DAL | Dallas Mavericks |
| DEN | Denver Nuggets |
| DET | Detroit Pistons |
| GSW | Golden State Warriors |
| HOU | Houston Rockets |
| IND | Indiana Pacers |
| LAC | Los Angeles Clippers |
| LAL | Los Angeles Lakers |
| MEM | Memphis Grizzlies |
| MIA | Miami Heat |
| MIL | Milwaukee Bucks |
| MIN | Minnesota Timberwolves |
| NOP | New Orleans Pelicans |
| NYK | New York Knicks |
| OKC | Oklahoma City Thunder |
| ORL | Orlando Magic |
| PHI | Philadelphia 76ers |
| PHX | Phoenix Suns |
| POR | Portland Trail Blazers |
| SAC | Sacramento Kings |
| SAS | San Antonio Spurs |
| TOR | Toronto Raptors |
| UTA | Utah Jazz |
| WAS | Washington Wizards |

---

## Scope: MAXIMUM GRANULARITY

Pull **every stat available** from the 2021-22 season onwards (when Polymarket started NBA markets).

**Seasons to collect:** 2021-22, 2022-23, 2023-24, 2024-25 (current)

---

## Data to Collect

### Team Stats (`data/nba_team_stats.csv`)

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

### Player Stats (`data/nba_player_stats.csv`)

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

### Game Logs (`data/nba_game_logs.csv`) — MOST IMPORTANT

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

---

## Required Script

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

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Dietrich | Give him your 3 NBA CSVs | Wed-Thu |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`
- `docs/reference/csv-formats.md`

**Libraries:**
- nba_api: https://github.com/swar/nba_api
- pandas: https://pandas.pydata.org/docs/

---

## Done Checklist

- [ ] Script at `scripts/collect_nba_stats.py`
- [ ] `data/nba_team_stats.csv` with 4 seasons (120 rows = 30 teams × 4 seasons)
- [ ] `data/nba_player_stats.csv` with 4 seasons (2000+ rows)
- [ ] `data/nba_game_logs.csv` with 4 seasons (5000+ rows)
- [ ] CSVs match Dietrich's format
- [ ] CSVs delivered to Dietrich

---

## Thursday Presentation (2 min)

1. Show row counts for all 3 CSVs (30 sec)
2. Show date range coverage (30 sec)
3. Show sample data from game_logs (1 min)
