# Task: OddsHarvester Setup

**Owner:** Alfie
**Deadline:** Feb 12 (Week 1)
**Priority:** Critical — blocks all sportsbook data

---

## What You're Building

Get OddsHarvester running locally to scrape NBA odds from sportsbooks. Verify it collects the data we need.

---

## Why This Matters

OddsHarvester gives us free sportsbook odds without needing expensive API subscriptions. It scrapes FanDuel, DraftKings, BetMGM, etc. We compare these odds to Polymarket to find gaps.

---

## Exactly What You Must Deliver

### 1. Fork and Clone OddsHarvester

```bash
# Fork on GitHub first: https://github.com/jordantete/OddsHarvester
# Then clone your fork

git clone https://github.com/YOUR_USERNAME/OddsHarvester.git
cd OddsHarvester
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt
```

### 3. Verify Installation

Run the scraper in test mode to confirm it works:

```bash
# Check what sports are available
python -m oddsharvester --help

# Try scraping NBA odds
python -m oddsharvester --sport basketball_nba --format json
```

### 4. Document What Data We Get

Create `team/alfie/work/notes/oddsharvester-data-fields.md`:

```markdown
# OddsHarvester Data Fields

## Output Structure

After running the scraper, document exactly what columns we get:

```json
{
    "game_id": "...",
    "home_team": "Los Angeles Lakers",
    "away_team": "Boston Celtics",
    "commence_time": "2026-02-10T19:00:00Z",
    "bookmakers": [
        {
            "key": "fanduel",
            "markets": [
                {
                    "key": "h2h",
                    "outcomes": [
                        {"name": "Los Angeles Lakers", "price": 1.95},
                        {"name": "Boston Celtics", "price": 2.05}
                    ]
                }
            ]
        }
    ]
}
```

## Fields We Care About

| Field | Use |
|-------|-----|
| home_team | Match to Polymarket events |
| away_team | Match to Polymarket events |
| commence_time | When the game starts |
| outcomes.price | Decimal odds for each team |
| bookmaker.key | Which sportsbook |

## Available Sportsbooks

- [ ] FanDuel
- [ ] DraftKings
- [ ] BetMGM
- [ ] Caesars
- [ ] PointsBet
```

### 5. Test NBA Scraping

Run actual scrapes and save output:

```bash
# Scrape and save to file
python -m oddsharvester --sport basketball_nba --format json > data/nba_odds_sample.json

# Verify file has data
cat data/nba_odds_sample.json | python -m json.tool | head -50
```

### 6. Create Wrapper Script

Create `scripts/scrape_nba_odds.py`:

```python
"""Wrapper script to scrape NBA odds using OddsHarvester."""

import subprocess
import json
from datetime import datetime
from pathlib import Path

def scrape_nba_odds(output_dir: str = "data/odds") -> str:
    """
    Scrape current NBA odds and save to timestamped file.

    Returns:
        Path to output file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/nba_odds_{timestamp}.json"

    # Run OddsHarvester
    # Adjust path if OddsHarvester is installed differently
    result = subprocess.run(
        ["python", "-m", "oddsharvester", "--sport", "basketball_nba", "--format", "json"],
        capture_output=True,
        text=True,
        cwd="/path/to/OddsHarvester"  # UPDATE THIS PATH
    )

    if result.returncode != 0:
        raise RuntimeError(f"Scraper failed: {result.stderr}")

    # Parse and save
    data = json.loads(result.stdout)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Scraped {len(data)} games to {output_file}")
    return output_file

if __name__ == "__main__":
    scrape_nba_odds()
```

---

## Done Checklist

- [ ] OddsHarvester forked and cloned
- [ ] Virtual environment set up
- [ ] Scraper runs without errors
- [ ] Data fields documented in `team/alfie/work/notes/oddsharvester-data-fields.md`
- [ ] Sample NBA odds saved to `data/nba_odds_sample.json`
- [ ] Wrapper script created at `scripts/scrape_nba_odds.py`
- [ ] Wrapper script runs and saves timestamped files

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Run the scraper: `python -m oddsharvester --sport basketball_nba`
2. Show the JSON output structure
3. List which sportsbooks we get data from
4. Show the wrapper script saving to file

**Duration:** 2 minutes max

---

## Resources

- OddsHarvester repo: https://github.com/jordantete/OddsHarvester
- OddsHarvester docs: Check the repo's README
- Python subprocess docs: https://docs.python.org/3/library/subprocess.html

---

## Common Issues

**Issue:** Scraper gets rate limited or blocked
**Fix:** Add delays between requests, check if proxies are needed

**Issue:** Missing teams in output
**Fix:** Check if NBA season is active, verify sport parameter

**Issue:** JSON parsing fails
**Fix:** Check for HTML in output (could be error page)

---

## Who To Ask If Stuck

1. Check OddsHarvester GitHub issues first
2. Google the error message
3. Max — he's doing similar data work
4. Tan — if completely blocked
