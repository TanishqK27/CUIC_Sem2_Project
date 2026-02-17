# Tan's Tasks

Personal task tracking for the CUIC Quant Fund project.

---

## In Progress

| Task | Priority | Started | Notes |
|------|----------|---------|-------|
| NBA prediction modeling | High | 2026-02-17 | Build on EDA findings, start with baseline models |

---

## To Do

### Research & Analysis

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| NBA model development | High | 2026-02-21 | Quantile regression, tier-stratified models |
| Polymarket trading strategy | Medium | 2026-02-24 | Based on microstructure findings |
| Cross-platform signal analysis | Medium | - | Combine Polymarket + sportsbook signals |

### Kalshi Integration

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Review Kalshi client implementation | Low | - | Check kalshi_client.py |
| Build Kalshi data collector | Low | - | Similar pattern to Polymarket |

### Team & Project Management

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Review team member PRs | Medium | Ongoing | Code review as PRs come in |
| Weekly standup summary | Medium | Weekly | Use /weekly-standup skill |

### DevOps & Infrastructure

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Set up CI/CD pipeline | Low | - | GitHub Actions (deprioritized) |
| Document database schema | Low | - | For team reference |

---

## Backlog

Items to tackle when time permits:

- [ ] Grafana dashboard for collection metrics
- [ ] Historical data export to Parquet files
- [ ] API rate limit monitoring
- [ ] Team onboarding documentation for database access

---

## Completed

| Task | Completed | Notes |
|------|-----------|-------|
| Polymarket NBA microstructure report | 2026-02-16 | 12-chapter LaTeX report, 67.9M events analyzed |
| Polymarket microstructure EDA notebook | 2026-02-15/16 | Orderbook, price dynamics, trade flow, temporal patterns |
| NBA player statistics EDA (rigorous) | 2026-02-14/15 | 136K rows, 5 seasons, publication-quality figures |
| Historic NBA data collection | 2026-02-14 | 136K player-game rows, 5 seasons collected |
| Assign research tasks to team | 2026-02-05 | Team members assigned and working |
| Follow up on task assignments | 2026-02-05 | All members have tasks |
| CockroachDB cloud database setup | 2026-02-04 | Team-shared database on AWS |
| Historic data collection script | 2026-02-04 | scripts/collect_historic_data.py |
| Cron job for nightly collection | 2026-02-04 | Runs at midnight |
| Polymarket client enhancements | 2026-02-04 | Price history, events API |
| Speak to team about preferences | 2026-02-04 | Discussed research areas |
| Repository initialization | 2026-02-01 | Complete structure |
| Documentation | 2026-02-01 | All platform guides |
| Team structure | 2026-02-01 | All member folders |
| Claude Code integration | 2026-02-01 | Skills and agents |

---

## Notes

- Dietrich handling Polymarket/sportsbook data collection on Railway (67.9M+ events)
- Focus shifting from infrastructure to modeling and strategy development
- NBA EDA complete - ready for prediction modeling phase
- Polymarket microstructure analysis complete - ready for trading strategy development
