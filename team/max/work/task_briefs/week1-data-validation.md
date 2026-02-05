# Week 1: Data Validation & Coordination

**Owner:** Max
**Deadline:** Thursday Feb 12
**Priority:** HIGH — catches bad data before it breaks everything

---

## Your Role

You're the data quality gatekeeper AND coordinator between Data team and Dietrich. You validate CSVs before Dietrich loads them, and validate the database after.

---

## This Week's Deliverables

### 1. CSV Validation Script

Create `scripts/validate_csv.py`:

```python
"""Validate CSVs before sending to Dietrich."""

import pandas as pd
import sys
from pathlib import Path

def validate_matches_csv(path: str) -> list:
    """Validate sportsbook_matches.csv"""
    issues = []
    df = pd.read_csv(path)

    # Required columns
    required = ['external_id', 'home_team', 'away_team', 'commence_time']
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
        return issues

    # Check for nulls
    for col in required:
        nulls = df[col].isnull().sum()
        if nulls > 0:
            issues.append(f"NULL values in {col}: {nulls}")

    # Check for duplicates
    dups = df['external_id'].duplicated().sum()
    if dups > 0:
        issues.append(f"Duplicate external_ids: {dups}")

    # Check datetime format
    try:
        pd.to_datetime(df['commence_time'])
    except:
        issues.append("commence_time not valid datetime format")

    return issues

def validate_odds_csv(path: str) -> list:
    """Validate sportsbook_odds.csv"""
    issues = []
    df = pd.read_csv(path)

    required = ['external_id', 'bookmaker', 'home_odds', 'away_odds']
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
        return issues

    # Check odds range (1.01 to 50 is reasonable)
    bad_home = ((df['home_odds'] < 1.01) | (df['home_odds'] > 50)).sum()
    bad_away = ((df['away_odds'] < 1.01) | (df['away_odds'] > 50)).sum()
    if bad_home > 0:
        issues.append(f"home_odds out of range: {bad_home}")
    if bad_away > 0:
        issues.append(f"away_odds out of range: {bad_away}")

    # Check overround (should be 100-115%)
    df['overround'] = (1/df['home_odds'] + 1/df['away_odds']) * 100
    bad_or = ((df['overround'] < 100) | (df['overround'] > 120)).sum()
    if bad_or > 0:
        issues.append(f"Suspicious overround: {bad_or}")

    return issues

def validate_team_stats_csv(path: str) -> list:
    """Validate nba_team_stats.csv"""
    issues = []
    df = pd.read_csv(path)

    required = ['team_name', 'season', 'games_played', 'wins', 'losses', 'win_pct', 'ppg']
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
        return issues

    # Should have 30 teams
    if len(df) != 30:
        issues.append(f"Expected 30 teams, got {len(df)}")

    # Win pct should be 0-1
    bad_wp = ((df['win_pct'] < 0) | (df['win_pct'] > 1)).sum()
    if bad_wp > 0:
        issues.append(f"win_pct out of range: {bad_wp}")

    # PPG should be 90-140
    bad_ppg = ((df['ppg'] < 90) | (df['ppg'] > 140)).sum()
    if bad_ppg > 0:
        issues.append(f"ppg out of range: {bad_ppg}")

    return issues

def validate_player_stats_csv(path: str) -> list:
    """Validate nba_player_stats.csv"""
    issues = []
    df = pd.read_csv(path)

    required = ['player_name', 'team_abbr', 'season', 'games_played', 'ppg']
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
        return issues

    # Should have 300+ players
    if len(df) < 200:
        issues.append(f"Too few players: {len(df)}")

    # PPG should be 0-45
    bad_ppg = ((df['ppg'] < 0) | (df['ppg'] > 45)).sum()
    if bad_ppg > 0:
        issues.append(f"ppg out of range: {bad_ppg}")

    return issues

def main():
    if len(sys.argv) < 3:
        print("Usage: python validate_csv.py <type> <path>")
        print("Types: matches, odds, team_stats, player_stats")
        sys.exit(1)

    validators = {
        'matches': validate_matches_csv,
        'odds': validate_odds_csv,
        'team_stats': validate_team_stats_csv,
        'player_stats': validate_player_stats_csv,
    }

    csv_type = sys.argv[1]
    path = sys.argv[2]

    if csv_type not in validators:
        print(f"Unknown type: {csv_type}")
        sys.exit(1)

    print(f"Validating {path}...")
    issues = validators[csv_type](path)

    if issues:
        print("❌ FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("✓ PASSED - Ready for Dietrich")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### 2. Database Validation Script

Create `scripts/validate_database.py`:

```python
"""Validate data after loading into Railway."""

import pandas as pd
from sqlalchemy import create_engine
import os

def get_engine():
    return create_engine(os.environ['DATABASE_URL'])

def validate_all():
    engine = get_engine()
    issues = []

    # Check all tables exist and have data
    tables = ['sportsbook_matches', 'sportsbook_odds', 'nba_team_stats', 'nba_player_stats']

    for table in tables:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", engine).iloc[0,0]
            print(f"{table}: {count} rows")
            if count == 0:
                issues.append(f"{table} is empty")
        except Exception as e:
            issues.append(f"{table} error: {e}")

    # Check matches have odds
    orphan_query = """
        SELECT COUNT(*) FROM sportsbook_matches m
        LEFT JOIN sportsbook_odds o ON m.id = o.match_id
        WHERE o.id IS NULL
    """
    orphans = pd.read_sql(orphan_query, engine).iloc[0,0]
    if orphans > 0:
        issues.append(f"Matches without odds: {orphans}")

    print("\n" + "="*40)
    if issues:
        print("ISSUES FOUND:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("✓ All validations passed")

    return issues

if __name__ == "__main__":
    validate_all()
```

### 3. Coordinate Data Flow

Your job is to be the middleman:

1. **Alfie** produces CSVs → You validate → Send to **Dietrich**
2. **Dietrich** loads to DB → You validate DB
3. Report any issues back to data owner

Create a tracking doc `team/max/work/notes/data-flow-status.md`:

```markdown
# Data Flow Status - Week 1

## CSV Status

| CSV | Owner | Validated | Sent to Dietrich | Loaded |
|-----|-------|-----------|------------------|--------|
| sportsbook_matches.csv | Alfie | ⏳ | ⏳ | ⏳ |
| sportsbook_odds.csv | Alfie | ⏳ | ⏳ | ⏳ |
| nba_team_stats.csv | Miran | ⏳ | ⏳ | ⏳ |
| nba_player_stats.csv | Vansheeka | ⏳ | ⏳ | ⏳ |

## Issues Log

| Date | CSV | Issue | Owner | Status |
|------|-----|-------|-------|--------|
| | | | | |
```

---

## Who You Work With

| Person | Your Interaction | When |
|--------|-----------------|------|
| Alfie | Validate his CSVs before Dietrich gets them | Tue-Wed |
| Miran | Check her CSVs, help her fix format issues | Tue-Wed |
| Vansheeka | Check her team name list matches schema | Mon-Tue |
| Dietrich | Give him validated CSVs, validate DB after load | Wed-Thu |

---

## Resources

**Required Reading:**
- File structure: `docs/SOPs/file-structure.md`
- Modularity: `docs/SOPs/modularity-upgrades.md`
- Team SOPs: `docs/SOPs/team-sops.md`


**Libraries:**
- pandas: https://pandas.pydata.org/docs/
- SQLAlchemy: https://docs.sqlalchemy.org/

**Internal Docs:**
- CSV formats: `docs/reference/csv-formats.md` (from Dietrich)
- Database connection: `docs/guides/connecting-to-database.md`

**AI Tools:**
- Use Claude: "Write a pandas validation for checking decimal ranges"

---

## Done Checklist

- [ ] CSV validation script works for all 4 types
- [ ] Database validation script works
- [ ] At least one CSV validated and passed to Dietrich
- [ ] Database validated after Dietrich loads
- [ ] Data flow status doc updated

---

## Thursday Presentation (2 min)

1. Run CSV validation: `python scripts/validate_csv.py matches data/matches.csv`
2. Show pass/fail output
3. Run database validation
4. Show data flow status
