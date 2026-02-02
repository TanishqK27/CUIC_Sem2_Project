# Slash Commands Reference

Quick reference for all custom Claude Code slash commands available in this project.

---

## Available Commands

### /update-log

Updates your personal `LOG.md` and the shared `PROJECT_LOG.md` with timestamped entries.

**Usage:**
```
/update-log <name> <message>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `name` | Your name (lowercase): tan, andrii, dietrich, ben, alfie, max, miran, mya, isameel, vansheeka |
| `message` | Description of work completed |

**Examples:**
```
/update-log tan Completed Polymarket API client implementation
/update-log andrii Added unit tests for Kelly criterion
/update-log mya Fixed bug in arbitrage detection
```

**What it does:**
1. Adds entry to `team/<name>/LOG.md` under today's date
2. Adds attributed entry to `team/PROJECT_LOG.md`
3. Creates date section if it doesn't exist

---

### /research-template

Creates a new Jupyter notebook from the project research template.

**Usage:**
```
/research-template <category> <name>
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `category` | One of: `polymarket`, `kalshi`, `sports`, `exploratory` |
| `name` | Notebook name in kebab-case (e.g., `market-efficiency`) |

**Examples:**
```
/research-template polymarket market-efficiency
/research-template kalshi weather-contracts
/research-template sports nba-over-under
/research-template exploratory cross-market-correlation
```

**What it does:**
1. Copies `research/notebooks/templates/research_template.ipynb`
2. Places it in `research/notebooks/<category>/<name>.ipynb`
3. Updates title, category, and creation date metadata

**Categories explained:**
| Category | Use For |
|----------|---------|
| `polymarket` | Polymarket prediction market research |
| `kalshi` | Kalshi event contracts research |
| `sports` | Sports betting and odds analysis |
| `exploratory` | Cross-platform or general research |

---

### /weekly-standup

Generates a weekly progress summary from all team member logs.

**Usage:**
```
/weekly-standup
```

**No arguments required.**

**What it does:**
1. Reads all `team/<name>/LOG.md` files
2. Extracts entries from the past 7 days
3. Generates a formatted summary with:
   - Activity by team member
   - Summary statistics
   - Active member count

**Example output:**
```markdown
# Weekly Standup Summary

**Week of:** 2025-01-27 to 2025-02-02

## Team Activity

### tan
- Completed API client implementation
- Fixed rate limiting bug

### andrii
- Added Kelly criterion tests

### dietrich
*No activity this week*

## Summary Statistics
- **Total entries:** 3
- **Active members:** 2 / 10
- **Most active:** tan (2 entries)
```

---

## Quick Reference Table

| Command | Purpose | Example |
|---------|---------|---------|
| `/update-log` | Log your daily work | `/update-log tan Fixed API bug` |
| `/research-template` | Create research notebook | `/research-template polymarket price-discovery` |
| `/weekly-standup` | Generate team summary | `/weekly-standup` |

---

## Tips

### When to use /update-log
- After completing a task or milestone
- When switching to a different task
- At the end of a work session

### When to use /research-template
- Starting a new research investigation
- Exploring a new dataset or API
- Testing a hypothesis

### When to use /weekly-standup
- Before team meetings
- For progress reviews
- To check team activity levels

---

## File Locations

| File | Purpose |
|------|---------|
| `team/<name>/LOG.md` | Personal work log |
| `team/PROJECT_LOG.md` | Aggregated project log |
| `research/notebooks/<category>/` | Research notebooks |
| `research/notebooks/templates/` | Notebook templates |

---

## Troubleshooting

**"Invalid name" error with /update-log:**
- Use lowercase names only
- Valid names: tan, andrii, dietrich, ben, alfie, max, miran, mya, isameel, vansheeka

**"Invalid category" error with /research-template:**
- Valid categories: polymarket, kalshi, sports, exploratory

**No entries showing in /weekly-standup:**
- Check that LOG.md files use format `### YYYY-MM-DD` for date headers
- Entries must be from the past 7 days

