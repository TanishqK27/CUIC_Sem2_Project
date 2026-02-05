# Modularity & Upgrade Contracts

## Core Principle

**Everything is modular. When one component upgrades, dependent components must upgrade too.**

---

## Dependency Chain

```
Mya (test data) ──→ James (backtester) ──→ Ben (metrics) ──→ Ismaeel (testing)
                          ↑
Alfie (CSVs) ──→ Dietrich (DB) ──→ James (loads from DB)
```

---

## Upgrade Contracts

### If James Adds a New Column to Backtester Output

**Example:** James adds `strategy_name` column to results DataFrame

| Who | What They Must Do |
|-----|-------------------|
| James | 1. Update `strategy-interface.md` with new column |
| James | 2. Announce in chat: "Added `strategy_name` column" |
| Ben | 3. Update `calculate_all_metrics()` to handle new column (or ignore it) |
| Ismaeel | 4. Update test cases to include new column |

**James's responsibility:** Document the change, notify dependents
**Ben's responsibility:** Handle new columns gracefully (don't crash)

```python
# Ben's metrics should be defensive:
def calculate_all_metrics(trades_df: pd.DataFrame) -> dict:
    # Only use columns you need - ignore extras
    required = ['pnl', 'cumulative_pnl', 'outcome']
    # Don't crash if new columns added
```

---

### If Dietrich Adds a New Table/Column to Database

**Example:** Dietrich adds `game_outcome` column to `sportsbook_matches`

| Who | What They Must Do |
|-----|-------------------|
| Dietrich | 1. Update `csv-formats.md` with new column |
| Dietrich | 2. Update `load_csv_to_railway.py` to handle it |
| Dietrich | 3. Announce: "Added `game_outcome` column" |
| Alfie | 4. Update CSV production to include new column |
| Max | 5. Update validation to check new column |
| James | 6. Update `load_backtest_data()` query if needed |

---

### If Alfie Changes CSV Format

**Rule: Alfie CANNOT change CSV format without coordinating with Dietrich and Max first.**

| Step | Who | Action |
|------|-----|--------|
| 1 | Alfie | Propose change to Dietrich |
| 2 | Dietrich | Approve or reject |
| 3 | Dietrich | Update loader if approved |
| 4 | Max | Update validator |
| 5 | Alfie | Produce new format |

---

## Version Communication

When you change a format/interface:

1. **Update the doc** (`docs/reference/your-spec.md`)
2. **Add a version note:**
   ```markdown
   ## Changelog
   - v1.1 (Feb 14): Added `strategy_name` column
   - v1.0 (Feb 12): Initial version
   ```
3. **Announce in team chat** with:
   - What changed
   - Who needs to update
   - By when

---

## Defensive Coding Rules

### For Producers (James, Dietrich, Alfie, Mya)

```python
# ALWAYS output documented columns
# NEVER remove a column without coordination
# ADD new columns at the end
```

### For Consumers (Ben, Ismaeel, Max)

```python
# ONLY use columns you need
# DON'T crash on extra columns
# VALIDATE inputs exist before using

def calculate_metrics(df):
    required = ['pnl', 'outcome']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    # Now safe to proceed
```

---

## Example Upgrade Flow

**Scenario:** James wants to add Kelly sizing output

```
Day 1:
  James → Chat: "Planning to add 'kelly_fraction' column to backtester output"
  Ben → Chat: "OK, I'll ignore it for now, add metric later"
  Ismaeel → Chat: "I'll add test case for it"

Day 2:
  James: Updates backtester, updates strategy-interface.md
  James → Chat: "kelly_fraction column live, see updated docs"

Day 3:
  Ben: Tests metrics still work (they do, ignores new column)
  Ismaeel: Adds test for kelly_fraction

Week 2:
  Ben: Adds kelly_fraction to metrics if needed
```

---

## Quick Reference

| Change Type | Who Approves | Who Updates |
|-------------|--------------|-------------|
| New backtester column | James decides | Ben, Ismaeel adapt |
| New DB column | Dietrich decides | Alfie, Max, James adapt |
| New CSV column | Dietrich approves | Alfie produces, Max validates |
| New metric | Ben decides | Ismaeel tests |
| New test data column | Mya + James coordinate | Ismaeel uses |
