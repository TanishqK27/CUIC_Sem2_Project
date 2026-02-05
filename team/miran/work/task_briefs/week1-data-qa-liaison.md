# Week 1: Data QA & Liaison

**Owner:** Miran
**Deadline:** Thursday Feb 12
**Priority:** MEDIUM — support role

---

## Your Role

You are the **quality checker and communication bridge** between Alfie (who produces data) and Dietrich (who loads it). You manually check CSVs for obvious errors and ensure handoffs happen smoothly.

**NO CODING REQUIRED** — this is manual QA and communication work.

---

## This Week's Deliverables

### 1. Manual CSV Quality Check

When Alfie produces CSVs, manually open them and check:

**For sportsbook_matches.csv:**
- [ ] File opens without errors
- [ ] Has columns: external_id, home_team, away_team, commence_time
- [ ] Team names look correct (real NBA teams)
- [ ] Dates make sense (not 1970, not 2099)
- [ ] No obvious duplicates (same game twice)
- [ ] Count rows: should be 10+ games

**For sportsbook_odds.csv:**
- [ ] File opens without errors
- [ ] Has columns: external_id, bookmaker, home_odds, away_odds
- [ ] Odds look reasonable (between 1.1 and 10.0)
- [ ] Bookmaker names are valid (fanduel, draftkings, etc.)
- [ ] Each external_id has multiple bookmakers

**How to check:**
```
# Open in any spreadsheet app (Excel, Google Sheets)
# Or use command line:
head -20 data/sportsbook_matches.csv
wc -l data/sportsbook_matches.csv  # count rows
```

### 2. Communication Tracking

Create `team/miran/work/notes/handoff-tracker.md`:

```markdown
# Data Handoff Tracker - Week 1

## Status

| Step | Owner | Status | Date | Notes |
|------|-------|--------|------|-------|
| Alfie produces matches.csv | Alfie | ⏳ | | |
| Miran checks matches.csv | Miran | ⏳ | | |
| Max validates matches.csv | Max | ⏳ | | |
| Alfie produces odds.csv | Alfie | ⏳ | | |
| Miran checks odds.csv | Miran | ⏳ | | |
| Max validates odds.csv | Max | ⏳ | | |
| Dietrich receives CSVs | Dietrich | ⏳ | | |
| Dietrich loads to DB | Dietrich | ⏳ | | |
| Max validates DB | Max | ⏳ | | |

## Communication Log

| Date | From | To | Message |
|------|------|-----|---------|
| | | | |

## Issues Found

| Date | File | Issue | Reported To | Fixed? |
|------|------|-------|-------------|--------|
| | | | | |
```

### 3. Daily Check-ins

Your communication duties:
- **Monday PM:** Ask Alfie: "Do you have OddsHarvester working?"
- **Tuesday PM:** Ask Alfie: "When will CSVs be ready?"
- **Wednesday AM:** Check Alfie's CSVs manually
- **Wednesday PM:** Tell Max: "CSVs ready for validation" (or report issues)
- **Thursday AM:** Confirm with Dietrich: "Did loading work?"

### 4. Team Name Verification

Create a list of official NBA team names. Alfie's data must use EXACTLY these:

```markdown
# Official NBA Team Names

Use EXACTLY these names in CSVs:

1. Atlanta Hawks
2. Boston Celtics
3. Brooklyn Nets
4. Charlotte Hornets
5. Chicago Bulls
6. Cleveland Cavaliers
7. Dallas Mavericks
8. Denver Nuggets
9. Detroit Pistons
10. Golden State Warriors
11. Houston Rockets
12. Indiana Pacers
13. Los Angeles Clippers
14. Los Angeles Lakers
15. Memphis Grizzlies
16. Miami Heat
17. Milwaukee Bucks
18. Minnesota Timberwolves
19. New Orleans Pelicans
20. New York Knicks
21. Oklahoma City Thunder
22. Orlando Magic
23. Philadelphia 76ers
24. Phoenix Suns
25. Portland Trail Blazers
26. Sacramento Kings
27. San Antonio Spurs
28. Toronto Raptors
29. Utah Jazz
30. Washington Wizards
```

Check Alfie's CSV team names against this list.

---

## Who You Work With

| Person | Your Job | When |
|--------|----------|------|
| Alfie | Check his CSVs, report issues | Tue-Wed |
| Max | Tell him when CSVs ready | Wed |
| Dietrich | Confirm he received files | Thu |
| Vansheeka | Coordinate on team names | Mon-Tue |

---

## Resources

**Tools:**
- Excel or Google Sheets to open CSVs
- Terminal commands: `head`, `wc -l`, `grep`

**Internal Docs:**
- CSV format requirements: `docs/reference/csv-formats.md`

---

## Done Checklist

- [ ] Handoff tracker created and maintained
- [ ] Manually checked Alfie's matches.csv
- [ ] Manually checked Alfie's odds.csv
- [ ] Team names verified against official list
- [ ] Reported any issues to Alfie
- [ ] Confirmed Max got the files
- [ ] Confirmed Dietrich loaded successfully

---

## Thursday Presentation (1 min)

1. Show handoff tracker with all statuses
2. Report any issues found and fixed
3. Confirm data is in the database
