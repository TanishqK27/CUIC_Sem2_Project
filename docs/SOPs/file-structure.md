# File Structure & Where To Put Things

## Golden Rule

**Put files in the RIGHT place so merges are clean and everyone can find things.**

---

## Directory Structure

```
CUIC_Sem2_Project/
├── src/cuic_quant/           # PRODUCTION CODE (importable modules)
│   ├── data/                 # API clients
│   ├── strategies/           # Trading strategies (Week 4)
│   ├── metrics/              # Ben's metrics module
│   └── models/               # ML models (Week 4)
│
├── scripts/                  # STANDALONE SCRIPTS (run from command line)
│   ├── load_csv_to_railway.py      # Dietrich
│   ├── validate_csv.py             # Max
│   ├── validate_database.py        # Max
│   └── convert_odds_to_csv.py      # Alfie
│
├── tools/                    # NOTEBOOKS & UTILITIES
│   ├── backtester.ipynb            # James
│   ├── test_metrics.ipynb          # Ben
│   └── test_data_generator.py      # Mya
│
├── data/                     # DATA FILES (CSVs, local DBs)
│   ├── sportsbook_matches.csv      # Alfie produces
│   ├── sportsbook_odds.csv         # Alfie produces
│   ├── test_games.csv              # Mya produces
│   └── nba/                        # NBA stats CSVs
│
├── docs/                     # DOCUMENTATION
│   ├── reference/                  # Specs & formats
│   │   ├── csv-formats.md          # Dietrich
│   │   ├── strategy-interface.md   # James
│   │   ├── nba-teams.md            # Vansheeka
│   │   └── test-data.md            # Mya
│   └── SOPs/                       # Standard procedures
│
├── team/                     # TEAM FOLDERS (personal work)
│   └── <name>/
│       ├── LOG.md                  # Daily log
│       └── work/
│           ├── task_briefs/        # Your assignments
│           └── notes/              # Your scratch notes
│
└── tests/                    # UNIT TESTS (if writing tests)
```

---

## Who Puts What Where

| Person | Files They Create | Location |
|--------|------------------|----------|
| **Dietrich** | `load_csv_to_railway.py` | `scripts/` |
| **Dietrich** | `csv-formats.md` | `docs/reference/` |
| **James** | `backtester.ipynb` | `tools/` |
| **James** | `strategy-interface.md` | `docs/reference/` |
| **Ben** | `metrics/__init__.py` | `src/cuic_quant/metrics/` |
| **Ben** | `test_metrics.ipynb` | `tools/` |
| **Max** | `validate_csv.py`, `validate_database.py` | `scripts/` |
| **Alfie** | `convert_odds_to_csv.py` | `scripts/` |
| **Alfie** | `sportsbook_*.csv` | `data/` |
| **Mya** | `test_data_generator.py` | `tools/` |
| **Mya** | `test_games.csv` | `data/` |
| **Mya** | `test-data.md` | `docs/reference/` |
| **Miran** | Notes only | `team/miran/work/notes/` |
| **Vansheeka** | `nba-teams.md`, `PROJECT_STATUS.md` | `docs/reference/`, `team/` |
| **Isameel** | Bug reports only | `team/isameel/work/notes/` |

---

## Naming Conventions

**Scripts:** `verb_noun.py` → `validate_csv.py`, `load_data.py`

**Modules:** `noun.py` → `metrics.py`, `backtester.py`

**CSVs:** `noun_type.csv` → `sportsbook_matches.csv`, `test_games.csv`

**Docs:** `noun-noun.md` → `csv-formats.md`, `strategy-interface.md`

---

## Git Branch Rules

**For Week 1:** Everyone works on `main` (small team, coordinated)

**If conflicts arise:**
```bash
# Before pushing
git pull origin main
# Fix any conflicts
git add .
git commit -m "fix: resolve merge conflict in X"
git push origin main
```

**Don't create feature branches unless Tan says so.**

---

## Avoiding Merge Conflicts

1. **Don't edit the same file** - each person has their own files
2. **Pull before you push** - `git pull origin main` first
3. **Small commits** - commit often, don't batch huge changes
4. **Communicate** - if you need to edit someone else's file, tell them first

---

## File Ownership

| File/Directory | Owner | Others Can Edit? |
|----------------|-------|------------------|
| `src/cuic_quant/metrics/` | Ben | No - ask Ben |
| `tools/backtester.ipynb` | James | No - ask James |
| `scripts/load_csv_to_railway.py` | Dietrich | No - ask Dietrich |
| `scripts/validate_*.py` | Max | No - ask Max |
| `data/*.csv` | Alfie/Mya | No - they produce, others consume |
| `docs/reference/` | Shared | Yes - but coordinate |
| `team/<name>/` | That person | No - private |
