# Tan's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:
```
/update-log tan <description of work>
```

Or use Tan's personal skill (no name needed):
```
/tan-update-log <description of work>
```

---

## Log Entries

### 2026-02-14

- Created rigorous EDA notebook for NBA player statistics
- Connected to CockroachDB cloud database: 136,965 rows × 428 columns
- Data spans 5 NBA seasons (2021-22 through 2025-26)
- Implemented comprehensive data quality assessment:
  - Missing data analysis with mechanism classification (MCAR/MAR/MNAR)
  - Pregame averages structurally missing for first games (MNAR)
  - Tracking stats ~15-20% missing (MAR)
  - Outlier detection using IQR method (no data integrity issues found)
- Univariate distribution analysis:
  - Target variables (PTS, REB, AST) right-skewed, non-normal
  - Bootstrap confidence intervals for means (n=1000 iterations)
  - Points: mean ~10, high variance (CV ≈ 0.8-1.0)
- Column categorization: identifiers, boxscore, advanced, pregame (player/team), quarter stats
- Data integrity checks: duplicate detection, value range validation, quarter sum consistency
- Set up publication-quality figure settings (colorblind-friendly Okabe-Ito palette)

### 2026-02-05

- Removed Polymarket data collection infrastructure - team member has shared server for queries
- Cleaned up codebase to focus on OddsHarvester and Kalshi integrations
- Removed: API client, collector, database models, notebooks, documentation, and tests
- Kept: Core strategies (arbitrage, kelly, mean_reversion), Kalshi client, OddsAPI client

### 2026-02-04

- Set up CockroachDB cloud database (AWS, 10GB free tier) for team-shared data storage
- Migrated from SQLite to CockroachDB - updated connection.py to auto-detect database type

### 2026-02-02

- Updated personal TASKS.md with team coordination tasks (speak to members, assign research tasks) due 4th Feb
- Added 25 research tasks to PROJECT_TASKS.md covering data sources, strategies, platforms, and literature reviews
- Added James to the team - created team/james/ folder with LOG.md and TASKS.md, updated all config files

### 2026-02-01

- Initialized project repository with complete structure
- Created comprehensive documentation for platforms (Polymarket, Kalshi, Sports Betting)
- Set up development tooling (pyproject.toml, pre-commit, ruff)
- Created team organization structure
- Implemented Claude Code skills for team workflow
- Committed initial infrastructure to main branch (72 files, 11k+ lines)
- Created personal `/tan-update-log` skill for quick log updates

---

<!-- New entries will be added above this line -->
