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

### 2026-02-04

- Set up CockroachDB cloud database (AWS, 10GB free tier) for team-shared data storage
- Migrated from SQLite to CockroachDB - updated connection.py to auto-detect database type
- Created historic data collection script (scripts/collect_historic_data.py) for NBA Polymarket data
- Set up cron job for nightly data collection at midnight
- Enhanced Polymarket collector with price history and events API support
- Discovered Polymarket limitation: closed markets don't retain price history
- Running initial historic collection now (~1000 NBA events, ~8000 markets)
- Next: Build continuous orderbook collector for live market snapshots

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
