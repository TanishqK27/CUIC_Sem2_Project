# CUIC Quant Fund - Project Tasks

Central task tracking for the entire project. Individual tasks are managed in `team/<name>/TASKS.md`.

---

## Project Milestones

### Phase 1: Infrastructure (February 2025)
- [x] Repository setup
- [x] Documentation
- [x] Development environment
- [ ] API client implementations
- [ ] Basic backtesting framework

---

## Week 1 Sprint (Feb 6-12, 2026)

**Goal:** Build complete data pipeline + backtesting framework for NBA sports betting research.
**Deadline:** Thursday Feb 12 (Presentation Day)
**Coordinator:** Miran (daily progress reports in `team/progress_reports/week1.md`)

### Data Collection
- [ ] NBA stats collected (4 seasons: 2021-25) - **Max**
- [ ] Sportsbook odds scraped (OddsHarvester) - **Alfie**
- [ ] Data validated with standardized `team_abbr` format - **Max + Alfie**

### Infrastructure
- [ ] Railway PostgreSQL tables created (5 tables) - **Dietrich**
- [ ] All CSVs loaded to database - **Dietrich**
- [ ] Tables joinable on `team_abbr` column verified - **Dietrich**

### Analysis Tools
- [ ] Backtester framework functional with dummy data - **James**
- [ ] Metrics module complete (Sharpe, drawdown, etc.) - **Ben**
- [ ] Test data generator ready - **Mya**

### Exploratory Analysis
- [ ] Polymarket EDA notebook with 5+ visualizations - **Dietrich**
- [ ] Sportsbook EDA notebook with 3+ findings - **Mya**

### Quality & Coordination
- [ ] Backtester + metrics tested against edge cases - **Isameel**
- [ ] Daily progress reports posted - **Miran**
- [ ] 3-5 research papers summarized - **Miran**

### Documentation
- [ ] Data inventory document complete - **Vansheeka**
- [ ] Strategy interface documented - **James**
- [ ] Meeting notes captured - **Isameel**

---

### Phase 2: Research (March 2025)
- [ ] Polymarket data exploration
- [ ] Kalshi data exploration
- [ ] Sports betting odds analysis
- [ ] Initial strategy hypotheses

### Phase 3: Strategy Development (April 2025)
- [ ] Mean reversion strategy
- [ ] Arbitrage detection
- [ ] Kelly criterion implementation
- [ ] Backtesting validation

### Phase 4: Paper Trading (May 2025)
- [ ] Paper trading infrastructure
- [ ] Performance monitoring
- [ ] Risk management

---

## Research Task Categories

1. [Data Sources & Collection](#category-1-data-sources--collection) (6 tasks)
2. [Strategy Research](#category-2-strategy-research) (8 tasks)
3. [Platform Deep Dives](#category-3-platform-deep-dives) (4 tasks)
4. [Academic Literature Reviews](#category-4-academic-literature-reviews) (4 tasks)
5. [Sport/Event Specific](#category-5-sportevent-specific) (4 tasks)

**Total Research Tasks: 26**

---

## Category 1: Data Sources & Collection

### [TASK-001] Sports Statistics API Comparison

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Compare major sports statistics APIs (Sportradar, ESPN API, StatsBomb, free alternatives) for coverage, data quality, pricing, and suitability for quantitative modeling. Document which APIs are best for different sports and use cases.

#### Hypothesis
Free APIs like ESPN provide sufficient data for basic models, but premium APIs (Sportradar, StatsBomb) offer granular play-by-play data that enables more sophisticated predictions.

#### Data Required
- API documentation from each provider
- Sample data from free tiers
- Pricing information
- Coverage by sport/league

#### Methodology
1. Catalog available APIs (paid and free)
2. Document coverage: sports, leagues, data types
3. Compare data freshness and update frequency
4. Evaluate ease of integration (authentication, rate limits)
5. Create recommendation matrix by use case

#### Expected Outcome
Comprehensive comparison document with clear recommendations for which APIs to use for different sports and modeling approaches.

#### Notes
Key providers to evaluate: Sportradar, ESPN API, StatsBomb, API-Football, The Odds API, Sportsdata.io, free options (Basketball-Reference API, nflverse).

---

### [TASK-002] Social Sentiment Data Sources

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research and document sources for social media sentiment data relevant to sports and political predictions. Evaluate Twitter/X, Reddit, Discord, and specialized services for extracting betting-relevant signals.

#### Hypothesis
Social sentiment (particularly from Reddit sportsbooks, Twitter betting accounts) contains predictive signal that can improve model accuracy when combined with odds data.

#### Data Required
- Twitter/X API access options
- Reddit API (PRAW) capabilities
- Sentiment analysis tools/services
- Sample sentiment data

#### Methodology
1. Document available APIs and their limitations
2. Identify relevant subreddits (r/sportsbook, r/sportsbetting)
3. Research Twitter betting communities
4. Evaluate sentiment analysis tools (VADER, FinBERT, custom)
5. Assess data volume and timeliness

#### Expected Outcome
Guide for collecting and processing social sentiment data, with recommendations for which platforms provide the most signal.

#### Notes
Consider both raw social data APIs and processed sentiment services (Santiment, LunarCrush for crypto, potential sports equivalents).

---

### [TASK-003] Weather Data Integration

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Low

#### Description
Research weather data APIs and their potential impact on outdoor sports predictions (NFL, MLB, soccer, tennis, golf). Document which weather variables matter most for each sport.

#### Hypothesis
Weather conditions (wind, precipitation, temperature) have measurable impact on scoring in outdoor sports, and integrating weather data can improve over/under predictions.

#### Data Required
- Weather API options (OpenWeatherMap, Weather.gov, Visual Crossing)
- Historical game weather data
- Stadium/venue location data
- Game outcomes with weather conditions

#### Methodology
1. Identify relevant weather variables by sport
2. Compare weather API coverage and accuracy
3. Research academic literature on weather impact
4. Evaluate forecast vs. actual accuracy
5. Document integration approach

#### Expected Outcome
Weather data integration guide with specific recommendations for each sport and identified high-impact weather scenarios.

#### Notes
Focus sports: NFL (wind/cold), MLB (wind/humidity), soccer (rain/heat), tennis outdoor events, golf tournaments.

---

### [TASK-004] Injury & Roster Data Providers

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Research sources for real-time injury reports, lineup confirmations, and roster changes across major sports. Evaluate speed, accuracy, and API availability.

#### Hypothesis
Fast access to injury and lineup information provides trading edge, as markets take 5-15 minutes to fully adjust to news.

#### Data Required
- Official league injury report sources
- Twitter beat reporter accounts
- Injury tracking services (RotoBaller, ESPN)
- Historical injury data

#### Methodology
1. Document official injury report schedules by league
2. Identify fastest news sources (Twitter, beat reporters)
3. Evaluate paid services (RotoWire, FantasyLabs)
4. Research news sentiment/NLP for injury extraction
5. Measure time-to-market-adjustment

#### Expected Outcome
Real-time injury data strategy with source ranking by speed and reliability, plus integration recommendations.

#### Notes
NFL injury reports have specific release windows; NBA has daily injury reports; soccer is more fragmented (team Twitter accounts).

---

### [TASK-005] Historical Odds Database Options

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Compare historical odds databases for coverage, quality, and cost. Evaluate options for backtesting betting strategies across different sports and time periods.

#### Hypothesis
Quality historical odds data is essential for backtesting; differences in data sources can significantly impact strategy evaluation results.

#### Data Required
- Historical odds providers (Odds-API historical, Football-Data.co.uk, etc.)
- Sample data from each source
- Pricing information
- Coverage details

#### Methodology
1. Catalog available historical odds sources
2. Compare coverage: sports, markets, time periods
3. Evaluate data quality (missing data, errors)
4. Assess pricing models
5. Document format and integration ease

#### Expected Outcome
Historical odds data sourcing guide with recommendations based on sport, time period, and budget.

#### Notes
Key sources: Football-Data.co.uk (free, soccer), Kaggle datasets, Odds Portal, SportingIndex, BetBrain historical.

---

### [TASK-026] OddsHarvester Integration (Replace Odds API)

**Assigned:** Alfie, Max
**Status:** Planned
**Priority:** High
**Plan Document:** `team/tan/plans_for_team_tasks/oddsharvester-integration-plan.md`

#### Description
Replace The Odds API with [OddsHarvester](https://github.com/jordantete/OddsHarvester), a free open-source scraper for oddsportal.com. Build a data warehouse architecture mirroring the Polymarket infrastructure to enable cross-platform analysis between prediction markets and traditional sportsbooks.

#### Hypothesis
Free unlimited scraping via OddsHarvester provides better historical coverage than The Odds API (500 req/month free tier), enabling comprehensive backtesting and cross-platform arbitrage detection with Polymarket.

#### Data Required
- Historical NBA odds (2021-2025, matching Polymarket's sports market history)
- All bookmakers (~30-50 per match)
- All markets (1x2, over/under, spreads, Asian handicap)
- Opening and closing odds

#### Architecture
```
Collection:  OddsHarvesterCollector (8 parallel workers, proxy rotation)
Storage:     SQLite (sports_odds.db) → PostgreSQL-ready schema
Query:       SportsOddsRepository (DataFrame methods for notebooks)
Analysis:    UnifiedOddsClient (cross-platform Polymarket + sports odds)
```

#### Implementation Phases

| Phase | Tasks | Effort |
|-------|-------|--------|
| **1. Core Infrastructure** | CLI wrapper, models, repository | ~15 hours |
| **2. Collection System** | Collector, scheduler, CLI commands | ~23 hours |
| **3. Historical Backfill** | NBA 2021-2025 data (~5,200 matches) | ~8 hours runtime |
| **4. Unified Interface** | Cross-platform queries, market linking | ~16 hours |
| **5. Production Hardening** | Error handling, monitoring, docs | ~12 hours |

#### Expected Outcome
- `sports_odds.db` with ~7-10 million odds rows (~1-2 GB)
- `SportsOddsRepository` for notebook-friendly queries
- `UnifiedOddsClient` for Polymarket ↔ sports odds correlation
- Cross-platform arbitrage detection capability

#### Dependencies
- OddsHarvester CLI (`pip install oddsharvester`)
- Playwright browsers (installed by OddsHarvester)
- Optional: Proxy service for parallel scraping

#### Notes
- Detailed implementation plan at: `team/tan/plans_for_team_tasks/oddsharvester-integration-plan.md`
- Mirrors existing Polymarket collector architecture for consistency
- Start with NBA, extensible to other sports (schema is sport-agnostic)

---

## Category 2: Strategy Research

### [TASK-006] ML Probability Estimation Methods

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Research and compare machine learning approaches for estimating win probabilities in sports: Random Forest, XGBoost, Neural Networks, and ensemble methods. Focus on which methods work best for different data types.

#### Hypothesis
Gradient boosting methods (XGBoost, LightGBM) outperform other approaches for tabular sports data, but neural networks may excel for sequential/time-series game data.

#### Data Required
- Historical game data with features
- Bookmaker closing lines (as benchmark)
- ML framework documentation
- Academic papers on sports prediction

#### Methodology
1. Survey academic literature on ML for sports
2. Document common feature engineering approaches
3. Compare model architectures by sport
4. Research calibration methods
5. Evaluate against bookmaker benchmark

#### Expected Outcome
ML methodology guide for sports prediction with code templates and benchmark results.

#### Notes
Key papers: "Beating the bookies" by Hubacek et al., FiveThirtyEight methodology docs.

---

### [TASK-007] Poisson Models for Soccer Scoring

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research Poisson and Dixon-Coles models for predicting soccer match outcomes. Document the methodology, assumptions, and implementation approaches including expected goals (xG) integration.

#### Hypothesis
Poisson-based models with expected goals (xG) data outperform basic models and can identify value in over/under and correct score markets.

#### Data Required
- Soccer match results
- Expected goals (xG) data
- Historical goal distributions
- Academic papers on Poisson models

#### Methodology
1. Document standard Poisson model for soccer
2. Research Dixon-Coles adjustments
3. Evaluate xG data sources and models
4. Compare to market implied probabilities
5. Identify value betting opportunities

#### Expected Outcome
Implementation guide for Poisson-based soccer models with code and validation results.

#### Notes
Key reference: Dixon & Coles (1997) "Modelling Association Football Scores and Inefficiencies in the Football Betting Market".

---

### [TASK-008] ELO Rating Systems

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research ELO and ELO-variant rating systems for team and player ranking across different sports. Document how to calibrate ELO parameters and convert ratings to win probabilities.

#### Hypothesis
Well-calibrated ELO systems provide competitive probability estimates and can identify market inefficiencies, especially for teams with recent form changes.

#### Data Required
- Historical game results
- Existing ELO implementations (538, ClubELO)
- Win probability formulas
- Parameter tuning approaches

#### Methodology
1. Document basic ELO formula and history
2. Research sport-specific variants (Glicko, TrueSkill)
3. Study FiveThirtyEight ELO implementations
4. Develop calibration methodology
5. Compare to market probabilities

#### Expected Outcome
ELO implementation guide with sport-specific parameters and probability conversion formulas.

#### Notes
FiveThirtyEight has excellent documentation on their NFL, NBA, and soccer ELO systems.

---

### [TASK-009] Momentum Strategies in Prediction Markets

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research momentum and trend-following strategies for prediction markets. Investigate whether price trends persist and can be profitably traded on platforms like Polymarket and Kalshi.

#### Hypothesis
Prediction market prices exhibit short-term momentum as information gradually incorporates, creating opportunities for trend-following strategies.

#### Data Required
- Historical prediction market prices (minute/hourly)
- Market resolution outcomes
- Trading volume data
- Transaction costs

#### Methodology
1. Collect historical price data from Polymarket/Kalshi
2. Test for autocorrelation in price changes
3. Backtest momentum indicators (MA crossovers, RSI)
4. Account for transaction costs and slippage
5. Identify market types where momentum exists

#### Expected Outcome
Analysis of momentum in prediction markets with strategy recommendations if profitable opportunities exist.

#### Notes
Reference QuantPedia research on systematic edges in prediction markets.

---

### [TASK-010] Contrarian/Fade-the-Public Strategies

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research contrarian betting strategies that bet against public money. Investigate when "fading the public" is profitable and identify indicators of public bias.

#### Hypothesis
Public bettors have systematic biases (home team, favorites, popular teams) that create value in betting against heavily lopsided action.

#### Data Required
- Public betting percentages (Action Network, etc.)
- Line movement data
- Game outcomes
- Sharp vs. public money indicators

#### Methodology
1. Document sources for public betting percentages
2. Identify historical public biases by sport
3. Backtest contrarian strategies
4. Distinguish public vs. sharp money
5. Define trigger thresholds for contrarian bets

#### Expected Outcome
Contrarian betting framework with identified biases and profitable thresholds.

#### Notes
Key sources: Action Network public percentages, Sports Insights, Vegas Insider.

---

### [TASK-011] Sharp Money Tracking

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Research methods for identifying and following "sharp" (professional) money in betting markets. Document reverse line movement, steam moves, and other sharp indicators.

#### Hypothesis
Following sharp money by identifying reverse line movement and steam moves produces positive expected value without requiring sophisticated models.

#### Data Required
- Real-time line movement data
- Public betting percentages
- Historical sharp move data
- Professional bettor case studies

#### Methodology
1. Define sharp money indicators
2. Document reverse line movement patterns
3. Research steam move detection
4. Evaluate Pinnacle as sharp benchmark
5. Backtest sharp-following strategies

#### Expected Outcome
Sharp money tracking system with defined indicators and historical performance analysis.

#### Notes
Key concept: Pinnacle lines are considered closest to "true" odds due to sharp bettor activity.

---

### [TASK-012] Line Movement Analysis

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research patterns in betting line movements from opening to closing. Investigate which line moves contain predictive information and how to exploit them.

#### Hypothesis
Closing Line Value (CLV) is highly predictive of long-term profitability; systematic analysis of line movements can identify when markets are adjusting to information.

#### Data Required
- Opening and closing lines
- Timestamped line movement data
- Game outcomes
- Line movement catalysts (injuries, weather)

#### Methodology
1. Collect historical opening/closing lines
2. Analyze typical movement patterns
3. Identify information-driven vs. noise moves
4. Calculate CLV distribution by bet type
5. Build line movement monitoring system

#### Expected Outcome
Line movement analysis framework with identified patterns and CLV tracking methodology.

#### Notes
Focus on understanding why lines move, not just that they move.

---

### [TASK-013] Market Making Strategies

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Low

#### Description
Research market making strategies for prediction markets. Investigate how to provide liquidity on Polymarket and profit from bid-ask spreads while managing inventory risk.

#### Hypothesis
Providing liquidity on prediction markets can generate consistent returns if inventory risk is properly managed and adverse selection is minimized.

#### Data Required
- Order book data from prediction markets
- Bid-ask spread distributions
- Trade flow data
- Market maker case studies

#### Methodology
1. Document prediction market mechanics
2. Research traditional market making theory
3. Analyze spreads and liquidity on Polymarket
4. Evaluate adverse selection risks
5. Design inventory management approach

#### Expected Outcome
Market making feasibility analysis with strategy outline if opportunities exist.

#### Notes
Consider capital requirements, technology needs, and regulatory constraints.

---

## Category 3: Platform Deep Dives

### [TASK-014] PredictIt Platform Analysis

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Low

#### Description
Analyze the PredictIt prediction market platform. Document fee structure, trading limits, available markets, and compare to Polymarket and Kalshi for strategy suitability.

#### Hypothesis
PredictIt's fee structure (10% on profits, 5% on withdrawals) and $850 position limits significantly impact strategy viability compared to Polymarket/Kalshi.

#### Data Required
- PredictIt fee documentation
- Available market types
- Historical price data
- Comparison with other platforms

#### Methodology
1. Document PredictIt mechanics and fees
2. Analyze available markets
3. Calculate fee impact on strategies
4. Compare liquidity and spreads
5. Identify unique opportunities

#### Expected Outcome
PredictIt platform guide with strategy recommendations accounting for its unique constraints.

#### Notes
PredictIt is CFTC-authorized like Kalshi but with different market focus (primarily political).

---

### [TASK-015] Betfair Exchange Model

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research the Betfair betting exchange model. Document how exchanges differ from traditional bookmakers, the lay betting mechanism, and liquidity dynamics.

#### Hypothesis
Betting exchanges offer superior odds due to peer-to-peer matching, but require understanding of lay betting and commission structures for profitable trading.

#### Data Required
- Betfair exchange documentation
- Historical exchange odds
- Liquidity patterns
- Commission structures

#### Methodology
1. Document exchange vs. bookmaker model
2. Explain back/lay betting mechanics
3. Analyze typical liquidity patterns
4. Research exchange trading strategies
5. Compare commission impact

#### Expected Outcome
Betfair exchange guide with strategy applications for sports trading.

#### Notes
Betfair is not available in US; research for international strategy development.

---

### [TASK-016] Pinnacle as Sharp Benchmark

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Research why Pinnacle is considered the "sharp" bookmaker benchmark. Document their business model, why professionals prefer it, and how to use Pinnacle lines for evaluation.

#### Hypothesis
Pinnacle's low margins and acceptance of professional bettors means their closing lines are the most efficient, making them the best benchmark for probability estimation.

#### Data Required
- Pinnacle line data
- Business model documentation
- Comparison with other books
- Closing line accuracy studies

#### Methodology
1. Document Pinnacle business model
2. Explain why sharps prefer Pinnacle
3. Analyze Pinnacle line efficiency
4. Research closing line as probability benchmark
5. Develop CLV measurement framework

#### Expected Outcome
Guide for using Pinnacle lines as sharp benchmark with CLV tracking methodology.

#### Notes
Key concept: If you consistently beat Pinnacle's closing line, you likely have an edge.

---

### [TASK-017] Asian Handicap Markets

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Low

#### Description
Research Asian Handicap (AH) betting markets for soccer. Document how AH works, why it's popular in Asia, and potential advantages over traditional 1X2 betting.

#### Hypothesis
Asian Handicap markets have higher limits, tighter spreads, and eliminate draw outcomes, making them more suitable for large-scale systematic betting.

#### Data Required
- Asian Handicap rules and variations
- Comparison with European markets
- Historical AH odds
- Market efficiency research

#### Methodology
1. Document AH mechanics (full, half, quarter lines)
2. Compare to traditional 1X2 betting
3. Analyze liquidity differences
4. Research AH-specific strategies
5. Evaluate for arbitrage opportunities

#### Expected Outcome
Asian Handicap guide with strategy recommendations for soccer betting.

#### Notes
Quarter goals (0.25, 0.75, etc.) create unique hedging opportunities.

---

## Category 4: Academic Literature Reviews

### [TASK-018] Favorite-Longshot Bias Literature Review

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Conduct a literature review of the favorite-longshot bias in betting markets. Document evidence, explanations, and whether it remains exploitable in modern markets.

#### Hypothesis
The favorite-longshot bias (longshots overbet, favorites underbet) has diminished in efficient markets but may persist in specific contexts (small markets, novelty bets).

#### Data Required
- Academic papers on favorite-longshot bias
- Historical odds and outcomes data
- Market efficiency studies
- Recent empirical analyses

#### Methodology
1. Collect seminal papers on favorite-longshot bias
2. Document proposed explanations (risk-seeking, utility)
3. Review recent empirical evidence
4. Analyze persistence in modern markets
5. Identify potentially exploitable contexts

#### Expected Outcome
Literature review document with summary of findings and modern exploitability assessment.

#### Notes
Key papers: Griffith (1949) original observation, Snowberg & Wolfers (2010) comprehensive review.

---

### [TASK-019] Closing Line Value (CLV) Research

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Research the importance of Closing Line Value (CLV) as a predictor of betting success. Document methodology for measuring CLV and its relationship to long-term profitability.

#### Hypothesis
CLV is the most reliable indicator of betting skill; consistent positive CLV predicts long-term profitability regardless of short-term results.

#### Data Required
- Academic papers on CLV
- Professional bettor case studies
- CLV calculation methodologies
- Historical line and outcome data

#### Methodology
1. Document CLV definition and calculation
2. Research academic evidence for CLV importance
3. Study professional bettor approaches
4. Analyze CLV vs. profit correlation
5. Develop CLV tracking system

#### Expected Outcome
CLV methodology guide with evidence summary and tracking implementation.

#### Notes
CLV is often called "the most important metric in sports betting."

---

### [TASK-020] Market Efficiency by Sport

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Review academic literature on market efficiency across different sports. Identify which sports and bet types show more inefficiency and potential for alpha.

#### Hypothesis
Market efficiency varies by sport and bet type; less popular sports, in-play markets, and player props show more inefficiency than major sport point spreads.

#### Data Required
- Academic papers on sports market efficiency
- Efficiency measures by sport
- Bet type comparisons
- Historical performance data

#### Methodology
1. Define market efficiency in betting context
2. Survey literature by sport
3. Compare efficiency across bet types
4. Identify systematic inefficiencies
5. Prioritize research areas

#### Expected Outcome
Market efficiency summary by sport/bet type with research prioritization recommendations.

#### Notes
Consider: NFL spreads (very efficient) vs. Korean baseball (less efficient).

---

### [TASK-021] Behavioral Biases in Betting

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Review research on behavioral biases affecting bettors. Document home bias, recency bias, representativeness bias, and how markets may not fully correct these biases.

#### Hypothesis
Behavioral biases create predictable patterns in betting markets that can be exploited by identifying when public perception systematically differs from true probabilities.

#### Data Required
- Behavioral finance literature
- Sports betting behavioral studies
- Public betting percentage data
- Historical bias patterns

#### Methodology
1. Catalog known behavioral biases
2. Review sports betting specific research
3. Document bias manifestations in odds
4. Analyze bias persistence
5. Develop bias-exploitation frameworks

#### Expected Outcome
Behavioral bias catalog with identified opportunities and exploitation strategies.

#### Notes
Key biases: home team bias, big-name team bias, recency bias, streak thinking.

---

## Category 5: Sport/Event Specific

### [TASK-022] NFL Betting Markets Deep Dive

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Comprehensive analysis of NFL betting markets. Document spread betting, totals, player props, key numbers, and NFL-specific factors affecting betting strategy.

#### Hypothesis
NFL markets are highly efficient for spreads but less so for totals and player props; key number analysis (3, 7) provides structural edge opportunities.

#### Data Required
- Historical NFL odds and outcomes
- Key number distributions
- Player prop data
- Situational factors (rest, weather, travel)

#### Methodology
1. Document NFL betting market types
2. Analyze key number significance (3, 7, 10)
3. Research situational factors
4. Evaluate prop market efficiency
5. Identify systematic opportunities

#### Expected Outcome
NFL betting market guide with specific strategy recommendations and key number analysis.

#### Notes
Consider teaser strategies, look-ahead lines, TNF/MNF dynamics.

---

### [TASK-023] NBA Betting Markets Deep Dive

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** High

#### Description
Comprehensive analysis of NBA betting markets. Document spread betting, totals, player props, rest patterns, and NBA-specific factors affecting betting strategy.

#### Hypothesis
NBA player prop markets are inefficient due to load management and rest patterns; totals are affected by pace changes that markets slowly adjust to.

#### Data Required
- Historical NBA odds and outcomes
- Rest and back-to-back data
- Player prop data
- Pace and efficiency stats

#### Methodology
1. Document NBA betting market types
2. Analyze rest pattern impact
3. Research pace/tempo adjustments
4. Evaluate player prop efficiency
5. Identify live betting opportunities

#### Expected Outcome
NBA betting market guide with specific strategy recommendations for props and totals.

#### Notes
Key factors: back-to-backs, load management, playoff seeding games, garbage time impact on totals.

---

### [TASK-024] Soccer Betting Markets

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Analysis of global soccer betting markets. Compare European leagues, Asian markets, and in-play betting opportunities. Document league-specific inefficiencies.

#### Hypothesis
Soccer betting efficiency varies significantly by league; lower-tier leagues and in-play markets offer more opportunities than Premier League match odds.

#### Data Required
- Historical soccer odds (multiple leagues)
- Asian market comparison
- In-play odds data
- League-by-league efficiency studies

#### Methodology
1. Document global soccer betting landscape
2. Compare efficiency by league tier
3. Analyze European vs. Asian markets
4. Research in-play opportunities
5. Identify league-specific inefficiencies

#### Expected Outcome
Soccer betting market guide with league recommendations and in-play strategy analysis.

#### Notes
Consider: Premier League (very efficient) vs. Eredivisie, MLS, lower leagues.

---

### [TASK-025] Political Prediction Markets

**Assigned:** Unassigned
**Status:** Proposed
**Priority:** Medium

#### Description
Research political prediction markets on Polymarket and Kalshi. Analyze historical accuracy, integration with polling data, and unique characteristics of political betting.

#### Hypothesis
Political prediction markets are often more accurate than polls but exhibit specific biases (overconfidence in certain outcomes) that create trading opportunities.

#### Data Required
- Historical prediction market political prices
- Polling data
- Election outcomes
- Academic accuracy studies

#### Methodology
1. Document political market mechanics
2. Compare market prices to polls
3. Analyze historical accuracy
4. Identify systematic biases
5. Research poll integration methods

#### Expected Outcome
Political prediction market guide with polling integration recommendations and identified biases.

#### Notes
Reference: Vanderbilt study on Polymarket/Kalshi accuracy; SSRN price discovery research.

---

## Active Tasks

### High Priority

| Task | Owner | Status | Due |
|------|-------|--------|-----|
| Complete Polymarket API client | TBD | Not Started | Feb 15 |
| Complete Kalshi API client | TBD | Not Started | Feb 15 |
| [TASK-026] OddsHarvester Integration | Alfie, Max | Planned | Feb 28 |

### Medium Priority

| Task | Owner | Status | Due |
|------|-------|--------|-----|
| Research notebook template testing | TBD | Not Started | Feb 20 |
| Backtest framework design | TBD | Not Started | Feb 28 |

### Low Priority

| Task | Owner | Status | Due |
|------|-------|--------|-----|
| Additional documentation | - | Ongoing | - |

---

## Task Assignment Guidelines

1. **Claiming a task**: Edit this file and add your name to the Assigned field
2. **Status updates**: Update status as you progress (Proposed → In Progress → Review → Completed)
3. **Completion**: When done, move findings to `research/notebooks/` or your personal folder

---

## Completed Tasks

| Task | Owner | Completed |
|------|-------|-----------|
| Repository initialization | tan | 2025-02-01 |
| Documentation structure | tan | 2025-02-01 |
| Development tooling setup | tan | 2025-02-01 |

---

## Ideas Backlog

Tasks that may be picked up in the future:

- [ ] Web dashboard for monitoring
- [ ] Automated data collection pipelines
- [ ] ML model experimentation framework
- [ ] Integration with trading platforms

---

## Task Status Legend

| Status | Description |
|--------|-------------|
| Proposed | Task defined, not yet started |
| In Progress | Actively being worked on |
| Review | Research complete, pending review |
| Completed | Finalized and documented |

---

## Weekly Updates

### Week of 2025-02-03

*To be updated in weekly standup*

---

## Notes

- Use `/weekly-standup` to generate weekly progress summary
- Keep individual task details in your personal `team/<name>/TASKS.md`
- Major blockers should be raised in team chat

---

## Resources

- [Research Ideas](../research/ideas/README.md)
- [Platform Documentation](../docs/platforms/)
- [API Setup Guides](../docs/setup/)
- [Paper References](../research/papers/README.md)
