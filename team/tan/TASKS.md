# Tan's Tasks

Personal task tracking for the CUIC Quant Fund project.

---

## In Progress

| Task | Priority | Started | Notes |
|------|----------|---------|-------|
| Historic NBA data collection | High | 2026-02-04 | Running now via collect_historic_data.py |
| Assign research tasks to team | High | 2026-02-04 | Match tasks to team member interests |

---

## To Do

### Data Collection Infrastructure

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| **Build continuous orderbook collector** | High | 2026-02-06 | - |
| ↳ Design snapshot schema (bids/asks/depth) | - | - | Add to database models |
| ↳ Implement orderbook fetcher | - | - | Use CLOB API |
| ↳ Add scheduling logic (every 5-15 min) | - | - | APScheduler or cron |
| ↳ Test with live NBA markets | - | - | Verify data capture |
| **Deploy collectors to cloud** | Medium | 2026-02-07 | So it runs 24/7 |
| ↳ Choose platform (Railway/Render/EC2) | - | - | Free tier options |
| ↳ Dockerize collection scripts | - | - | Dockerfile |
| ↳ Set up environment secrets | - | - | DATABASE_URL etc |
| ↳ Configure monitoring/alerts | - | - | Know when it fails |

### OddsHarvester (Sports Betting Data)

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| **Build OddsHarvester collector** | High | 2026-02-08 | The Odds API integration |
| ↳ Review existing odds_api.py client | - | - | Check what's implemented |
| ↳ Design odds snapshot schema | - | - | Bookmaker, sport, odds, timestamp |
| ↳ Build historic odds collector | - | - | Backfill available data |
| ↳ Build live odds collector | - | - | Continuous snapshots |
| ↳ Add to CockroachDB | - | - | New tables for odds data |
| **Cross-platform arbitrage data** | Medium | 2026-02-10 | - |
| ↳ Map Polymarket events to sports matches | - | - | Link prediction markets to games |
| ↳ Align timestamps across sources | - | - | Standardize for comparison |

### Kalshi Integration

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Review Kalshi client implementation | Medium | 2026-02-09 | Check kalshi_client.py |
| Build Kalshi data collector | Medium | - | Similar pattern to Polymarket |
| Add Kalshi tables to database | Medium | - | Events, markets, prices |

### Team & Project Management

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Follow up on task assignments | High | 2026-02-05 | Ensure everyone has claimed a task |
| Review team member PRs | Medium | Ongoing | Code review as PRs come in |
| Weekly standup summary | Medium | 2026-02-07 | Use /weekly-standup skill |
| Update PROJECT_TASKS.md status | Low | Weekly | Track overall progress |

### DevOps & Infrastructure

| Task | Priority | Due | Notes |
|------|----------|-----|-------|
| Set up CI/CD pipeline | Low | 2026-02-14 | GitHub Actions |
| Add database backup script | Low | - | CockroachDB exports |
| Create data validation tests | Low | - | Ensure collection quality |
| Document database schema | Low | - | For team reference |

---

## Backlog

Items to tackle when time permits:

- [ ] Grafana dashboard for collection metrics
- [ ] Slack/Discord alerts for collection failures
- [ ] Historical data export to Parquet files
- [ ] API rate limit monitoring
- [ ] Cost tracking for cloud services
- [ ] Team onboarding documentation for database access

---

## Completed

| Task | Completed | Notes |
|------|-----------|-------|
| Polymarket NBA microstructure report | 2026-02-16 | 12-chapter LaTeX report, 67.9M events analyzed |
| Polymarket microstructure EDA notebook | 2026-02-15/16 | Orderbook, price dynamics, trade flow, temporal patterns |
| NBA player statistics EDA (rigorous) | 2026-02-14/15 | 136K rows, 5 seasons, publication-quality figures |
| CockroachDB cloud database setup | 2026-02-04 | Team-shared database on AWS |
| Historic data collection script | 2026-02-04 | scripts/collect_historic_data.py |
| Cron job for nightly collection | 2026-02-04 | Runs at midnight |
| Polymarket client enhancements | 2026-02-04 | Price history, events API |
| Speak to team about preferences | 2026-02-04 | Discussed research areas |
| Repository initialization | 2025-02-01 | Complete structure |
| Documentation | 2025-02-01 | All platform guides |
| Team structure | 2025-02-01 | All member folders |
| Claude Code integration | 2025-02-01 | Skills and agents |

---

## Notes

- Focus on infrastructure and enabling team productivity
- Priority order: Polymarket → OddsHarvester → Kalshi
- Get continuous collection running before expanding to new sources
- Coordinate with team on task assignments
