# Week 1 Sprint: Feb 6-12, 2026

**Deadline:** Thursday Feb 12 (Presentation Day)
**Coordinator:** Miran (updates Daily Status tables below)

---

## Who Delivers What to Whom

```mermaid
flowchart TD
    subgraph Data
        Max -->|NBA stats| Dietrich
        Alfie -->|Odds data| Dietrich
    end

    subgraph Tools
        Mya -->|Test data| James
        James -->|Backtester| Ismaeel
        Ben -->|Metrics| Ismaeel
    end

    subgraph Research
        Dietrich -->|Database| Mya
        Mya --> Analysis[Sportsbook Analysis]
        Dietrich --> Polymarket[Polymarket Analysis]
        Miran --> Papers[Paper Summaries]
    end

    subgraph Support
        Vansheeka --> Inventory[Data Inventory]
        Ismaeel --> Notes[Meeting Notes]
        Miran --> Updates[Daily Updates]
    end
```

**Key Deadlines:**

- **Friday:** Mya sends test data to James
- **Sunday:** Max and Alfie send data to Dietrich
- **Tuesday:** James and Ben send code to Ismaeel for testing

---

## Timeline (Gantt)

```mermaid
gantt
    title Week 1 Sprint (Fri 6 → Thu 12)
    dateFormat  YYYY-MM-DD
    axisFormat  %a %d

    section Data Team
    Max - Collect NBA stats          :max1, 2026-02-06, 2d
    Max - Validate and send          :max2, 2026-02-08, 1d
    Alfie - Setup scraper            :alf1, 2026-02-06, 1d
    Alfie - Scrape odds              :alf2, 2026-02-07, 2d
    Alfie - Validate and send        :alf3, 2026-02-09, 1d

    section Database Team
    Dietrich - Create tables         :diet1, 2026-02-06, 2d
    Dietrich - Load all data         :diet2, 2026-02-09, 1d
    Dietrich - Verify joins          :diet3, 2026-02-10, 1d
    Dietrich - Data analysis         :diet4, 2026-02-11, 1d

    section Tools Team
    Mya - Test data for James        :crit, mya1, 2026-02-06, 1d
    James - Build backtester         :jam1, 2026-02-06, 4d
    James - Write documentation      :jam2, 2026-02-10, 1d
    Ben - Build metrics module       :ben1, 2026-02-06, 4d
    Ben - Write documentation        :ben2, 2026-02-10, 1d
    Ismaeel - Test both modules      :isa1, 2026-02-10, 2d

    section Research Team
    Mya - Sportsbook analysis        :mya2, 2026-02-09, 3d
    Miran - Find research papers     :mir1, 2026-02-06, 4d
    Miran - Write paper summaries    :mir2, 2026-02-10, 2d
    Vansheeka - Data inventory       :van1, 2026-02-08, 4d

    section Coordination
    Miran - Daily check-ins          :mir3, 2026-02-06, 5d
    Ismaeel - Thursday meeting notes :isa2, 2026-02-12, 1d

    section Milestones
    Test data to James               :milestone, m1, 2026-02-06, 0d
    All data to Dietrich             :milestone, m2, 2026-02-09, 0d
    Database ready                   :milestone, m3, 2026-02-10, 0d
    Presentation day                 :milestone, m4, 2026-02-12, 0d
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
| Max | ✅ | Linux compatibility errors observed but have been resolved |
| Alfie | ⏳ | Starting Saturday |
| Dietrich | ⏳ | Waiting for data|
| James | ⏳ | Haven't started due to illness|
| Ben | ✅ | Finished task with dummy data, waiting on James for real data |
| Mya | ✅ | Test Data Generator + Sportsbook EDA Completed |
| Ismaeel | ✅ | Completed set up on VS. Created dummy back tester input and output |
| Vansheeka | ⏳ | Still setting up environment |

### Saturday Feb 7

| Person | Status | Notes |
|--------|--------|-------|
| Max | | |
| Alfie | ✅ | Woorked on 2010s data, on track for others |
| Dietrich | ⏳ | Still waiting |
| James | ⏳ | Still ill |
| Ben | ✅ | Path issues |
| Mya | ✅ | Waiting for Alfie |
| Ismaeel | ✅ | Everything going smoothly |
| Vansheeka | | |

### Sunday Feb 8

| Person | Status | Notes |
|--------|--------|-------|
| Max | | |
| Alfie | ✅ | Handed over to Diestrich|
| Dietrich | | |
| James | ⏳ | Still ill |
| Ben | ✅ | Updated log |
| Mya | | |
| Ismaeel | | |
| Vansheeka | | |

---

## Escalation Path

**Blocked?** Tell Miran immediately → Miran escalates to Tan if critical.

**Missing handoff?** Don't wait. Use dummy data (see task briefs for formats).
