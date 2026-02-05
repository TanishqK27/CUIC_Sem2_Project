# Week 1: Documentation & Admin

**Owner:** Vansheeka
**Deadline:** Thursday Feb 12
**Priority:** MEDIUM — support role

---

## Your Role

You handle **documentation and administrative tasks**. You create reference documents that the team needs, and help track project progress.

**NO CODING REQUIRED** — this is documentation and admin work.

---

## This Week's Deliverables

### 1. NBA Team Reference Document

Create `docs/reference/nba-teams.md`:

```markdown
# NBA Teams Reference

## All 30 Teams

| Team Name | Abbreviation | City | Conference |
|-----------|--------------|------|------------|
| Atlanta Hawks | ATL | Atlanta | East |
| Boston Celtics | BOS | Boston | East |
| Brooklyn Nets | BKN | Brooklyn | East |
| Charlotte Hornets | CHA | Charlotte | East |
| Chicago Bulls | CHI | Chicago | East |
| Cleveland Cavaliers | CLE | Cleveland | East |
| Dallas Mavericks | DAL | Dallas | West |
| Denver Nuggets | DEN | Denver | West |
| Detroit Pistons | DET | Detroit | East |
| Golden State Warriors | GSW | San Francisco | West |
| Houston Rockets | HOU | Houston | West |
| Indiana Pacers | IND | Indianapolis | East |
| Los Angeles Clippers | LAC | Los Angeles | West |
| Los Angeles Lakers | LAL | Los Angeles | West |
| Memphis Grizzlies | MEM | Memphis | West |
| Miami Heat | MIA | Miami | East |
| Milwaukee Bucks | MIL | Milwaukee | East |
| Minnesota Timberwolves | MIN | Minneapolis | West |
| New Orleans Pelicans | NOP | New Orleans | West |
| New York Knicks | NYK | New York | East |
| Oklahoma City Thunder | OKC | Oklahoma City | West |
| Orlando Magic | ORL | Orlando | East |
| Philadelphia 76ers | PHI | Philadelphia | East |
| Phoenix Suns | PHX | Phoenix | West |
| Portland Trail Blazers | POR | Portland | West |
| Sacramento Kings | SAC | Sacramento | West |
| San Antonio Spurs | SAS | San Antonio | West |
| Toronto Raptors | TOR | Toronto | East |
| Utah Jazz | UTA | Salt Lake City | West |
| Washington Wizards | WAS | Washington | East |

## Name Variations to Watch For

Some scrapers use different names. Map these to official names:

| Variation | Official Name |
|-----------|---------------|
| LA Lakers | Los Angeles Lakers |
| LA Clippers | Los Angeles Clippers |
| GS Warriors | Golden State Warriors |
| NY Knicks | New York Knicks |
| NO Pelicans | New Orleans Pelicans |
| OKC Thunder | Oklahoma City Thunder |
| SA Spurs | San Antonio Spurs |

## Notes

- Always use full team names in database
- Abbreviations are for display only
- If unsure, check NBA.com official roster
```

### 2. Project Progress Tracker

Create `team/PROJECT_STATUS.md`:

```markdown
# Project Status - Week 1

Last updated: [DATE]

## Infrastructure Status

| Component | Owner | Status | Notes |
|-----------|-------|--------|-------|
| Railway DB schemas | Dietrich | ⏳ | |
| CSV loader script | Dietrich | ⏳ | |
| Sportsbook data | Alfie | ⏳ | |
| Data validation | Max | ⏳ | |
| Backtester core | James | ⏳ | |
| Metrics module | Ben | ⏳ | |
| Test data | Mya | ⏳ | |

## Data Status

| Dataset | Rows | Last Updated | Validated |
|---------|------|--------------|-----------|
| sportsbook_matches | 0 | - | No |
| sportsbook_odds | 0 | - | No |
| nba_team_stats | 0 | - | No |
| nba_player_stats | 0 | - | No |

## Blockers

| Blocker | Owner | Blocking | Status |
|---------|-------|----------|--------|
| | | | |

## Thursday Meeting Agenda

1. Dietrich - DB setup (2 min)
2. James - Backtester (2 min)
3. Ben - Metrics (2 min)
4. Alfie - Data collection (2 min)
5. Max - Validation (2 min)
6. Mya - Test data (2 min)
7. Miran - Handoffs (1 min)
8. Vansheeka - Status (1 min)
9. Isameel - Testing (1 min)
```

### 3. Meeting Notes Template

Create `team/meeting-notes/week1-feb12.md`:

```markdown
# Week 1 Meeting Notes - Feb 12, 2026

## Attendees
- [ ] Tan
- [ ] Dietrich
- [ ] James
- [ ] Ben
- [ ] Max
- [ ] Alfie
- [ ] Mya
- [ ] Miran
- [ ] Vansheeka
- [ ] Isameel

## Presentations

### Dietrich - Database
- Status:
- Demo:
- Issues:

### James - Backtester
- Status:
- Demo:
- Issues:

### Ben - Metrics
- Status:
- Demo:
- Issues:

### Alfie - Data
- Status:
- Demo:
- Issues:

### Max - Validation
- Status:
- Demo:
- Issues:

### Mya - Test Data
- Status:
- Demo:
- Issues:

### Miran - Handoffs
- Status:

### Isameel - Testing
- Status:

## Action Items for Week 2

| Action | Owner | Due |
|--------|-------|-----|
| | | |

## Blockers for Tan

| Issue | Who | Notes |
|-------|-----|-------|
| | | |
```

### 4. Daily Status Collection

Every day, ping each person and update PROJECT_STATUS.md:
- **Monday:** Check who has started
- **Tuesday:** Check progress
- **Wednesday:** Check blockers
- **Thursday AM:** Final status before meeting

---

## Who You Work With

| Person | Your Job | When |
|--------|----------|------|
| Everyone | Collect status updates | Daily |
| Miran | Coordinate on team names doc | Mon |
| Tan | Report blockers | As needed |

---

## Resources

**Required Reading:**
- File structure: `docs/SOPs/file-structure.md`
- Modularity: `docs/SOPs/modularity-upgrades.md`
- Team SOPs: `docs/SOPs/team-sops.md`


**NBA Reference:**
- Official teams: https://www.nba.com/teams
- Team abbreviations: https://en.wikipedia.org/wiki/Wikipedia:WikiProject_National_Basketball_Association/National_Basketball_Association_team_abbreviations

**Tools:**
- Google Docs/Sheets for tracking
- Slack/Discord for status pings

---

## Done Checklist

- [ ] NBA teams reference doc created
- [ ] PROJECT_STATUS.md created and maintained
- [ ] Meeting notes template ready
- [ ] Collected status from everyone at least once
- [ ] Blockers reported to Tan

---

## Thursday Presentation (1 min)

1. Show PROJECT_STATUS.md
2. Highlight any blockers
3. Confirm meeting notes template ready
