# Task: Validate All Datasets

**Owner:** Isameel
**Deadline:** Feb 19 (Week 2)
**Priority:** High — catches issues before modeling

---

## What You're Building

Run Max's validation scripts on all data in Railway DB and document any issues found. Then work with the data owners to fix problems.

---

## Why This Matters

Bad data = bad models. You're the quality gatekeeper. Before anyone runs models, you verify the data is clean and complete.

---

## Exactly What You Must Deliver

### 1. Run Validation Scripts

Use Max's validation script from Week 1:

```bash
# Set database URL
export DATABASE_URL="postgresql://..."

# Run Max's validation
python scripts/validate_data.py
```

### 2. Extended Validation

Create your own extended validation notebook at `tools/data_quality_report.ipynb`:

```python
# Cell 1: Setup
"""
# Data Quality Report

Complete validation of all datasets in Railway DB.
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime

engine = create_engine(os.environ['DATABASE_URL'])

# Cell 2: Table Overview
"""
## Database Overview
"""

# Get all tables
tables_query = """
    SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name)))
    FROM information_schema.tables
    WHERE table_schema = 'public'
"""
tables = pd.read_sql(tables_query, engine)
print("Tables in database:")
for _, row in tables.iterrows():
    count = pd.read_sql(f"SELECT COUNT(*) FROM {row['table_name']}", engine).iloc[0,0]
    print(f"  {row['table_name']}: {count} rows")

# Cell 3: Sportsbook Matches Validation
"""
## Sportsbook Matches
"""

matches = pd.read_sql("SELECT * FROM sportsbook_matches", engine)

issues = []

# Check 1: Missing values
null_cols = matches.isnull().sum()
for col, count in null_cols.items():
    if count > 0:
        issues.append(f"NULL in {col}: {count} rows")

# Check 2: Team name consistency
all_teams = set(matches['home_team'].unique()) | set(matches['away_team'].unique())
print(f"Unique teams: {len(all_teams)}")

# Look for duplicates/variations
team_variations = [t for t in all_teams if 'laker' in t.lower()]
if len(team_variations) > 1:
    issues.append(f"Team name variations: {team_variations}")

# Check 3: Date range
print(f"Date range: {matches['commence_time'].min()} to {matches['commence_time'].max()}")

print(f"\nIssues found: {len(issues)}")
for issue in issues:
    print(f"  - {issue}")

# Cell 4: Sportsbook Odds Validation
"""
## Sportsbook Odds
"""

odds = pd.read_sql("SELECT * FROM sportsbook_odds", engine)

issues = []

# Check 1: Odds range (should be 1.01 to ~20 for moneyline)
weird_home = ((odds['home_odds'] < 1.01) | (odds['home_odds'] > 50)).sum()
weird_away = ((odds['away_odds'] < 1.01) | (odds['away_odds'] > 50)).sum()
if weird_home > 0:
    issues.append(f"Suspicious home_odds: {weird_home} rows")
if weird_away > 0:
    issues.append(f"Suspicious away_odds: {weird_away} rows")

# Check 2: Overround (should be 100-110%)
odds['overround'] = (1/odds['home_odds'] + 1/odds['away_odds']) * 100
weird_or = ((odds['overround'] < 100) | (odds['overround'] > 115)).sum()
if weird_or > 0:
    issues.append(f"Weird overround (not 100-115%): {weird_or} rows")

# Check 3: Bookmaker distribution
print("\nBookmaker counts:")
print(odds['bookmaker'].value_counts())

print(f"\nIssues found: {len(issues)}")
for issue in issues:
    print(f"  - {issue}")

# Cell 5: NBA Team Stats Validation
"""
## NBA Team Stats
"""

try:
    team_stats = pd.read_sql("SELECT * FROM nba_team_stats", engine)

    issues = []

    # Check 1: All 30 teams present
    if len(team_stats) != 30:
        issues.append(f"Expected 30 teams, got {len(team_stats)}")

    # Check 2: Win % in valid range
    bad_wp = ((team_stats['win_pct'] < 0) | (team_stats['win_pct'] > 1)).sum()
    if bad_wp > 0:
        issues.append(f"Win % out of range: {bad_wp}")

    # Check 3: PPG sanity (NBA average is ~110-115)
    avg_ppg = team_stats['ppg'].mean()
    if avg_ppg < 100 or avg_ppg > 125:
        issues.append(f"Average PPG looks wrong: {avg_ppg:.1f}")

    print(f"Teams: {len(team_stats)}")
    print(f"Average PPG: {avg_ppg:.1f}")
    print(f"\nIssues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

except Exception as e:
    print(f"Could not validate nba_team_stats: {e}")

# Cell 6: NBA Player Stats Validation
"""
## NBA Player Stats
"""

try:
    player_stats = pd.read_sql("SELECT * FROM nba_player_stats", engine)

    issues = []

    # Check 1: Reasonable number of players
    if len(player_stats) < 300:
        issues.append(f"Too few players: {len(player_stats)}")

    # Check 2: PPG range (0-40 is reasonable)
    bad_ppg = ((player_stats['ppg'] < 0) | (player_stats['ppg'] > 45)).sum()
    if bad_ppg > 0:
        issues.append(f"PPG out of range: {bad_ppg}")

    # Check 3: All teams represented
    teams_in_player = player_stats['team_abbr'].nunique()
    if teams_in_player < 30:
        issues.append(f"Missing teams in player stats: only {teams_in_player}")

    print(f"Players: {len(player_stats)}")
    print(f"Teams represented: {teams_in_player}")
    print(f"\nIssues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

except Exception as e:
    print(f"Could not validate nba_player_stats: {e}")

# Cell 7: Cross-Table Validation
"""
## Cross-Table Checks

Do tables link correctly?
"""

# Check: Team names match between tables
match_teams = set(matches['home_team'].unique()) | set(matches['away_team'].unique())

try:
    team_stat_names = set(team_stats['team_name'].unique())
    missing_in_stats = match_teams - team_stat_names
    if missing_in_stats:
        print(f"Teams in matches but not in team_stats: {missing_in_stats}")
except:
    print("Could not compare team names")

# Check: Matches have odds
orphan_query = """
    SELECT COUNT(*)
    FROM sportsbook_matches m
    LEFT JOIN sportsbook_odds o ON m.id = o.match_id
    WHERE o.id IS NULL
"""
orphans = pd.read_sql(orphan_query, engine).iloc[0,0]
print(f"Matches without odds: {orphans}")

# Cell 8: Summary Report
"""
## Summary Report
"""

report = f"""
# Data Quality Report
Generated: {datetime.now()}

## Table Counts
- sportsbook_matches: {len(matches)}
- sportsbook_odds: {len(odds)}
- nba_team_stats: {len(team_stats) if 'team_stats' in dir() else 'N/A'}
- nba_player_stats: {len(player_stats) if 'player_stats' in dir() else 'N/A'}

## Critical Issues
[List any CRITICAL issues here]

## Warnings
[List any warnings here]

## Recommendations
1. [Action item 1]
2. [Action item 2]

## Sign-off
Validated by: Isameel
Date: {datetime.now().date()}
"""

print(report)
```

### 3. Document Issues

Create `team/isameel/work/notes/data-issues-log.md`:

```markdown
# Data Issues Log

## Validation Run: [DATE]

### Critical Issues (Must Fix)

| Table | Issue | Owner | Status |
|-------|-------|-------|--------|
| sportsbook_odds | X rows with odds < 1.01 | Alfie | Open |
| nba_team_stats | Missing 2 teams | Miran | Open |

### Warnings (Should Fix)

| Table | Issue | Owner | Status |
|-------|-------|-------|--------|
| sportsbook_matches | Team name variations | Max | Open |

### Notes

- [Any observations]

### Actions Taken

1. Notified Alfie about odds issue
2. [...]
```

### 4. Communicate Issues

For each issue found:
1. Identify the owner (who loaded that data)
2. Tell them specifically what's wrong
3. Track when it's fixed

---

## Done Checklist

- [ ] Ran Max's validation script
- [ ] Created extended validation notebook
- [ ] Validated all 4 main tables
- [ ] Cross-table checks completed
- [ ] Issues documented with owners
- [ ] Notified owners of issues
- [ ] Summary report generated

---

## What You Will Present (Thursday Feb 19)

**Live demo showing:**
1. Run the validation notebook
2. Show summary: how many rows in each table
3. Show any critical issues found
4. Explain what needs to be fixed

**Duration:** 2 minutes max

---

## Resources

- Max's validation script: `scripts/validate_data.py`
- Database connection: `docs/guides/connecting-to-database.md`

---

## Who To Ask If Stuck

1. Max — he wrote the initial validation
2. Dietrich — database schema questions
3. The data owner for each table
4. Tan — if unsure if something is an issue
