# Alfie's Tasks

## Week 1: Odds Collection + Validation (Feb 6-12)

### To Do
- [ ] Fork OddsHarvester repo and test locally
- [ ] Create `scripts/scrape_nba_odds.py` wrapper script
- [ ] Scrape NBA odds data (at least 2 weeks of games)
- [ ] Generate `data/raw/sportsbook_matches.csv`
- [ ] Generate `data/raw/sportsbook_odds.csv`
- [ ] Run `validate_matches_csv()` - pass all checks
- [ ] Run `validate_odds_csv()` - pass all checks
- [ ] Send validated CSVs to Dietrich for database loading
- [ ] Update `team/alfie/LOG.md` daily

### In Progress
| Task | Started | Notes |
|------|---------|-------|
| | | |

### Completed
| Task | Completed | Notes |
|------|-----------|-------|
| | | |

---

## Notes
- CSVs use `team_abbr` (3-letter codes: LAL, BOS, etc.) for database joins
- external_id format: `nba_{YYYYMMDD}_{away}_{home}`
- See `team/alfie/work/task_briefs/week1-odds-collection.md` for full spec
