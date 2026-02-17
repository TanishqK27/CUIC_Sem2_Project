# Plan: Polymarket Prediction Market EDA

## Context

Create a comprehensive EDA report documenting Polymarket prediction market dynamics for NBA games. The report is for the internal CUIC team, must be mathematically rigorous but accessible to undergraduates, with step-by-step explanations of statistical techniques and their interpretations.

**Key requirements:**
- **All available data**: 180,848 price snapshots, 67.9M websocket events, 129 games
- Covers both Polymarket internals AND PM vs Sportsbook (SB) comparison
- **Cross-game and temporal comparisons** integrated throughout
- Market microstructure analysis (orderbook, spreads, depth)
- Lead/lag relationships between PM and SB
- Mirrors the notebook structure with publication figures
- Explains each statistical method used (Granger causality, autocorrelation, etc.)
- Mixed tone: pure statistics with trading/arbitrage context
- ~25-30 pages, no appendices/citations/code
- Brief trading strategy recommendations at end

---

## EDA Scope (Strict Definition)

### This Report INCLUDES (Pure EDA):
- **Descriptive statistics**: Price distributions, spreads, depths, volumes
- **Data quality**: Missing data patterns, outliers, data integrity
- **Market structure**: Bid-ask spreads, liquidity profiles, depth distribution
- **Price dynamics**: Volatility, autocorrelation, mean reversion
- **PM-SB comparison**: Gap distributions, correlations, lead/lag (descriptive)
- **Temporal patterns**: Time-of-day effects, game phase patterns
- **Microstructure**: Orderbook imbalance, trade flow, depth shocks
- **Implications**: What the data suggests for trading strategies

### This Report EXCLUDES (NOT EDA):
- ❌ Predictive models (no regression, no ML)
- ❌ Strategy backtesting or P&L simulation
- ❌ Model performance metrics
- ❌ Live trading recommendations with specific sizing
- ❌ Causal claims about market efficiency

### Clarifications:
- **Granger causality**: Descriptive of lead/lag, NOT causal proof
- **"Predictive"**: Correlation-based, NOT model-derived
- **"Half-life"**: Descriptive of persistence, NOT trading signal

---

## Scientific Skills to Use

### Skills to Apply During Implementation
| Skill | Purpose | When to Invoke |
|-------|---------|----------------|
| `scientific-skills:statsmodels` | Granger causality, autocorrelation, time series | Statistical computations |
| `scientific-skills:matplotlib` | Low-level figure customization, publication styling | Figure generation |
| `scientific-skills:seaborn` | Statistical visualizations, heatmaps, distributions | Figure generation |
| `scientific-skills:statistical-analysis` | Test selection, assumption checking | Notebook analysis cells |

### Skills to Apply During Report Writing
| Skill | Purpose | When to Invoke |
|-------|---------|----------------|
| `scientific-skills:scientific-writing` | LaTeX structure, flowing prose, notation standards | Report writing |
| `scientific-skills:scientific-visualization` | Publication-quality figures, colorblind-safe palettes | Figure creation |
| `scientific-skills:scientific-critical-thinking` | Ensure statistical rigor, avoid causal overclaims | Review |

---

## Data Scope

### Database Tables

| Table | Rows | Description |
|-------|------|-------------|
| `price_snapshots` | 180,848 | PM and SB prices every 5 min |
| `ws_book_events` | 67,953,360 | Real-time orderbook, trades, price changes |
| `latency_events` | 148,152 | System latency measurements |

### ws_book_events Breakdown

| Event Type | Count | Description |
|------------|-------|-------------|
| `book` | 1,343,541 | Full orderbook snapshots |
| `last_trade_price` | 666,309 | Trade executions |
| `price_change` | 65,943,510 | Mid-price updates |

### Coverage

| Metric | Value |
|--------|-------|
| Games | 129 |
| Outcomes tracked | 30 unique |
| Date range | Jan 31 - Feb 12, 2026 |
| Duration | ~2 weeks |

---

## Proposed LaTeX Report Structure

### Executive Summary (½ page)
*A standalone paragraph summarizing the entire report for readers who won't read further*

- Scope: 129 NBA games, 180K price snapshots, 68M orderbook events
- Key finding: SB leads PM in 63% of games (Granger causality at lag 1)
- Key finding: PM-SB gap has 128-minute half-life (slow mean reversion)
- Key finding: Spread predicts volatility (r = 0.23)
- Implication: PM follows SB; wide spreads signal upcoming volatility

### 1. Introduction (1-2 pages)
- **Purpose**: What this EDA investigates and why
- **Scope**: 129 NBA games on Polymarket, Jan-Feb 2026
- **Prediction Markets vs Sportsbooks**: Brief explanation
- **Key Questions**:
  - How does PM price discovery compare to SB?
  - What does the orderbook tell us about market quality?
  - Are there exploitable patterns in PM-SB gaps?
  - When is PM most/least efficient?

*Note: Brief explanation of prediction markets, orderbooks, bid-ask spreads*

### 2. Data Overview (4-5 pages)

#### 2.1 Dataset Description
- Source: Railway PostgreSQL (Dietrich's collection)
- **Three tables**: price_snapshots, ws_book_events, latency_events
- Collection method: 5-min polling + websocket streaming
- Date range: Jan 31 - Feb 12, 2026
- **Game-by-game breakdown table**

#### 2.2 Data Quality Assessment
- **Missing data analysis**: By table and field
- **Timestamp gaps**: Are there collection outages?
- **Data integrity**: Cross-table consistency checks
- **Methodology box**: What is websocket data? Why use it?

#### 2.3 Market Coverage
- Games per day distribution
- Outcome types (home win, away win)
- **Figure**: Data collection timeline

### 3. Statistical Methodology (2-3 pages)
*Brief explanations of techniques used throughout*

#### 3.1 Autocorrelation Analysis
- What ACF measures and how to interpret
- Ornstein-Uhlenbeck half-life estimation

#### 3.2 Granger Causality
- What it tests (predictive relationship, not causation)
- F-test interpretation
- Why we use differenced series

#### 3.3 Correlation Measures
- Pearson vs Spearman
- Rolling correlation for regime detection

#### 3.4 Effect Size for Proportions
- Cohen's h for comparing rates

### 4. Analysis (14-16 pages)

#### 4.1 Price Distribution Analysis
- PM probability distributions across games
- **Figure**: fig1_price_distributions.png - Histogram of PM prices
- Concentration near 0.5 vs extremes (0.1, 0.9)
- **Cross-game**: Do different game types have different distributions?
- **Trading implication**: Where is liquidity concentrated?

#### 4.2 PM-SB Gap Analysis
- Distribution of (SB - PM) gaps
- **Figure**: fig2_gap_distribution.png - Gap histogram with percentiles
- Mean gap: ~0.3pp, but high variance
- **By game state**: Gaps widen in decided games (SB > 90%)
- **Key finding**: Large gaps (>10pp) only appear in lopsided games

#### 4.3 Gap Persistence (Autocorrelation)
- ACF of gap series across lags
- **Figure**: fig3_gap_autocorrelation.png - ACF plot
- Half-life estimation: ~128 minutes
- **Methodology box**: What does half-life mean for trading?
- **Implication**: Gaps are persistent; convergence is slow

#### 4.4 Lead/Lag: Who Moves First? (Granger Causality)
- Granger causality tests: PM → SB and SB → PM
- **Figure**: fig4_granger_causality.png - % significant by lag
- **Key finding**: SB leads PM (63% vs 46% at lag 1)
- **Cross-game**: Is leadership consistent across games?
- **Trading implication**: Watch SB for PM price moves

#### 4.5 Conditional Correlation by Game State
- PM-SB correlation bucketed by SB probability
- **Figure**: fig5_correlation_by_state.png - Correlation by game state
- Competitive games (50-60%): r = 0.86
- Decided games (>90%): r = 0.90 but higher gap variance
- **Decorrelation episodes**: When do markets diverge?

#### 4.6 Orderbook Structure
- Bid-ask spread distribution
- **Figure**: fig6_spread_distribution.png - Spread histogram
- Depth distribution (bid vs ask)
- **Figure**: fig7_depth_analysis.png - Depth by price level
- Typical spread: 1-2 cents
- **Implication**: Transaction costs for entering/exiting

#### 4.7 Orderbook Imbalance Analysis
- Imbalance = bid_depth / (bid + ask)
- **Figure**: fig8_imbalance_signal.png - Imbalance quintiles vs returns
- Correlation with forward price: r = 0.02 (weak)
- **Quintile breakdown**: Q5 (buy pressure) vs Q1 (sell pressure)
- **Trading implication**: Weak signal, not actionable alone

#### 4.8 Spread as Volatility Predictor
- Spread → forward realized volatility
- **Figure**: fig9_spread_volatility.png - Spread terciles vs vol
- Correlation: r = 0.23 (moderate, significant)
- **Key finding**: Wide spreads predict 1.8x more price movement
- **Trading implication**: Spread as regime filter

#### 4.9 Trade Flow Analysis
- Buy vs sell trade breakdown
- **Figure**: fig10_trade_flow.png - Trade side distribution
- Imbalance: 86% buys, 14% sells (data artifact?)
- **Data quality note**: Trade side extraction issues
- **Implication for future**: Need cleaner trade data

#### 4.10 Depth Shock Analysis
- Events where depth drops >30%
- **Figure**: fig11_depth_shocks.png - Shock frequency by game
- 8,448 depth shocks detected across 92 games
- Average depth drop: -57.5%
- **Gap impact**: Unable to match to price snapshots (data join issue)

#### 4.11 Temporal Patterns
- Time-of-day effects on spread, depth, volatility
- **Figure**: fig12_time_patterns.png - Metrics by hour
- Game phase effects (pregame, 1st half, 2nd half, OT)
- **Cross-game**: Are patterns consistent?
- **Trading implication**: When is PM most liquid?

#### 4.12 Latency Analysis
- System latency distribution
- **Figure**: fig13_latency_distribution.png - Latency histogram
- Impact of latency on data quality
- **Implication**: Latency floor for any trading strategy

#### 4.13 Market Case Studies
- **2-3 specific games analyzed in depth**:
  - A competitive game (close throughout)
  - A blowout (one-sided)
  - A comeback (large price swing)
- **Insight**: How market dynamics differ by game type

### 5. Summary of Key Findings (2-3 pages)

#### 5.1 Market Efficiency Patterns
| Finding | Evidence | Stability |
|---------|----------|-----------|
| SB leads PM | 63% Granger significance at lag 1 | Consistent across games |
| Gaps are persistent | Half-life ~128 min | Stable |
| Spread predicts vol | r = 0.23 | Consistent |
| Orderbook imbalance weak | r = 0.02 | Weak signal |

#### 5.2 Market Quality Metrics
| Metric | Typical Value | Trading Implication |
|--------|---------------|---------------------|
| Bid-ask spread | 1-2 cents | Entry cost |
| Depth at best | Variable | Size limitations |
| Gap magnitude | ~3pp typical, >10pp in decided games | Arbitrage ceiling |

#### 5.3 Trading Implications Summary
- **Information flow**: SB → PM (watch SB for signals)
- **Convergence trades**: Slow (128 min half-life), need patience
- **Spread as filter**: Wide spread = volatility coming
- **Game state matters**: Competitive games have tighter PM-SB correlation

### 6. Limitations of This Analysis (½-1 page)

#### 6.1 Data Limitations
- **Short time window**: Only 2 weeks of data (Jan 31 - Feb 12)
- **NBA only**: May not generalize to other event types
- **Collection gaps**: 5-min polling misses fast price moves
- **Trade side data**: Extraction issues limit flow analysis

#### 6.2 Methodological Limitations
- **Granger ≠ causation**: Lead/lag is descriptive only
- **Aggregation**: Game-level patterns may not apply to individual moments
- **No external data**: Missing injury news, lineup changes

#### 6.3 Scope Limitations
- **No backtesting**: EDA only, no strategy validation
- **No cross-market**: Only NBA Polymarket
- **No cost analysis**: Did not model transaction costs fully

### 7. Recommendations for Trading Strategy Development (1 page)

#### 7.1 Data Collection Improvements
1. Higher frequency polling (sub-minute)
2. Clean trade side extraction
3. Add SB line movement timestamps
4. Integrate injury/lineup news feeds

#### 7.2 Strategy Considerations
- **Signal**: SB moves → PM follows (5-10 min window)
- **Filter**: Only trade when PM spread is wide (volatility expected)
- **Avoid**: Decided games (>90% SB prob) - gaps are real, not mispricings
- **Position sizing**: Account for slow convergence (128 min half-life)

#### 7.3 Next Steps
- Build prototype following SB → PM signal
- Backtest on historical data with realistic costs
- Paper trade before live capital

---

## Files to Create

**Notebook**: `research/notebooks/polymarket/01_polymarket_eda.ipynb`

### Figures to Create

| Figure | File | Section | Description |
|--------|------|---------|-------------|
| Price distributions | fig1_price_distributions.png | 4.1 | PM probability histogram |
| Gap distribution | fig2_gap_distribution.png | 4.2 | (SB - PM) gap histogram |
| Gap autocorrelation | fig3_gap_autocorrelation.png | 4.3 | ACF plot with half-life |
| Granger causality | fig4_granger_causality.png | 4.4 | % significant by lag |
| Correlation by state | fig5_correlation_by_state.png | 4.5 | PM-SB corr by game state |
| Spread distribution | fig6_spread_distribution.png | 4.6 | Bid-ask spread histogram |
| Depth analysis | fig7_depth_analysis.png | 4.6 | Depth by price level |
| Imbalance signal | fig8_imbalance_signal.png | 4.7 | Quintile returns |
| Spread vs volatility | fig9_spread_volatility.png | 4.8 | Tercile analysis |
| Trade flow | fig10_trade_flow.png | 4.9 | Buy vs sell breakdown |
| Depth shocks | fig11_depth_shocks.png | 4.10 | Shock frequency |
| Time patterns | fig12_time_patterns.png | 4.11 | Metrics by hour |
| Latency | fig13_latency_distribution.png | 4.12 | Latency histogram |
| Case studies | fig14_case_studies.png | 4.13 | 2-3 game deep dives |

---

## Implementation

### Skill Invocation Sequence

```
PHASE 1: Notebook Creation
├── /scientific-skills:statsmodels      → For Granger, ACF, time series
├── /scientific-skills:matplotlib       → For figure styling
├── /scientific-skills:seaborn          → For statistical plots
└── /scientific-skills:statistical-analysis → Test selection

PHASE 2: Report Writing
├── /scientific-skills:scientific-writing → For LaTeX structure
├── /scientific-skills:scientific-visualization → For figure quality
└── /scientific-skills:latex-posters     → If LaTeX issues

PHASE 3: Review
└── /scientific-skills:scientific-critical-thinking → Final rigor check
```

---

### Step 0: Create Notebook

**Location**: `research/notebooks/polymarket/01_polymarket_eda.ipynb`

**Database Connection**:
```python
import psycopg2
import pandas as pd

DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def query(sql):
    conn = psycopg2.connect(DB_URL, connect_timeout=30)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df
```

### Step 1: Data Loading Cells

```python
# Load price snapshots
snaps = query("""
    SELECT game, timestamp, pm_home_prob, sb_home_prob,
           (sb_home_prob - pm_home_prob) * 100 as gap
    FROM price_snapshots
    WHERE pm_home_prob IS NOT NULL AND sb_home_prob IS NOT NULL
    ORDER BY game, timestamp
""")

# Load book events
books = query("""
    SELECT timestamp, game, outcome, mid_price,
           bid_depth_total, ask_depth_total, best_bid, best_ask
    FROM ws_book_events
    WHERE event_type = 'book'
      AND bid_depth_total IS NOT NULL
    ORDER BY game, outcome, timestamp
""")

# Load trades
trades = query("""
    SELECT timestamp, game, outcome, best_bid as trade_price, buy_levels
    FROM ws_book_events
    WHERE event_type = 'last_trade_price'
    ORDER BY game, outcome, timestamp
""")
```

### Step 2: Analysis Cells (14 sections)

Each section follows pattern:
1. Query/filter relevant data
2. Compute statistics
3. Generate figure
4. Print key findings table
5. Save figure to `figures/`

### Step 3: Generate All Figures

After notebook complete, run all cells to generate:
- fig1 through fig14
- Save to `research/notebooks/polymarket/figures/`

### Step 4: Create LaTeX Report

Use `scientific_report.sty` for professional formatting.

---

## Verification Checklist

### EDA Compliance (CRITICAL)
- [ ] NO predictive models trained
- [ ] NO backtesting or P&L simulation
- [ ] Granger causality stated as descriptive, not causal
- [ ] All "implications" are observational
- [ ] Language uses "association", not "prediction"

### Notebook Completion
- [ ] All 14 figure cells execute without errors
- [ ] Figures saved to figures/ directory
- [ ] Key statistics printed for each section
- [ ] Data quality issues documented

### Content
- [ ] All 14 figures created and included
- [ ] Statistics cross-checked against Dietrich's correlation notebook
- [ ] 2-3 game case studies with real data
- [ ] Temporal patterns analyzed

### Writing Quality
- [ ] NO bullet points in final document
- [ ] Methodology boxes explain each technique
- [ ] Plain English interpretations
- [ ] Trading context explained

### Formatting
- [ ] Consistent statistical notation
- [ ] All figures have complete captions
- [ ] Tables use professional formatting
- [ ] Page count: 25-30 pages

---

## Iterative Improvement Loop (4 Passes)

### Pass 1: Foundation (Draft)
- Build notebook with all 14 analysis sections
- Generate all figures
- Create LaTeX skeleton
- Convert outline to prose

### Pass 2: Statistical Rigor
- Verify all statistics against database
- Check for overclaims
- Add methodology boxes
- Cross-game comparisons in every section

### Pass 3: Writing Quality
- Full prose check, no bullets
- Plain English interpretations
- Logical flow
- Trading implications clearly stated

### Pass 4: Polish & Optimization
- Figure captions complete
- Notation consistency
- Colorblind-safe figures
- Final proofread

---

## Page Estimates

| Section | Pages |
|---------|-------|
| Executive Summary | 0.5 |
| Introduction | 1.5 |
| Data Overview | 4 |
| Statistical Methodology | 2.5 |
| Analysis (13 subsections) | 15 |
| Summary of Key Findings | 2.5 |
| Limitations | 1 |
| Recommendations | 1 |
| **Total** | **~28 pages** |

---

## Key Differences from NBA EDA

| Aspect | NBA EDA | Polymarket EDA |
|--------|---------|----------------|
| Data type | Player performance | Market prices |
| Granularity | Per-game | Sub-second to 5-min |
| Time span | 5 seasons | 2 weeks |
| Key metric | CV (consistency) | Gap half-life |
| Lead/lag | N/A | SB → PM (Granger) |
| Microstructure | N/A | Orderbook, depth, spreads |
| Target | Player props | Arbitrage/convergence |

---

## Database Schema Reference

### price_snapshots
```sql
game, timestamp, pm_home_prob, sb_home_prob, (derived: gap)
```

### ws_book_events
```sql
timestamp, game, outcome, event_type, mid_price,
bid_depth_total, ask_depth_total, best_bid, best_ask, buy_levels
```

### latency_events
```sql
timestamp, latency_ms, event_type
```
