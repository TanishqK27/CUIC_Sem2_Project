# Week 1: OddsHarvester Setup & Data Collection

**Owner:** Alfie
**Deadline:** Thursday Feb 12
**Priority:** HIGH — sportsbook data is critical

---

## Your Role

Get OddsHarvester running, scrape NBA odds, produce CSVs in Dietrich's exact format.

---

## ⚠️ DO NOT WAIT FOR ODDSHARVESTER TO WORK — CREATE DUMMY CSVs MONDAY

**Build your conversion script against dummy JSON first. Don't block on OddsHarvester setup.**

### Dummy OddsHarvester JSON (`data/dummy_odds_harvester.json`)

Create a fake JSON matching OddsHarvester's output format with 3-5 games. Use this to build and test your conversion script Monday-Tuesday.

If OddsHarvester setup is slow, you still deliver:
1. Working conversion script (tested against dummy JSON)
2. Dummy CSVs in correct format (validated by Max)
3. Fallback plan: use The Odds API instead

---

## CSV Format (MUST MATCH EXACTLY)

### sportsbook_matches.csv

| Column | Type | Example |
|--------|------|---------|
| external_id | string | "nba_20260210_lal_bos" |
| home_team | string | "Los Angeles Lakers" |
| away_team | string | "Boston Celtics" |
| commence_time | datetime | "2026-02-10 19:00:00" |

### sportsbook_odds.csv

| Column | Type | Example |
|--------|------|---------|
| external_id | string | "nba_20260210_lal_bos" |
| bookmaker | string | "fanduel" |
| home_odds | decimal | 1.95 |
| away_odds | decimal | 2.05 |

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

## Workflow

1. **Mon-Tue:** Set up OddsHarvester, get it running
2. **Tue:** Create DUMMY CSVs in correct format, send to Max for validation test
3. **Wed:** Scrape real data, convert to CSV, validate with Max
4. **Thu:** Hand validated CSVs to Dietrich

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Miran | She checks your data quality | Tue-Wed |
| Max | He validates your CSVs | Wed |
| Dietrich | He loads your CSVs | Thu |

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

- [ ] OddsHarvester running
- [ ] Conversion script at `scripts/convert_odds_to_csv.py`
- [ ] Dummy CSVs created and validated by Max
- [ ] Real CSVs passed validation
- [ ] CSVs delivered to Dietrich

---

## Thursday Presentation (2 min)

1. Show OddsHarvester output
2. Show both CSV files
3. Confirm passed validation
