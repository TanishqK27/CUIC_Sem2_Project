# Max's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:
```
/update-log max <description of work>
```

---

## Log Entries

### 2026-02-10

- Changes made: implemented append-only, resumable NBA data pipeline in `scripts/collect_nba_stats.py` (schema migration helpers, OT columns, per-game team stats, per-game/per-quarter player stats, injury event ingestion with games-missed calculation, checkpoints in `data/cache/nba/checkpoints.json`); added unit tests in `tests/test_nba_collect.py`; added `nba_api` and `nba-injury-report` to dependencies (`requirements.txt`, `pyproject.toml`); kicked off long-running data collection to backfill 2021-22 through 2026-02-10.
- Errors/issues encountered: initial run failed due to a type-hint issue (`int | pd.NA`), fixed and restarted; pytest not available in environment when attempting to run tests.

### 2026-02-07

- Changes made: created `scripts/collect_nba_stats.py` to pull team/player/game logs via `nba_api` with rate limiting; installed `nba_api`; generated `data/nba/nba_team_stats.csv`, `data/nba/nba_player_stats.csv`, and `data/nba/nba_game_logs.csv` for seasons 2021-22 through 2024-25; moved NBA CSVs into `data/nba/`.
- Errors/issues encountered: `docs/reference/csv-formats.md` missing; initial `nba_api` responses lacked expected columns (e.g., `TEAM_ABBREVIATION`, `HOME_W`, `OPP_PTS`, `GS`) requiring endpoint changes/NA fills; timeouts from `stats.nba.com` during game log collection; VS Code only displayed a partial CSV (large-file rendering), so full row counts were verified and `nba_game_logs.csv` regenerated to 4920 rows (1230 per season).

### 2026-02-06

- Errors encountered: VS Code/Pylance unresolved imports for `numpy` and `pytest` due to incorrect interpreter path; PowerShell activation blocked by execution policy; Pylance `reportArgumentType` for `rsi` tests because `list[int]` passed where `list[float]` was expected.
- Changes made: updated `.vscode/settings.json` to use Windows venv interpreter path and added `python.terminal.activateEnvironment` + `python.venvPath`; fixed RSI tests to use `list[float]` and committed as "Fix RSI test price types for Pylance".

### 2025-02-01

- Joined CUIC Quant Fund project

---

<!-- New entries will be added above this line -->
