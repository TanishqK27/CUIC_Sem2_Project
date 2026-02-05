# OddsHarvester Integration Plan

**Date:** 2025-02-04
**Author:** Tan
**Status:** Ready for Implementation

---

## Executive Summary

Replace The Odds API with [OddsHarvester](https://github.com/jordantete/OddsHarvester) for sports betting odds collection. OddsHarvester is a free, open-source scraper for oddsportal.com that provides historical and upcoming odds across multiple bookmakers.

**Key Decision:** Build a data warehouse architecture mirroring the existing Polymarket infrastructure, enabling cross-platform analysis between prediction markets and traditional sportsbooks.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Schema](#2-database-schema)
3. [Component Specifications](#3-component-specifications)
4. [Unified Query Interface](#4-unified-query-interface)
5. [Implementation Tasks](#5-implementation-tasks)
6. [Technical Decisions](#6-technical-decisions)

---

## 1. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CUIC Quant Data Layer                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  COLLECTION LAYER                                                   │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │ PolymarketCollector     │    │ OddsHarvesterCollector  │        │
│  │ (existing)              │    │ (NEW)                   │        │
│  └───────────┬─────────────┘    └───────────┬─────────────┘        │
│              │                              │                       │
│              └──────────┬───────────────────┘                       │
│                         ▼                                           │
│              ┌─────────────────────┐                                │
│              │ CollectionScheduler │  (EXTEND existing)             │
│              │ - APScheduler       │                                │
│              │ - 8 parallel workers│                                │
│              │ - Proxy rotation    │                                │
│              └─────────────────────┘                                │
│                                                                     │
│  STORAGE LAYER                                                      │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │ polymarket.db           │    │ sports_odds.db          │        │
│  │ (existing)              │    │ (NEW)                   │        │
│  │ - MarketSnapshot        │    │ - matches               │        │
│  │ - PricePoint            │    │ - odds_snapshots        │        │
│  │ - CollectionRun         │    │ - sports, leagues       │        │
│  └───────────┬─────────────┘    └───────────┬─────────────┘        │
│              │                              │                       │
│              └──────────┬───────────────────┘                       │
│                         ▼                                           │
│  QUERY LAYER                                                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ UnifiedOddsClient                                       │       │
│  │ - Cross-platform queries                                │       │
│  │ - Market linking (Polymarket ↔ Sports)                  │       │
│  │ - Arbitrage detection                                   │       │
│  │ - DataFrame output for notebooks                        │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### File Structure

```
src/cuic_quant/
├── data/
│   ├── polymarket_client.py      # existing
│   ├── kalshi_client.py          # existing
│   ├── odds_api.py               # DEPRECATED - keep for reference
│   └── oddsharvester_client.py   # NEW - CLI wrapper
│
├── collector/
│   ├── __init__.py
│   ├── polymarket_collector.py   # existing
│   ├── oddsharvester_collector.py # NEW
│   └── scheduler.py              # EXTEND - add sports odds jobs
│
├── database/
│   ├── models.py                 # EXTEND - add sports odds models
│   ├── connection.py             # EXTEND - multi-db support
│   └── repositories/
│       ├── __init__.py
│       ├── market_repo.py        # existing (Polymarket)
│       └── sports_odds_repo.py   # NEW
│
└── analysis/
    └── unified_client.py         # NEW - cross-platform queries

data/
├── polymarket.db                 # existing
└── sports_odds.db                # NEW

configs/
└── oddsharvester/
    ├── proxies.txt               # proxy list for rotation
    └── leagues.yaml              # league configurations
```

---

## 2. Database Schema

### Sports Odds Database (`sports_odds.db`)

```sql
-- Reference tables (sport-agnostic design)

CREATE TABLE sports (
    id TEXT PRIMARY KEY,              -- 'basketball', 'football'
    name TEXT NOT NULL,               -- 'Basketball', 'Football'
    oddsharvester_key TEXT NOT NULL,  -- CLI flag: 'basketball'
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leagues (
    id TEXT PRIMARY KEY,              -- 'nba', 'premier-league'
    sport_id TEXT NOT NULL REFERENCES sports(id),
    name TEXT NOT NULL,               -- 'NBA', 'Premier League'
    country TEXT,                     -- 'USA', 'England'
    oddsharvester_key TEXT NOT NULL,  -- CLI flag: 'usa-nba'
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookmakers (
    id TEXT PRIMARY KEY,              -- 'pinnacle', 'bet365'
    name TEXT NOT NULL,               -- 'Pinnacle', 'Bet365'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Core data tables

CREATE TABLE matches (
    id TEXT PRIMARY KEY,              -- 'nba_20240115_lakers_celtics'
    league_id TEXT NOT NULL REFERENCES leagues(id),
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    -- Results (populated after match completes)
    home_score INTEGER,
    away_score INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    -- Metadata
    oddsharvester_url TEXT,           -- source URL for debugging
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE odds_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL REFERENCES matches(id),
    bookmaker_id TEXT NOT NULL REFERENCES bookmakers(id),
    market TEXT NOT NULL,             -- '1x2', 'over_under', 'spread', 'asian_handicap'
    outcome TEXT NOT NULL,            -- 'home', 'away', 'over_210.5', 'home_-4.5'
    line REAL,                        -- NULL for 1x2, value for spreads/totals
    odds REAL NOT NULL,               -- decimal odds
    odds_type TEXT DEFAULT 'current', -- 'opening', 'closing', 'current'
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_type TEXT NOT NULL,    -- 'backfill', 'upcoming', 'results'
    sport_id TEXT REFERENCES sports(id),
    league_id TEXT REFERENCES leagues(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'running',    -- 'running', 'completed', 'failed', 'partial'
    matches_collected INTEGER DEFAULT 0,
    odds_collected INTEGER DEFAULT 0,
    error_message TEXT,
    config_json TEXT                  -- store job config for debugging
);

-- Linking table for Polymarket correlation

CREATE TABLE market_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    polymarket_id TEXT NOT NULL,      -- from polymarket.db
    match_id TEXT NOT NULL REFERENCES matches(id),
    confidence REAL,                  -- 0-1 match confidence score
    link_type TEXT DEFAULT 'auto',    -- 'auto', 'manual'
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    UNIQUE(polymarket_id, match_id)
);

-- Performance indexes

CREATE INDEX idx_matches_league ON matches(league_id);
CREATE INDEX idx_matches_time ON matches(commence_time);
CREATE INDEX idx_matches_teams ON matches(home_team, away_team);
CREATE INDEX idx_odds_match ON odds_snapshots(match_id);
CREATE INDEX idx_odds_market ON odds_snapshots(market);
CREATE INDEX idx_odds_bookmaker ON odds_snapshots(bookmaker_id);
CREATE INDEX idx_odds_scraped ON odds_snapshots(scraped_at);
CREATE INDEX idx_links_poly ON market_links(polymarket_id);
CREATE INDEX idx_links_match ON market_links(match_id);
```

### Initial Data Seeds

```sql
-- Sports
INSERT INTO sports (id, name, oddsharvester_key) VALUES
('basketball', 'Basketball', 'basketball');

-- Leagues (start with NBA, expandable)
INSERT INTO leagues (id, sport_id, name, country, oddsharvester_key) VALUES
('nba', 'basketball', 'NBA', 'USA', 'usa-nba'),
('ncaab', 'basketball', 'NCAA Basketball', 'USA', 'usa-ncaa-basketball');
```

---

## 3. Component Specifications

### 3.1 OddsHarvesterClient

**Purpose:** Wrapper around the `oddsharvester` CLI tool.

**File:** `src/cuic_quant/data/oddsharvester_client.py`

```python
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import subprocess
import json
from typing import Iterator

@dataclass
class ScrapedMatch:
    """Raw match data from OddsHarvester."""
    home_team: str
    away_team: str
    commence_time: str
    league: str
    url: str

@dataclass
class ScrapedOdds:
    """Raw odds data from OddsHarvester."""
    match_url: str
    bookmaker: str
    market: str
    outcome: str
    line: float | None
    odds: float
    odds_type: str  # 'opening' or 'closing'

class OddsHarvesterClient:
    """Wrapper for oddsharvester CLI."""

    def __init__(
        self,
        headless: bool = True,
        proxy: str | None = None,
        output_dir: Path | None = None,
    ):
        self.headless = headless
        self.proxy = proxy
        self.output_dir = output_dir or Path("/tmp/oddsharvester")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def scrape_upcoming(
        self,
        sport: str,
        league: str,
        markets: list[str],
        days_ahead: int = 7,
    ) -> Path:
        """Scrape upcoming matches. Returns path to JSON output."""
        ...

    def scrape_historic(
        self,
        sport: str,
        league: str,
        season: str,
        markets: list[str],
    ) -> Path:
        """Scrape historical season data. Returns path to JSON output."""
        ...

    def parse_output(self, output_path: Path) -> Iterator[tuple[ScrapedMatch, list[ScrapedOdds]]]:
        """Parse JSON output into dataclasses."""
        ...
```

### 3.2 OddsHarvesterCollector

**Purpose:** Orchestrates scraping and database persistence.

**File:** `src/cuic_quant/collector/oddsharvester_collector.py`

```python
class OddsHarvesterCollector:
    """Collects sports odds data using OddsHarvester."""

    def __init__(
        self,
        db_path: str | Path = "data/sports_odds.db",
        parallel: int = 8,
        proxies: list[str] | None = None,
        headless: bool = True,
    ):
        self.db_path = Path(db_path)
        self.parallel = parallel
        self.proxies = proxies or []
        self.headless = headless
        self._init_db()

    def backfill(
        self,
        sport: str,
        league: str,
        seasons: list[str],
        markets: list[str] | None = None,
        resume: bool = True,
        on_progress: Callable[[Progress], None] | None = None,
    ) -> CollectionResult:
        """
        Backfill historical data for multiple seasons.

        Args:
            sport: Sport key (e.g., 'basketball')
            league: League key (e.g., 'nba')
            seasons: List of seasons ['2021-2022', '2022-2023', ...]
            markets: Markets to collect (default: all available)
            resume: Skip already-collected data
            on_progress: Callback for progress updates

        Returns:
            CollectionResult with statistics
        """
        ...

    def collect_upcoming(
        self,
        sport: str,
        league: str,
        days_ahead: int = 7,
        markets: list[str] | None = None,
    ) -> CollectionResult:
        """Collect upcoming match odds."""
        ...

    def collect_results(
        self,
        sport: str,
        league: str,
        start_date: date | None = None,
    ) -> CollectionResult:
        """Update match results for completed games."""
        ...

    def get_gaps(
        self,
        sport: str,
        league: str,
    ) -> dict[str, list[str]]:
        """Find missing data in collection."""
        ...

    def status(self) -> dict:
        """Get collection statistics."""
        ...
```

### 3.3 SportsOddsRepository

**Purpose:** Query interface for sports odds database.

**File:** `src/cuic_quant/database/repositories/sports_odds_repo.py`

```python
class SportsOddsRepository:
    """Repository for querying sports odds data."""

    def __init__(self, db_path: str | Path = "data/sports_odds.db"):
        self.db_path = Path(db_path)
        self.engine = create_engine(f"sqlite:///{db_path}")

    # === DataFrame Methods (for notebooks) ===

    def get_odds_df(
        self,
        league: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        markets: list[str] | None = None,
        bookmakers: list[str] | None = None,
    ) -> pd.DataFrame:
        """Get odds data as DataFrame."""
        ...

    def get_matches_df(
        self,
        league: str | None = None,
        season: str | None = None,
        completed_only: bool = False,
    ) -> pd.DataFrame:
        """Get matches as DataFrame."""
        ...

    def get_best_odds_df(
        self,
        match_id: str | None = None,
        league: str | None = None,
        market: str = "1x2",
    ) -> pd.DataFrame:
        """Get best odds across bookmakers."""
        ...

    def get_odds_history_df(
        self,
        match_id: str,
        market: str | None = None,
    ) -> pd.DataFrame:
        """Get odds movement over time for a match."""
        ...

    # === Listing Methods ===

    def list_sports(self) -> list[str]:
        """List available sports."""
        ...

    def list_leagues(self, sport: str | None = None) -> list[str]:
        """List available leagues."""
        ...

    def list_bookmakers(self) -> list[str]:
        """List available bookmakers."""
        ...

    def list_markets(self) -> list[str]:
        """List available market types."""
        ...

    # === Statistics ===

    def get_collection_stats(self) -> dict:
        """Get comprehensive collection statistics."""
        ...
```

---

## 4. Unified Query Interface

### UnifiedOddsClient

**Purpose:** Cross-platform queries joining Polymarket and sports odds data.

**File:** `src/cuic_quant/analysis/unified_client.py`

```python
class UnifiedOddsClient:
    """Unified interface for Polymarket + sports betting odds."""

    def __init__(
        self,
        polymarket_db: str | Path = "data/polymarket.db",
        sports_odds_db: str | Path = "data/sports_odds.db",
    ):
        self.poly_repo = MarketRepository(polymarket_db)
        self.sports_repo = SportsOddsRepository(sports_odds_db)
        self.sports_engine = create_engine(f"sqlite:///{sports_odds_db}")

    # === Market Linking ===

    def auto_link_markets(
        self,
        confidence_threshold: float = 0.85,
        sport: str | None = None,
        league: str | None = None,
    ) -> int:
        """
        Automatically link Polymarket markets to sports matches.
        Uses fuzzy matching on team names + date proximity.
        Returns number of links created.
        """
        ...

    def suggest_links(
        self,
        unlinked_only: bool = True,
        limit: int = 50,
    ) -> pd.DataFrame:
        """Get suggested links for manual verification."""
        ...

    def verify_link(
        self,
        polymarket_id: str,
        match_id: str,
        correct: bool = True,
    ) -> None:
        """Manually verify or reject a suggested link."""
        ...

    def get_linked_markets(
        self,
        sport: str | None = None,
        league: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        verified_only: bool = False,
    ) -> pd.DataFrame:
        """
        Get linked markets with data from both platforms.

        Returns DataFrame with columns:
        - match_id, polymarket_id
        - home_team, away_team, commence_time
        - poly_yes_price, poly_no_price
        - best_home_odds, best_away_odds, best_bookmaker
        - implied_diff (Polymarket vs book implied probability)
        """
        ...

    # === Cross-Platform Analysis ===

    def find_cross_arbitrage(
        self,
        sport: str | None = None,
        league: str | None = None,
        min_edge_pct: float = 1.0,
    ) -> pd.DataFrame:
        """
        Find arbitrage opportunities between Polymarket and bookmakers.

        Returns DataFrame with columns:
        - match_id, polymarket_id
        - home_team, away_team
        - poly_price, book_odds, bookmaker
        - edge_pct
        - optimal_stakes (dict)
        """
        ...

    def compare_closing_prices(
        self,
        league: str,
        season: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Compare Polymarket closing prices vs bookmaker closing odds.

        Returns DataFrame with:
        - match details
        - poly_closing, book_closing
        - actual_outcome
        - poly_correct, book_correct (boolean)
        - brier_poly, brier_book (Brier scores)
        """
        ...

    def get_calibration_data(
        self,
        league: str,
        source: str = "both",  # 'polymarket', 'bookmakers', 'both'
        bins: int = 10,
    ) -> pd.DataFrame:
        """
        Get calibration data for probability accuracy analysis.

        Returns DataFrame with:
        - probability_bin (0.0-0.1, 0.1-0.2, ...)
        - predicted_prob (bin midpoint)
        - actual_win_rate
        - count
        - source
        """
        ...
```

### Example Notebook Usage

```python
# research/notebooks/cross_platform_analysis.ipynb

from cuic_quant.analysis import UnifiedOddsClient
import pandas as pd
import matplotlib.pyplot as plt

# Initialize
client = UnifiedOddsClient()

# Auto-link Polymarket markets to NBA games
links_created = client.auto_link_markets(
    sport="basketball",
    league="nba",
    confidence_threshold=0.85
)
print(f"Created {links_created} market links")

# Get linked data
df = client.get_linked_markets(
    league="nba",
    start_date="2024-01-01",
    end_date="2024-03-01"
)

# Analyze price differences
df['poly_implied'] = df['poly_yes_price']
df['book_implied'] = 1 / df['best_home_odds']
df['diff'] = df['poly_implied'] - df['book_implied']

# Visualize
fig, ax = plt.subplots(figsize=(10, 6))
df['diff'].hist(bins=30, ax=ax)
ax.axvline(0, color='red', linestyle='--')
ax.set_xlabel('Implied Probability Difference (Poly - Book)')
ax.set_ylabel('Frequency')
ax.set_title('Polymarket vs Bookmaker Pricing')
plt.show()

# Find arbitrage opportunities
arbs = client.find_cross_arbitrage(league="nba", min_edge_pct=2.0)
print(f"Found {len(arbs)} arbitrage opportunities")
arbs.head(10)
```

---

## 5. Implementation Tasks

### Phase 1: Core Infrastructure (Week 1-2)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **1.1** | Install OddsHarvester, verify CLI works | 1 hour |
| **1.2** | Create `OddsHarvesterClient` (CLI wrapper) | 4 hours |
| **1.3** | Create sports odds SQLAlchemy models | 2 hours |
| **1.4** | Create database connection utilities | 1 hour |
| **1.5** | Create `SportsOddsRepository` | 4 hours |
| **1.6** | Write unit tests for client + repo | 3 hours |

### Phase 2: Collection System (Week 2-3)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **2.1** | Create `OddsHarvesterCollector` base class | 4 hours |
| **2.2** | Implement `backfill()` with parallel workers | 6 hours |
| **2.3** | Implement `collect_upcoming()` | 2 hours |
| **2.4** | Implement `collect_results()` | 2 hours |
| **2.5** | Add proxy rotation support | 2 hours |
| **2.6** | Extend `CollectionScheduler` for sports odds | 2 hours |
| **2.7** | Add CLI commands (`cuic-quant sports-collect`) | 2 hours |
| **2.8** | Write integration tests | 3 hours |

### Phase 3: Historical Backfill (Week 3-4)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **3.1** | Configure proxy list | 1 hour |
| **3.2** | Run NBA 2021-2022 backfill | ~2 hours runtime |
| **3.3** | Run NBA 2022-2023 backfill | ~2 hours runtime |
| **3.4** | Run NBA 2023-2024 backfill | ~2 hours runtime |
| **3.5** | Run NBA 2024-2025 backfill | ~1 hour runtime |
| **3.6** | Verify data quality, fix gaps | 2 hours |

### Phase 4: Unified Interface (Week 4-5)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **4.1** | Create `UnifiedOddsClient` class | 2 hours |
| **4.2** | Implement fuzzy market linking | 4 hours |
| **4.3** | Implement `get_linked_markets()` | 2 hours |
| **4.4** | Implement `find_cross_arbitrage()` | 3 hours |
| **4.5** | Implement `compare_closing_prices()` | 2 hours |
| **4.6** | Create example notebooks | 3 hours |
| **4.7** | Write documentation | 2 hours |

### Phase 5: Production Hardening (Week 5-6)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **5.1** | Add comprehensive error handling | 2 hours |
| **5.2** | Add retry logic with exponential backoff | 2 hours |
| **5.3** | Add collection monitoring/alerting | 2 hours |
| **5.4** | Performance optimization (batch inserts) | 2 hours |
| **5.5** | Add data validation checks | 2 hours |
| **5.6** | Documentation and team onboarding | 2 hours |

---

## 6. Technical Decisions

### Decisions Made During Design

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Data source** | OddsHarvester (replace Odds API) | Free, unlimited scraping vs 500 req/month |
| **Integration approach** | CLI wrapper | Clean separation, no fork maintenance |
| **Interface design** | Fresh design (not drop-in) | Leverage OddsHarvester's strengths |
| **Primary use case** | Both arbitrage + backtesting | Full research capability |
| **Initial sport** | Basketball (NBA) | Start focused, expand later |
| **Markets** | All available | Maximum data coverage |
| **Database** | SQLite (PostgreSQL-ready) | Easy now, migrate later |
| **Parallelism** | 8 workers with proxy rotation | Balance speed vs blocking risk |
| **Historical range** | 2021-present | Match Polymarket's sports history |
| **Data scope** | Odds only (stats elsewhere) | OddsHarvester's strength |
| **Architecture** | Mirror Polymarket infrastructure | Consistency, familiar patterns |

### Data Volume Estimates

| Metric | Estimate |
|--------|----------|
| NBA seasons | 4 (2021-2025) |
| Total matches | ~5,200 |
| Bookmakers per match | ~30-40 |
| Odds rows | ~7-10 million |
| Database size | ~1-2 GB |
| Backfill time (8 parallel) | ~1-2 hours |

### Dependencies

**New Python packages:**
- None required (OddsHarvester is CLI-based)

**System dependencies:**
- `oddsharvester` CLI installed via `uv sync` or `pip install oddsharvester`
- Playwright browsers (installed by OddsHarvester)

**Optional:**
- Proxy service for parallel scraping

### Future Extensibility

**Adding a new sport:**
1. Insert row into `sports` table
2. Insert rows into `leagues` table
3. Run `collector.backfill(sport="new_sport", league="new_league", ...)`

No code changes required for supported OddsHarvester sports.

**PostgreSQL Migration:**
1. Create PostgreSQL database with two schemas: `polymarket`, `sports_odds`
2. Use `pgloader` or pandas to migrate SQLite data
3. Update connection strings in config
4. Both repositories work unchanged (SQLAlchemy abstraction)

---

## Appendix A: OddsHarvester CLI Reference

```bash
# Upcoming matches
oddsharvester upcoming \
  -s basketball \
  -l usa-nba \
  -m 1x2,over_under,spread,asian_handicap \
  -d 20250301 \
  --headless \
  --output json \
  --proxy http://proxy:8080

# Historical data
oddsharvester historic \
  -s basketball \
  -l usa-nba \
  --season 2024-2025 \
  -m 1x2,over_under,spread,asian_handicap \
  --headless \
  --output json \
  --proxy http://proxy:8080
```

---

## Appendix B: Example Queries

```python
# Get all NBA odds for January 2024
df = repo.get_odds_df(
    league="nba",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    markets=["1x2", "over_under"]
)

# Find best odds for a specific match
best = repo.get_best_odds_df(match_id="nba_20240115_lakers_celtics")

# Get odds movement (for line shopping analysis)
history = repo.get_odds_history_df(
    match_id="nba_20240115_lakers_celtics",
    market="spread"
)

# Cross-platform: Polymarket vs books
linked = client.get_linked_markets(league="nba", season="2023-2024")
arbs = client.find_cross_arbitrage(league="nba", min_edge_pct=2.0)
```

---

## Appendix C: Schema Migration (SQLite → PostgreSQL)

```sql
-- PostgreSQL setup
CREATE SCHEMA polymarket;
CREATE SCHEMA sports_odds;

-- Migrate using pgloader
-- pgloader sqlite:///data/polymarket.db postgresql:///cuic_quant?schema=polymarket
-- pgloader sqlite:///data/sports_odds.db postgresql:///cuic_quant?schema=sports_odds

-- Or via Python
import pandas as pd
from sqlalchemy import create_engine

sqlite_engine = create_engine("sqlite:///data/sports_odds.db")
pg_engine = create_engine("postgresql://user:pass@host/cuic_quant")

for table in ["sports", "leagues", "bookmakers", "matches", "odds_snapshots"]:
    df = pd.read_sql_table(table, sqlite_engine)
    df.to_sql(table, pg_engine, schema="sports_odds", if_exists="replace", index=False)
```
