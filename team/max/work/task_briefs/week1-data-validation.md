# Week 1: Data Validation & Coordination

**Owner:** Max
**Deadline:** Thursday Feb 12
**Priority:** HIGH — catches bad data before it breaks everything

---

## Your Role

Data quality gatekeeper. Validate CSVs before Dietrich loads them, validate database after.

---

## Required Scripts

### 1. CSV Validation Script

**Location:** `scripts/validate_csv.py`

**CLI Usage:** `python validate_csv.py <type> <path>`
- Types: `matches`, `odds`, `team_stats`, `player_stats`

**Required Functions:**

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

#### `validate_team_stats_csv(path) -> list`
**Checks:**
- Required columns: `team_name`, `season`, `games_played`, `wins`, `losses`, `win_pct`, `ppg`
- Exactly 30 rows (NBA teams)
- `win_pct` between 0-1
- `ppg` between 90-140

**Returns:** List of issue strings

#### `validate_player_stats_csv(path) -> list`
**Checks:**
- Required columns: `player_name`, `team_abbr`, `season`, `games_played`, `ppg`
- At least 200 players
- `ppg` between 0-45

**Returns:** List of issue strings

---

### 2. Database Validation Script

**Location:** `scripts/validate_database.py`

**CLI Usage:** `python validate_database.py`

**Required Function:**

#### `validate_all() -> list`
**Checks:**
- All 4 tables exist and have data
- No orphaned odds (odds without matching match)
- Row counts reasonable

**Returns:** List of issue strings

---

## Data Flow Coordination

You are middleman between data producers and Dietrich:

```
Alfie produces CSV → You validate → Pass to Dietrich → You validate DB
```

**Tracking doc:** `team/max/work/notes/data-flow-status.md`

| CSV | Owner | Validated | Sent | Loaded |
|-----|-------|-----------|------|--------|
| sportsbook_matches | Alfie | ⏳ | ⏳ | ⏳ |
| ... | ... | ... | ... | ... |

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Alfie | Validate his CSVs | Tue-Wed |
| Miran | She helps check data | Tue-Wed |
| Dietrich | Give validated CSVs, validate DB after | Wed-Thu |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`
- `docs/reference/csv-formats.md` (from Dietrich)

**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## Done Checklist

- [ ] CSV validation script at `scripts/validate_csv.py`
- [ ] Database validation script at `scripts/validate_database.py`
- [ ] Validates all 4 CSV types
- [ ] At least one CSV validated end-to-end
- [ ] Data flow status doc maintained

---

## Thursday Presentation (2 min)

1. Run CSV validation on sample file
2. Show pass/fail output
3. Show data flow status
