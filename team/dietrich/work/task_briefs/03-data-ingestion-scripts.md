# Task: Data Ingestion Scripts

**Owner:** Dietrich
**Deadline:** Feb 12 (Week 1)
**Priority:** Medium — needed once schemas are ready

---

## What You're Building

Python scripts to bulk load CSV data into Railway PostgreSQL. Alfie, Miran, and Vansheeka will produce CSVs — your scripts load them.

---

## Why This Matters

Manual data loading doesn't scale. We need repeatable scripts that anyone can run to refresh data.

---

## Exactly What You Must Deliver

### 1. Ingestion Script

Create `scripts/load_data_to_railway.py` that:

```python
# Pseudocode structure
def load_sportsbook_odds(csv_path: str) -> int:
    """Load sportsbook odds CSV to Railway DB.

    Returns number of rows inserted.
    Handles duplicates (skip or update).
    """
    pass

def load_nba_team_stats(csv_path: str) -> int:
    """Load NBA team stats CSV to Railway DB."""
    pass

def load_nba_player_stats(csv_path: str) -> int:
    """Load NBA player stats CSV to Railway DB."""
    pass

if __name__ == "__main__":
    # CLI interface
    # python load_data_to_railway.py --type odds --file data/odds.csv
    pass
```

### 2. Features Required

- **Duplicate handling:** Skip rows that already exist (based on unique key)
- **Error handling:** Don't crash on bad rows, log and continue
- **Progress output:** Print how many rows loaded
- **Validation:** Basic checks (dates make sense, numbers are numbers)

### 3. Documentation

Add to script docstring or separate README:
- How to run it
- Expected CSV format for each data type
- What happens with duplicates
- Example commands

---

## Done Checklist

- [ ] Script created at `scripts/load_data_to_railway.py`
- [ ] Handles sportsbook odds CSVs
- [ ] Handles NBA team stats CSVs
- [ ] Handles NBA player stats CSVs
- [ ] Skips duplicates gracefully
- [ ] Logs errors without crashing
- [ ] Prints row counts
- [ ] Usage documented

---

## What You Will Present (Thursday Feb 12)

**Live demo showing:**
1. Run script on a sample CSV
2. Show rows appearing in Railway DB
3. Run again — show it handles duplicates

**Duration:** 2 minutes max

---

## Resources

- `psycopg2` for PostgreSQL connection
- Existing connection pattern: `src/cuic_quant/database/connection.py`

---

## Who To Ask If Stuck

1. Check existing database code in `src/cuic_quant/database/`
2. Tan — architecture decisions
