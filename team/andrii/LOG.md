# Andrii's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:

```bash
/update-log andrii <description of work>
```

---

## Log Entries

### 2026-02-25

- Created NBA Data Understanding & Audit notebook — forensic exploration of `combined_player_stats` (137k rows, 428 cols)
- Analysed 6 information layers: core box score, per-quarter, advanced, hustle/tracking, pregame features, availability
- Built data dictionary with column meanings, fill rates, and plain-English descriptions
- Investigated coverage gaps (2023-24 season 13% incomplete), missingness patterns (hustle stats game-level), PACE corruption
- Quantified 8 research edge hypotheses: early-season mispricing, hustle alpha, Q1 live betting, trade system change, B2B fatigue, blowout distortion, rookie uncertainty, overlooked tracking features
- Produced polished readable notebook (`NBA_Data_Understanding_and_Audit_READABLE.ipynb`) and PDF report (`NBA_Data_Understanding_and_Audit_Report.pdf`)

### 2026-02-16

- Refactored cleaning pipeline based on code review feedback
- Fixed Step 2b: added `unidecode` for accent-normalized name matching (e.g. Dončić vs Doncic)
- Fixed Step 2e: COVID-era threshold (12 players for 2020-22 seasons vs 16 normal)
- Removed Step 3 (minutes filter) — keeping all played rows preserves bench player variance
- Removed Steps 5, 6, 7 — keeping OT, quarter, and all columns (useful for live betting, storage is cheap)
- Removed Step 8 — rate stats with 0 denominator stay NaN (not 0)
- Fixed Step 5 (was 10): per-player expanding median with shift(1) to avoid data leakage
- Set correlation filter to suggestion mode (`AUTO_DROP=False`) — feature selection, not cleaning
- Moved DATABASE_URL to env var, added game_id as sort key for determinism

### 2026-02-15

- Built NBA data cleaning pipeline in `team/andrii/work/cleaning_data.ipynb`
- Connected to Dietrich's Railway PostgreSQL database (combined_player_stats: 136k rows, 428 columns)
- Implemented 10-step cleaning process:
  - Filter DNP(Did not play) rows, remove duplicates, misspelled name detection (difflib)
  - Outlier detection for impossible stat values (inspired by MA2502 comp stats)
  - Logical consistency checks (fgm <= fga, points formula, rebounds add up)
  - Incomplete game detection (flag games with < 16 players)
  - Minutes conversion (MM:SS to decimal) and threshold filter (>= 10 min) (more than 10 minutes played in the match)
  - Added flags: is_overtime, is_blowout, games_into_season
  - Dropped overtime, per-quarter, and redundant columns (~200 cols removed)
  - Configurable correlation filter with suggestion mode
  - Early-season NaN handling for pregame averages
- Researched NBA data cleaning best practices and adapted techniques from MA2502 NBA_Data_Preparation notebook (Computational Statistics module )

### 2026-02-14

- Hello world

### 2025-02-01

- Joined CUIC Quant Fund project

---

<!-- New entries will be added above this line -->
