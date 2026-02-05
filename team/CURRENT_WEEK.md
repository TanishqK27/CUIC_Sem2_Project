# Week 1 Sprint: Feb 6-12, 2026

**Deadline:** Thursday Feb 12 (Presentation Day)
**Coordinator:** Miran (updates Daily Status tables below)

---

## Who Delivers What to Whom

```mermaid
flowchart TD
    MAX[Max] -->|3 NBA CSVs| DB[(Database)]
    ALFIE[Alfie] -->|2 Odds CSVs| DB

    DB -->|queries| EDA[EDA Notebooks]

    MYA[Mya] -->|test_games.csv| JAMES[James]
    JAMES -->|backtester| TEST[Ismaeel Tests]
    BEN[Ben] -->|metrics| TEST
```

**Key Deadlines:**
- **Fri 6:** Mya → James (test data)
- **Sun 8:** Max + Alfie → Dietrich (CSVs)
- **Tue 10:** James + Ben → Ismaeel (modules to test)

---

## Timeline (Gantt)

```mermaid
gantt
    title Week 1 Sprint Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %a %d

    section Data Collection
    NBA stats collection       :max1, 2026-02-06, 3d
    Validate & send CSVs       :max2, after max1, 1d
    OddsHarvester setup        :alf1, 2026-02-06, 1d
    Scrape odds data           :alf2, after alf1, 2d
    Validate & send CSVs       :alf3, after alf2, 1d

    section Database
    Create tables              :diet1, 2026-02-06, 2d
    Load CSVs                  :diet2, after max2, 1d
    Verify joins               :diet3, after diet2, 1d

    section Analysis Tools
    Test data generator        :crit, mya1, 2026-02-06, 1d
    Backtester with dummy      :jam1, 2026-02-06, 2d
    Integrate test data        :jam2, after mya1, 1d
    Document interface         :jam3, after jam2, 1d
    Metrics module             :ben1, 2026-02-06, 3d
    Integration + docs         :ben2, after ben1, 1d
    Test backtester            :isa1, after jam2, 2d
    Test metrics               :isa2, after ben1, 2d

    section EDA & Research
    Polymarket EDA             :diet4, after diet3, 2d
    Sportsbook EDA             :mya2, after alf3, 2d
    Find papers                :mir1, 2026-02-06, 3d
    Write summaries            :mir2, after mir1, 2d

    section Coordination
    Daily check-ins            :mir3, 2026-02-06, 7d
    Data inventory             :van1, 2026-02-08, 3d
    Meeting notes              :isa3, 2026-02-06, 7d

    section Milestones
    Test data ready            :milestone, m1, 2026-02-07, 0d
    CSVs delivered             :milestone, m2, 2026-02-09, 0d
    Database ready             :milestone, m3, 2026-02-10, 0d
    Presentation               :milestone, m4, 2026-02-12, 0d
```

---

## Handoff Schedule

| Day | Who | Delivers | To | Format |
|-----|-----|----------|-----|--------|
| **Fri 6** | Mya | `test_games.csv` | James | CSV with 20+ rows |
| **Sun 8** | Max | 3 NBA CSVs | Dietrich | `team_stats`, `player_stats`, `game_logs` |
| **Sun 8** | Alfie | 2 Odds CSVs | Dietrich | `matches`, `odds` |
| **Mon 9** | Dietrich | Database ready | Team | Railway PostgreSQL |
| **Tue 10** | James | Backtester | Ismaeel | Python module |
| **Tue 10** | Ben | Metrics | Ismaeel | Python module |
| **Wed 11** | Ismaeel | Bug reports | James/Ben | Markdown |
| **Thu 12** | All | Presentation | Tan | Ready |

---

## Stream Details

### Stream 1: Data Collection → Database

```mermaid
flowchart TB
    subgraph Friday-Saturday
        M1[Max: nba_api setup]
        A1[Alfie: Fork OddsHarvester]
    end

    subgraph Saturday-Sunday
        M2[Max: Collect 4 seasons]
        A2[Alfie: Scrape 2+ weeks odds]
    end

    subgraph Sunday
        M3[Max: Validate CSVs]
        A3[Alfie: Validate CSVs]
        D1[Dietrich: Tables ready]
    end

    subgraph Monday
        D2[Dietrich: Load all CSVs]
        D3[Dietrich: Verify joins work]
    end

    M1 --> M2 --> M3
    A1 --> A2 --> A3
    M3 -->|"3 CSVs"| D2
    A3 -->|"2 CSVs"| D2
    D1 --> D2 --> D3
```

**Key Join Column:** `team_abbr` (3-letter codes: LAL, BOS, MIA, etc.)

---

### Stream 2: Analysis Tools → Testing

```mermaid
flowchart TB
    subgraph "Friday (CRITICAL)"
        MYA[Mya: test_games.csv]
    end

    subgraph Friday-Sunday
        JAM1[James: Backtester with dummy data]
        BEN1[Ben: Metrics module]
    end

    subgraph Monday-Tuesday
        JAM2[James: Integrate real test data]
        BEN2[Ben: Add integration tests]
    end

    subgraph Tuesday-Wednesday
        ISA1[Ismaeel: Test backtester]
        ISA2[Ismaeel: Test metrics]
    end

    subgraph Wednesday
        BUGS[Bug reports to James/Ben]
    end

    MYA -->|"FRIDAY!"| JAM1
    JAM1 --> JAM2
    BEN1 --> BEN2
    JAM2 --> ISA1
    BEN2 --> ISA2
    ISA1 --> BUGS
    ISA2 --> BUGS
```

**Critical Path:** Mya's test data blocks James. Must deliver Friday.

---

### Stream 3: Research & EDA

```mermaid
flowchart TB
    subgraph "Parallel Research"
        MIR1[Miran: Find 3-5 papers]
        MIR2[Miran: Daily check-ins]
    end

    subgraph "After Database Ready"
        D_EDA[Dietrich: Polymarket EDA]
        M_EDA[Mya: Sportsbook EDA]
    end

    subgraph "Documentation"
        VAN[Vansheeka: Data inventory]
        ISA[Ismaeel: Meeting notes]
    end

    MIR1 --> MIR3[Paper summaries]
    D_EDA --> INSIGHTS[Research findings]
    M_EDA --> INSIGHTS
```

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| :white_check_mark: | Completed |
| :hourglass_flowing_sand: | In Progress |
| :x: | Blocked |
| :warning: | At Risk |

---

## Daily Status (Miran updates)

### Friday Feb 6
| Person | Status | Notes |
|--------|--------|-------|
| Max | | |
| Alfie | | |
| Dietrich | | |
| James | | |
| Ben | | |
| Mya | | |
| Ismaeel | | |
| Vansheeka | | |

### Saturday Feb 7
| Person | Status | Notes |
|--------|--------|-------|
| Max | | |
| Alfie | | |
| Dietrich | | |
| James | | |
| Ben | | |
| Mya | | |
| Ismaeel | | |
| Vansheeka | | |

### Sunday Feb 8
| Person | Status | Notes |
|--------|--------|-------|
| Max | | |
| Alfie | | |
| Dietrich | | |
| James | | |
| Ben | | |
| Mya | | |
| Ismaeel | | |
| Vansheeka | | |

---

## Escalation Path

**Blocked?** Tell Miran immediately → Miran escalates to Tan if critical.

**Missing handoff?** Don't wait. Use dummy data (see task briefs for formats).
