# Week 1: Test Data Generator

**Owner:** Mya
**Deadline:** Thursday Feb 12
**Priority:** HIGH — James and Isameel need this to test

---

## Your Role

Create synthetic test data with KNOWN outcomes for backtester testing.

---

## ⚠️ YOU HAVE ZERO DEPENDENCIES — START MONDAY

**James and Isameel are waiting for you. Get `data/test_games.csv` created Monday so they can start immediately.**

You don't need anything from anyone. Start building Day 1.

---

## Input Format (James Needs This EXACTLY)

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Game time |
| game | str | "Home vs Away" |
| home_team | str | Home team name |
| away_team | str | Away team name |
| home_odds | float | Decimal odds (1.5-3.0 range) |
| away_odds | float | Decimal odds (1.5-3.0 range) |
| home_win | int | 1 if home won, 0 if away won |

---

## Required Functions

**Location:** `tools/test_data_generator.py`

### 1. `generate_test_data(n_games=100, start_date="2026-01-01", home_win_rate=0.55, seed=42) -> pd.DataFrame`

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

---

### 2. `generate_perfect_test(n_games=20) -> pd.DataFrame`

**Purpose:** Deterministic test data for verifying backtester logic

**Rules:**
- Even-indexed games: home wins
- Odd-indexed games: away wins
- All odds = 2.0 (even money)

---

### 3. `generate_edge_cases() -> dict`

**Returns:** Dict with keys:
- `empty`: Empty DataFrame
- `single_game`: 1 game
- `all_home_wins`: 20 games, home_win_rate=1.0
- `all_away_wins`: 20 games, home_win_rate=0.0

---

## Output File

Save default test data: `data/test_games.csv`

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| James | He needs your test data | Give him Mon-Tue |
| Isameel | He uses your data to test | Wed |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`

**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- numpy.random: https://numpy.org/doc/stable/reference/random/

---

## Done Checklist

- [ ] Script at `tools/test_data_generator.py`
- [ ] `generate_test_data()` produces correct format
- [ ] `generate_perfect_test()` for deterministic testing
- [ ] `generate_edge_cases()` for edge case testing
- [ ] `data/test_games.csv` created
- [ ] Documentation at `docs/reference/test-data.md`

---

## Thursday Presentation (2 min)

1. Run generator, show output format
2. Show test_games.csv
3. Confirm James/Isameel can use it
