# Week 1: Test Data Generator + Sportsbook EDA

**Owner:** Mya
**Deadline:** Thursday Feb 12
**Priority:** HIGH

---

## Your Role

Two tasks this week:
1. Create synthetic test data for James/Isameel (Fri-Sat)
2. Analyze Alfie's sportsbook odds data (Sat-Wed)

---

## ⚠️ TASK 1 IS BLOCKING OTHERS — DELIVER FRIDAY

**James cannot start until you give him `data/test_games.csv`. Build it Friday morning, send it to him Friday afternoon.**

---

## Task 1: Test Data Generator (Fri-Sat)

### Input Format (James Needs This EXACTLY)

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Game time |
| game | str | "Home vs Away" |
| home_team | str | Home team name |
| away_team | str | Away team name |
| home_odds | float | Decimal odds (1.5-3.0 range) |
| away_odds | float | Decimal odds (1.5-3.0 range) |
| home_win | int | 1 if home won, 0 if away won |

### Required Functions

**Location:** `tools/test_data_generator.py`

#### 1. `generate_test_data(n_games=100, start_date="2026-01-01", home_win_rate=0.55, seed=42) -> pd.DataFrame`

**Parameters:**
- `n_games`: int, number of games
- `start_date`: str, start date
- `home_win_rate`: float, probability home wins
- `seed`: int, for reproducibility

**Flow:**
1. Set random seed
2. Create team list (use real NBA team names)
3. For each game:
   - Pick random home/away teams
   - Determine outcome based on home_win_rate
   - Generate odds (slightly favor eventual winner)
   - Create row with all 7 columns
4. Return DataFrame

#### 2. `generate_perfect_test(n_games=20) -> pd.DataFrame`

**Purpose:** Deterministic test data for verifying backtester logic

**Rules:**
- Even-indexed games: home wins
- Odd-indexed games: away wins
- All odds = 2.0 (even money)

#### 3. `generate_edge_cases() -> dict`

**Returns:** Dict with keys:
- `empty`: Empty DataFrame
- `single_game`: 1 game
- `all_home_wins`: 20 games, home_win_rate=1.0
- `all_away_wins`: 20 games, home_win_rate=0.0

### Output File

Save default test data: `data/test_games.csv`

---

## Task 2: Sportsbook Odds EDA (Sat-Wed)

**Get Alfie's CSV data Tuesday/Wednesday and analyze it.**

This is parallel to Dietrich's Polymarket EDA — you both produce independent reports on your data sources before we combine them.

### Analysis Areas

| Area | Questions |
|------|-----------|
| Odds distribution | What's the typical range? Any outliers? |
| Bookmaker comparison | Do different bookmakers offer different odds? |
| Home vs away | Is there a home favorite bias? |
| Overround analysis | How much margin do bookmakers take? |
| Time patterns | Do odds change closer to game time? |

### Deliverable

**Location:** `research/notebooks/analysis/sportsbook_eda.ipynb`

**Sections:**
1. Key Findings (bullet points)
2. Visualizations (odds distributions, bookmaker comparison, overround)
3. Intuition (why might this happen?)
4. Questions for team

### STAY IN YOUR LANE

**DO:** Descriptive stats, visualizations, hypothesize
**DON'T:** Build models, create strategies, backtest

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| James | Send him test_games.csv | **Friday** |
| Isameel | He uses your test data | Tue |
| Alfie | Get his CSVs for EDA | Sat-Mon |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`

**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- numpy.random: https://numpy.org/doc/stable/reference/random/
- matplotlib: https://matplotlib.org/stable/gallery/

---

## Done Checklist

**Test Data Generator:**
- [ ] Script at `tools/test_data_generator.py`
- [ ] `generate_test_data()` produces correct format
- [ ] `generate_perfect_test()` for deterministic testing
- [ ] `generate_edge_cases()` for edge case testing
- [ ] `data/test_games.csv` created and sent to James **Friday**

**Sportsbook EDA:**
- [ ] Notebook created at `research/notebooks/analysis/sportsbook_eda.ipynb`
- [ ] 3+ findings documented
- [ ] Visualizations included

---

## Thursday Presentation (3 min)

1. Show test_games.csv, confirm James/Isameel used it (1 min)
2. Show 2-3 sportsbook findings with visualizations (2 min)
