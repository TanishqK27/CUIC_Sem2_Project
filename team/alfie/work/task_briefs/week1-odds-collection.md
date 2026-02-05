# Week 1: OddsHarvester Setup & Data Collection

**Owner:** Alfie
**Deadline:** Thursday Feb 12
**Priority:** HIGH — sportsbook data is critical

---

## Your Role

Get OddsHarvester running, scrape NBA odds, and produce CSVs in the EXACT format Dietrich needs. Max validates your CSVs before they go to Dietrich.

---

## This Week's Deliverables

### 1. Set Up OddsHarvester

```bash
# Fork the repo first on GitHub
git clone https://github.com/YOUR_USERNAME/OddsHarvester.git
cd OddsHarvester

# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test it works
python -m oddsharvester --help
```

### 2. Scrape NBA Odds

```bash
# Run scraper for NBA
python -m oddsharvester --sport basketball_nba --format json > raw_odds.json
```

### 3. Convert to Dietrich's CSV Format

Create `scripts/convert_odds_to_csv.py`:

```python
"""Convert OddsHarvester JSON to CSVs for Dietrich."""

import json
import pandas as pd
from datetime import datetime

def convert_to_csvs(json_path: str, output_dir: str = "data"):
    with open(json_path) as f:
        data = json.load(f)

    matches = []
    odds = []

    for game in data:
        # Create match record
        external_id = f"nba_{game['id']}"
        matches.append({
            'external_id': external_id,
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'commence_time': game['commence_time'],
        })

        # Create odds records
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    outcomes = {o['name']: o['price'] for o in market['outcomes']}
                    odds.append({
                        'external_id': external_id,
                        'bookmaker': bookmaker['key'],
                        'home_odds': outcomes.get(game['home_team']),
                        'away_odds': outcomes.get(game['away_team']),
                    })

    # Save CSVs
    matches_df = pd.DataFrame(matches)
    matches_df.to_csv(f"{output_dir}/sportsbook_matches.csv", index=False)
    print(f"Saved {len(matches_df)} matches")

    odds_df = pd.DataFrame(odds)
    odds_df.to_csv(f"{output_dir}/sportsbook_odds.csv", index=False)
    print(f"Saved {len(odds_df)} odds records")

if __name__ == "__main__":
    convert_to_csvs("raw_odds.json")
```

### 4. Validate & Hand Off

```bash
# Run Max's validator
python scripts/validate_csv.py matches data/sportsbook_matches.csv
python scripts/validate_csv.py odds data/sportsbook_odds.csv

# If both pass, tell Max & Dietrich the CSVs are ready
```

---

## CSV Format You Must Produce

**sportsbook_matches.csv:**
```
external_id,home_team,away_team,commence_time
nba_123456,Los Angeles Lakers,Boston Celtics,2026-02-10 19:00:00
```

**sportsbook_odds.csv:**
```
external_id,bookmaker,home_odds,away_odds
nba_123456,fanduel,1.95,2.05
nba_123456,draftkings,1.92,2.08
```

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Miran | She helps you check data quality | Tue-Wed |
| Max | He validates your CSVs | Wed |
| Dietrich | He loads your CSVs (after Max approves) | Thu |

---

## Resources

**OddsHarvester:**
- Repo: https://github.com/jordantete/OddsHarvester
- Check README for usage

**Libraries:**
- pandas for CSV: https://pandas.pydata.org/docs/
- json module: https://docs.python.org/3/library/json.html

**Internal Docs:**
- CSV formats required: `docs/reference/csv-formats.md`

**AI Tools:**
- Use Claude: "Convert this JSON structure to pandas DataFrame"

**If OddsHarvester doesn't work:**
- Try The Odds API (free tier): https://the-odds-api.com/
- Existing client: `src/cuic_quant/data/odds_api.py`

---

## Done Checklist

- [ ] OddsHarvester cloned and running
- [ ] Scraped NBA odds (at least one successful run)
- [ ] Conversion script produces correct CSV format
- [ ] `sportsbook_matches.csv` passes Max's validation
- [ ] `sportsbook_odds.csv` passes Max's validation
- [ ] CSVs handed to Dietrich

---

## Thursday Presentation (2 min)

1. Show OddsHarvester running
2. Show the two CSV files
3. Show they passed validation
4. Confirm Dietrich has them
