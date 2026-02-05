# Week 1: OddsHarvester Setup + Data Collection + Validation

**Owner:** Alfie
**Deadline:** Thursday Feb 12
**Priority:** HIGH — sportsbook data is critical

---

## Your Role

Two tasks:
1. Get OddsHarvester running, scrape NBA odds, produce CSVs
2. Validate your own CSVs before handing to Dietrich

---

## ⚠️ DO NOT WAIT FOR ODDSHARVESTER TO WORK — CREATE DUMMY CSVs MONDAY

**Build your conversion script against dummy JSON first. Don't block on OddsHarvester setup.**

### Dummy OddsHarvester JSON (`data/dummy_odds_harvester.json`)

Create a fake JSON matching OddsHarvester's output format with 3-5 games. Use this to build and test your conversion script Monday-Tuesday.

If OddsHarvester setup is slow, you still deliver:
1. Working conversion script (tested against dummy JSON)
2. Dummy CSVs in correct format
3. Fallback plan: use The Odds API instead

---

## ⚠️ STANDARDIZE FOR MATCHING — COORDINATE WITH MAX

**All your CSVs must use `team_abbr` (3-letter code) as the standard team identifier.**

Max's NBA data will also use `team_abbr`. This lets Dietrich join everything easily.

OddsHarvester may output full team names — your conversion script must map them to standard abbreviations.

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

## CSV Format (MUST MATCH EXACTLY)

### sportsbook_matches.csv

| Column | Type | Example |
|--------|------|---------|
| external_id | string | "nba_20260210_lal_bos" |
| game_date | date | "2026-02-10" |
| home_team_abbr | string | "LAL" |
| away_team_abbr | string | "BOS" |
| commence_time | datetime | "2026-02-10 19:00:00" |

### sportsbook_odds.csv

| Column | Type | Example |
|--------|------|---------|
| external_id | string | "nba_20260210_lal_bos" |
| bookmaker | string | "fanduel" |
| home_odds | decimal | 1.95 |
| away_odds | decimal | 2.05 |

**Note:** `external_id` format is `nba_{YYYYMMDD}_{away_abbr}_{home_abbr}` (lowercase)

---

## Required Script

**Location:** `scripts/convert_odds_to_csv.py`

### `convert_to_csvs(json_path, output_dir="data") -> None`

**Flow:**
1. Load OddsHarvester JSON output
2. For each game:
   - Create match record with `external_id` = `nba_{game_id}`
   - For each bookmaker with h2h market:
     - Create odds record linking to `external_id`
3. Save `sportsbook_matches.csv`
4. Save `sportsbook_odds.csv`
5. Print row counts

---

## Task 2: Validate Your Own CSVs

You own the full pipeline: collect → convert → validate → deliver.

### Validation Script

**Location:** `scripts/validate_odds_csv.py`

**CLI:** `python validate_odds_csv.py <type> <path>`

**Functions:**

#### `validate_matches_csv(path) -> list`
**Checks:**
- Required columns: `external_id`, `home_team`, `away_team`, `commence_time`
- No NULL values in required columns
- No duplicate `external_id`
- `commence_time` parseable as datetime

**Returns:** List of issue strings (empty = passed)

#### `validate_odds_csv(path) -> list`
**Checks:**
- Required columns: `external_id`, `bookmaker`, `home_odds`, `away_odds`
- Odds in range 1.01 to 50
- Overround between 100-120%

**Returns:** List of issue strings

### Dummy Test CSVs (Monday)

Create these to test your validation works:

**1. Valid CSVs** - should PASS validation
**2. Invalid CSVs** - missing columns, bad odds values, should FAIL

---

## Workflow

1. **Mon-Tue:** Set up OddsHarvester, build validation script
2. **Tue:** Create DUMMY CSVs, test validation catches errors
3. **Wed:** Scrape real data, convert to CSV, self-validate
4. **Thu:** Hand validated CSVs to Dietrich

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Miran | She spot-checks your data quality | Tue-Wed |
| Dietrich | He loads your validated CSVs | Thu |
| Mya | Send her CSVs for EDA analysis | Tue-Wed |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/reference/csv-formats.md`

**OddsHarvester:**
- Repo: https://github.com/jordantete/OddsHarvester

**Fallback (if OddsHarvester fails):**
- The Odds API: https://the-odds-api.com/
- Existing client: `src/cuic_quant/data/odds_api.py`

---

## Done Checklist

**Collection:**
- [ ] OddsHarvester running
- [ ] Conversion script at `scripts/convert_odds_to_csv.py`
- [ ] `data/sportsbook_matches.csv` created
- [ ] `data/sportsbook_odds.csv` created

**Validation:**
- [ ] Validation script at `scripts/validate_odds_csv.py`
- [ ] Dummy test CSVs pass/fail correctly
- [ ] Real CSVs pass validation
- [ ] CSVs delivered to Dietrich

---

## Thursday Presentation (2 min)

1. Show OddsHarvester output (30 sec)
2. Run validation on your CSVs, show PASS (30 sec)
3. Show row counts and data sample (1 min)
