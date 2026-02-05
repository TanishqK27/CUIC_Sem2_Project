# Week 1 Sprint: Feb 6-12, 2026

**Deadline:** Thursday Feb 12 (Presentation Day)
**Coordinator:** Miran ([daily reports](progress_reports/week1.md))

---

## Dependency Overview

Three parallel streams converge into the final deliverable. Each node shows **who delivers what to whom**.

```mermaid
flowchart LR
    subgraph Stream1["Stream 1: Data Collection"]
        MAX[("Max\n─────────\nNBA Stats\n3 CSVs")]
        ALFIE[("Alfie\n─────────\nOdds Data\n2 CSVs")]
        DIETRICH_DB[("Dietrich\n─────────\nDatabase\n5 Tables")]
    end

    subgraph Stream2["Stream 2: Analysis Tools"]
        MYA_TEST[("Mya\n─────────\nTest Data\n1 CSV")]
        JAMES[("James\n─────────\nBacktester\nModule")]
        BEN[("Ben\n─────────\nMetrics\nModule")]
        ISAMEEL[("Isameel\n─────────\nQA Testing\nBug Reports")]
    end

    subgraph Stream3["Stream 3: Research & EDA"]
        DIETRICH_EDA[("Dietrich\n─────────\nPolymarket\nEDA")]
        MYA_EDA[("Mya\n─────────\nSportsbook\nEDA")]
        MIRAN[("Miran\n─────────\nPaper\nSummaries")]
    end

    MAX -->|"CSVs by Sun"| DIETRICH_DB
    ALFIE -->|"CSVs by Sun"| DIETRICH_DB
    ALFIE -->|"Odds CSV"| MYA_EDA
    MYA_TEST -->|"test_games.csv\nby Fri!"| JAMES
    JAMES -->|"backtester"| ISAMEEL
    BEN -->|"metrics"| ISAMEEL
    DIETRICH_DB -->|"DB ready Mon"| DIETRICH_EDA
    DIETRICH_DB -->|"DB ready Mon"| MYA_EDA
```

---

## Timeline (Gantt)

```mermaid
gantt
    title Week 1 Sprint Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %a %d

    section Data Collection
    Max: NBA stats collection       :max1, 2026-02-06, 3d
    Max: Validate & send CSVs       :max2, after max1, 1d
    Alfie: OddsHarvester setup      :alf1, 2026-02-06, 1d
    Alfie: Scrape odds data         :alf2, after alf1, 2d
    Alfie: Validate & send CSVs     :alf3, after alf2, 1d

    section Database
    Dietrich: Create tables         :diet1, 2026-02-06, 2d
    Dietrich: Load CSVs             :diet2, after max2, 1d
    Dietrich: Verify joins          :diet3, after diet2, 1d

    section Analysis Tools
    Mya: Test data generator        :crit, mya1, 2026-02-06, 1d
    James: Backtester with dummy    :jam1, 2026-02-06, 2d
    James: Integrate test data      :jam2, after mya1, 1d
    James: Document interface       :jam3, after jam2, 1d
    Ben: Metrics module             :ben1, 2026-02-06, 3d
    Ben: Integration + docs         :ben2, after ben1, 1d
    Isameel: Test backtester        :isa1, after jam2, 2d
    Isameel: Test metrics           :isa2, after ben1, 2d

    section EDA & Research
    Dietrich: Polymarket EDA        :diet4, after diet3, 2d
    Mya: Sportsbook EDA             :mya2, after alf3, 2d
    Miran: Find papers              :mir1, 2026-02-06, 3d
    Miran: Write summaries          :mir2, after mir1, 2d

    section Coordination
    Miran: Daily check-ins          :mir3, 2026-02-06, 7d
    Vansheeka: Data inventory       :van1, 2026-02-08, 3d
    Isameel: Meeting notes          :isa3, 2026-02-06, 7d

    section Milestones
    Test data to James              :milestone, crit, m1, 2026-02-07, 0d
    CSVs to Dietrich                :milestone, m2, 2026-02-09, 0d
    Database ready                  :milestone, m3, 2026-02-10, 0d
    Presentation                    :milestone, crit, m4, 2026-02-12, 0d
```

---

## Handoff Schedule

| Day | Who | Delivers | To | Format |
|-----|-----|----------|-----|--------|
| **Fri 6** | Mya | `test_games.csv` | James | CSV with 20+ rows |
| **Sun 8** | Max | 3 NBA CSVs | Dietrich | `team_stats`, `player_stats`, `game_logs` |
| **Sun 8** | Alfie | 2 Odds CSVs | Dietrich | `matches`, `odds` |
| **Mon 9** | Dietrich | Database ready | Team | Railway PostgreSQL |
| **Tue 10** | James | Backtester | Isameel | Python module |
| **Tue 10** | Ben | Metrics | Isameel | Python module |
| **Wed 11** | Isameel | Bug reports | James/Ben | Markdown |
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
        ISA1[Isameel: Test backtester]
        ISA2[Isameel: Test metrics]
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
        ISA[Isameel: Meeting notes]
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
| Isameel | | |
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
| Isameel | | |
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
| Isameel | | |
| Vansheeka | | |

---

## Escalation Path

**Blocked?** Tell Miran immediately → Miran escalates to Tan if critical.

**Missing handoff?** Don't wait. Use dummy data (see task briefs for formats).
