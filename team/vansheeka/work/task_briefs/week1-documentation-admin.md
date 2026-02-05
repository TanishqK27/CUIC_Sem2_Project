# Week 1: Data Cleanliness Analysis

**Owner:** Vansheeka
**Deadline:** Thursday Feb 12
**Priority:** MEDIUM

---

## Your Role

Analyze the Railway database to understand what data we have, what's missing, and whether everything is clean and ready for modeling.

---

## Task 1: Database Inventory (Mon-Tue)

### What Data Exists?

Connect to Railway and document everything:

```python
# Connect to Railway
import pandas as pd
from sqlalchemy import create_engine
import os

engine = create_engine(os.environ['DATABASE_URL'])

# List all tables
tables_query = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
"""
tables = pd.read_sql(tables_query, engine)
print(tables)
```

For EACH table, document:
- Table name
- Row count
- Column names and types
- Date range of data
- Any obvious gaps

### Create Inventory Document

Create `docs/reference/data-inventory.md`:

```markdown
# Data Inventory - Railway Database

Last updated: [DATE]

## Tables Overview

| Table | Rows | Date Range | Status |
|-------|------|------------|--------|
| price_snapshots | 90,000+ | Jan-Feb 2026 | ✓ Complete |
| sportsbook_matches | 0 | - | ⏳ Pending (Alfie) |
| ... | ... | ... | ... |

## Table Details

### price_snapshots
- **Rows:** X
- **Columns:** [list]
- **Date range:** X to Y
- **Missing data:** [any gaps?]

### sportsbook_matches
- **Status:** Empty - waiting for Alfie's CSV
- **Expected:** Wed Feb 12
```

---

## Task 2: Data Quality Analysis (Tue-Thu)

### Analyze Existing Data

Focus on `price_snapshots` (the Polymarket data). Check:

**1. Completeness**
- Any NULL values? Which columns?
- Any events with missing snapshots?
- Time gaps between snapshots?

**2. Correctness**
- Probabilities between 0 and 1?
- Timestamps make sense?
- Event names consistent?

**3. Consistency**
- Same event spelled differently?
- Duplicate rows?
- Timezone issues?

### Create Analysis Notebook

Create `research/notebooks/analysis/data_quality.ipynb`:

```python
# Cell 1: Overview
"""
# Data Quality Analysis

Checking cleanliness of Railway database for modeling readiness.
"""

# Cell 2: Connect and count
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

engine = create_engine(os.environ['DATABASE_URL'])

# Get row counts for all tables
# ...

# Cell 3: NULL analysis
"""
## Missing Values
"""
df = pd.read_sql("SELECT * FROM price_snapshots LIMIT 10000", engine)
print("NULL counts:")
print(df.isnull().sum())

# Cell 4: Value ranges
"""
## Value Ranges
"""
# Check probabilities are 0-1
# Check timestamps are reasonable
# ...

# Cell 5: Duplicates
"""
## Duplicate Check
"""
# Check for duplicate rows
# ...

# Cell 6: Visualizations
"""
## Data Coverage
"""
# Plot: snapshots over time (are there gaps?)
# Plot: events by count
# Plot: NULL distribution
```

### Visualizations to Include

1. **Timeline chart** - When do we have data? Any gaps?
2. **Completeness heatmap** - Which columns have NULLs?
3. **Distribution plots** - Are values in expected ranges?

---

## Task 3: Status Tracking (Ongoing)

Keep `team/PROJECT_STATUS.md` updated:

```markdown
# Project Status - Week 1

## Data Status

| Dataset | Rows | Quality | Owner | Notes |
|---------|------|---------|-------|-------|
| price_snapshots | 90K | ✓ Clean | - | Ready |
| sportsbook_matches | 0 | ⏳ | Alfie | Wed |
| sportsbook_odds | 0 | ⏳ | Alfie | Wed |

## Infrastructure Status

| Component | Owner | Status |
|-----------|-------|--------|
| DB schemas | Dietrich | ⏳ |
| Backtester | James | ⏳ |
| ... | ... | ... |
```

---

## Who You Work With

| Person | Interaction | When |
|--------|-------------|------|
| Dietrich | Ask about table schemas | Mon |
| Max | Coordinate on validation | Wed |
| Everyone | Collect status updates | Daily |

---

## Resources

**Required Reading:**
- `docs/SOPs/file-structure.md`
- `docs/SOPs/modularity-upgrades.md`
- `docs/SOPs/team-sops.md`

**For Analysis:**
- pandas: https://pandas.pydata.org/docs/
- matplotlib: https://matplotlib.org/stable/gallery/

**Claude Code Prompts:**
- "Analyze DataFrame for NULL values and data quality"
- "Create data completeness visualization"
- "Check for duplicates and inconsistencies in pandas"

---

## Done Checklist

- [ ] Connected to Railway, listed all tables
- [ ] Data inventory document created
- [ ] Quality analysis notebook with findings
- [ ] At least 3 visualizations
- [ ] PROJECT_STATUS.md updated
- [ ] Reported any data issues found

---

## Thursday Presentation (2 min)

1. Show data inventory (what we have vs missing)
2. Show 1-2 quality visualizations
3. Report any issues found (NULLs, gaps, etc.)
