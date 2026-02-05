# Task: Data Validation Scripts

**Owner:** Max
**Deadline:** Feb 12 (Week 1)
**Priority:** High — catches bad data early

---

## What You're Building

Python scripts that check data quality in Railway DB. Find missing values, duplicates, outliers, and formatting issues before they break our models.

---

## Why This Matters

"Garbage in, garbage out." If odds are stored as strings instead of numbers, or dates are formatted wrong, our backtester will crash or give wrong results. Validation catches problems early.

---

## Exactly What You Must Deliver

### 1. Validation Script

Create `scripts/validate_data.py`:

```python
"""Data validation for Railway PostgreSQL tables."""

import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime

def get_engine():
    """Get database connection."""
    return create_engine(os.environ['DATABASE_URL'])

def validate_sportsbook_matches() -> dict:
    """
    Validate sportsbook_matches table.

    Returns:
        dict with validation results
    """
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM sportsbook_matches", engine)

    issues = []

    # Check 1: Missing values
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            issues.append(f"NULL values in {col}: {count} rows")

    # Check 2: Duplicate external_ids
    dup_count = df['external_id'].duplicated().sum()
    if dup_count > 0:
        issues.append(f"Duplicate external_ids: {dup_count}")

    # Check 3: Future dates too far out (might be errors)
    future_cutoff = datetime.now() + pd.Timedelta(days=30)
    far_future = (df['commence_time'] > future_cutoff).sum()
    if far_future > 0:
        issues.append(f"Games more than 30 days in future: {far_future}")

    # Check 4: Team name consistency
    all_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
    print(f"  Unique teams found: {len(all_teams)}")

    return {
        'table': 'sportsbook_matches',
        'row_count': len(df),
        'issues': issues,
        'passed': len(issues) == 0
    }

def validate_sportsbook_odds() -> dict:
    """
    Validate sportsbook_odds table.

    Returns:
        dict with validation results
    """
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM sportsbook_odds", engine)

    issues = []

    # Check 1: Odds in valid range (1.01 to 100.0 is reasonable)
    invalid_home = ((df['home_odds'] < 1.01) | (df['home_odds'] > 100)).sum()
    invalid_away = ((df['away_odds'] < 1.01) | (df['away_odds'] > 100)).sum()
    if invalid_home > 0:
        issues.append(f"Home odds out of range: {invalid_home} rows")
    if invalid_away > 0:
        issues.append(f"Away odds out of range: {invalid_away} rows")

    # Check 2: Orphaned odds (no matching match)
    orphan_query = """
        SELECT COUNT(*)
        FROM sportsbook_odds o
        LEFT JOIN sportsbook_matches m ON o.match_id = m.id
        WHERE m.id IS NULL
    """
    orphans = pd.read_sql(orphan_query, engine).iloc[0, 0]
    if orphans > 0:
        issues.append(f"Orphaned odds (no match): {orphans} rows")

    # Check 3: Bookmaker values
    valid_bookmakers = ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet']
    unknown_books = df[~df['bookmaker'].isin(valid_bookmakers)]['bookmaker'].unique()
    if len(unknown_books) > 0:
        issues.append(f"Unknown bookmakers: {list(unknown_books)}")

    # Check 4: Overround sanity (should be 102-110%)
    df['overround'] = (1/df['home_odds'] + 1/df['away_odds']) * 100
    weird_overround = ((df['overround'] < 100) | (df['overround'] > 120)).sum()
    if weird_overround > 0:
        issues.append(f"Suspicious overround: {weird_overround} rows")

    return {
        'table': 'sportsbook_odds',
        'row_count': len(df),
        'issues': issues,
        'passed': len(issues) == 0
    }

def validate_nba_team_stats() -> dict:
    """Validate nba_team_stats table."""
    engine = get_engine()

    try:
        df = pd.read_sql("SELECT * FROM nba_team_stats", engine)
    except Exception as e:
        return {
            'table': 'nba_team_stats',
            'row_count': 0,
            'issues': [f"Table doesn't exist or error: {e}"],
            'passed': False
        }

    issues = []

    # Check 1: Missing values
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            issues.append(f"NULL values in {col}: {count}")

    # Check 2: Win percentage in valid range
    if 'win_pct' in df.columns:
        invalid_wp = ((df['win_pct'] < 0) | (df['win_pct'] > 1)).sum()
        if invalid_wp > 0:
            issues.append(f"Win pct out of range: {invalid_wp}")

    # Check 3: PPG sanity (should be 90-140 for NBA)
    if 'ppg' in df.columns:
        weird_ppg = ((df['ppg'] < 80) | (df['ppg'] > 150)).sum()
        if weird_ppg > 0:
            issues.append(f"Suspicious PPG: {weird_ppg}")

    return {
        'table': 'nba_team_stats',
        'row_count': len(df),
        'issues': issues,
        'passed': len(issues) == 0
    }

def validate_all() -> list:
    """Run all validations and print report."""
    results = []

    print("=" * 60)
    print("DATA VALIDATION REPORT")
    print(f"Run at: {datetime.now()}")
    print("=" * 60)

    validators = [
        validate_sportsbook_matches,
        validate_sportsbook_odds,
        validate_nba_team_stats,
    ]

    for validator in validators:
        print(f"\nValidating {validator.__name__}...")
        result = validator()
        results.append(result)

        status = "✓ PASSED" if result['passed'] else "✗ FAILED"
        print(f"  {result['table']}: {result['row_count']} rows - {status}")

        if result['issues']:
            for issue in result['issues']:
                print(f"    - {issue}")

    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r['passed'])
    print(f"SUMMARY: {passed}/{len(results)} tables passed validation")
    print("=" * 60)

    return results

if __name__ == "__main__":
    validate_all()
```

### 2. Run Validation

```bash
# Set database URL
export DATABASE_URL="postgresql://..."

# Run validation
python scripts/validate_data.py
```

Expected output:
```
============================================================
DATA VALIDATION REPORT
Run at: 2026-02-10 14:30:00
============================================================

Validating validate_sportsbook_matches...
  sportsbook_matches: 500 rows - ✓ PASSED

Validating validate_sportsbook_odds...
  sportsbook_odds: 2500 rows - ✗ FAILED
    - Unknown bookmakers: ['bet365']

Validating validate_nba_team_stats...
  nba_team_stats: 30 rows - ✓ PASSED

============================================================
SUMMARY: 2/3 tables passed validation
============================================================
```

### 3. Document Issues Found

Create `team/max/work/notes/data-issues-found.md`:

```markdown
# Data Issues Found

## Week 1 Validation (Date: ___)

### sportsbook_matches
- [ ] Issue 1: ...
- [ ] Issue 2: ...

### sportsbook_odds
- [ ] Issue 1: ...

### nba_team_stats
- [ ] Issue 1: ...

## Who Needs to Fix

| Issue | Owner | Status |
|-------|-------|--------|
| ... | Alfie | Open |
```

---

## Done Checklist

- [ ] Script created at `scripts/validate_data.py`
- [ ] Validates sportsbook_matches table
- [ ] Validates sportsbook_odds table
- [ ] Validates nba_team_stats table
- [ ] Clear output format showing pass/fail
- [ ] Issues list documented in your notes
- [ ] Told relevant team members about issues found

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Run the validation script
2. Show which tables passed/failed
3. Show one specific issue found
4. Explain how you'd fix it

**Duration:** 2 minutes max

---

## Resources

- pandas validation: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.isnull.html
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## Who To Ask If Stuck

1. Dietrich — database schema questions
2. Alfie — sportsbook data issues
3. Miran/Vansheeka — NBA stats issues
4. Tan — if unsure what counts as "valid"
