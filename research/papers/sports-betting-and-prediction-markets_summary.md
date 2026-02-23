# Sports Betting and Prediction Markets: Key Research Summaries

## Scope and selection
This document summarizes high-signal academic papers and industry reports relevant to:
- favourite-longshot bias
- closing line value (CLV) and opening-vs-closing line information
- market efficiency
- quantitative methods for betting and prediction markets

## A. Favourite-Longshot Bias (FLB)

### 1) Snowberg, E., & Wolfers, J. (2010). *Explaining the Favorite-Longshot Bias: Is it Risk-Love or Misperceptions?*
- Source: NBER WP 15923 / Journal of Political Economy
- Link: https://www.nber.org/papers/w15923
- Methodology: Large horse-racing dataset across win and exotic pools; tests whether demand-side models (risk love vs probability misperception) jointly fit observed choices.
- Key findings: Evidence favors probability misperception (Prospect-Theory-style weighting) over pure risk-loving utility.
- Relevance to project: Supports modeling bettor behavior as probability distortion, not just utility-based risk preference. Useful for bias-correction layers on implied probabilities.

### 2) Shin, H. S. (1993). *Measuring the Incidence of Insider Trading in a Market for State-Contingent Claims*
- Source: The Economic Journal
- Link: https://academic.oup.com/ej/article/103/420/1141/5157258
- Methodology: Structural model where bookmakers set odds under insider-risk; estimates insider share from observed market spreads.
- Key findings: FLB can emerge from bookmaker risk management under asymmetric information.
- Relevance to project: Motivates using Shin-style probability extraction instead of naive normalization when converting odds to "true" probabilities.

### 3) Cain, M., Law, D., & Peel, D. (2000). *The Favourite-Longshot Bias and Market Efficiency in UK Football Betting*
- Source: Scottish Journal of Political Economy (metadata via EconPapers)
- Link: https://econpapers.repec.org/RePEc:bla:scotjp:v:47:y:2000:i:1:p:25-36
- Methodology: Fixed-odds UK football analysis for match outcomes and correct scores; regression-based expected-goals modeling.
- Key findings: FLB is present in UK football fixed-odds markets; some rules look profitable in-sample.
- Relevance to project: Strong precedent for sport-specific FLB diagnostics in soccer markets.

### 4) Berkowitz, J. P., Depken, C. A., & Gandar, J. M. (2017). *A favorite-longshot bias in fixed-odds betting markets: Evidence from college basketball and college football*
- Source: Quarterly Review of Economics and Finance
- Link: https://www.sciencedirect.com/science/article/pii/S1062976916000041
- Methodology: NCAA moneyline data; expected return profiles by favorite/longshot buckets.
- Key findings: Documents FLB in these US fixed-odds moneyline markets; heavy favorites approach break-even net of vig.
- Relevance to project: Indicates side-dependent calibration errors and suggests that "favorite tilts" may improve EV screening.

### 5) Whelan, K. (2026 issue / online 2025). *Market structure and prices in online betting markets: theory and evidence*
- Source: Oxford Economic Papers
- Link: https://academic.oup.com/oep/article/78/1/90/8244336
- Methodology: Theoretical and empirical analysis of online bookmaker pricing with imperfect competition.
- Key findings: FLB can arise from market structure and demand elasticity differences, not only behavioral errors.
- Relevance to project: Important for model design: some observed bias may be structural microstructure effect, not exploitable mispricing.

## B. CLV and Opening-vs-Closing Information (closest academic proxy to CLV literature)

### 6) Simon, J. (2024). *Inefficient Forecasts at the Sportsbook: An Analysis of Real-Time Betting Line Movement*
- Source: Management Science (INFORMS; metadata via IDEAS/RePEc)
- Link: https://ideas.repec.org/a/inm/ormnsc/v70y2024i12p8583-8611.html
- Methodology: 3,681 MLB games, four sportsbooks, full opening-to-closing line sequences.
- Key findings: Forecasts are mostly reliable, but line updates show overreaction and negative autocorrelation; weak-form efficiency is rejected in parts of the sequence.
- Relevance to project: Strong modern evidence that timing and path of line movement matter, not just close. Supports CLV tracking plus intraday execution features.

### 7) Krieger, K., & Fodor, A. (2013). *Price movements and the prevalence of informed traders: The case of line movement in college basketball*
- Source: Journal of Economics and Business
- Link: https://www.sciencedirect.com/science/article/abs/pii/S0148619513000295
- Methodology: Compares opening vs closing line informativeness across market segments with different informed-trader concentration.
- Key findings: Closing lines are more accurate than opening lines; information-based moves are more common in lower-profile games.
- Relevance to project: Supports CLV as a skill benchmark and suggests stratifying CLV by market visibility/liquidity.

### 8) Tsaris, P. (2021). *Market efficiency and the Greek fixed-odds betting market*
- Source: EuroMed Journal of Business
- Link: https://www.sciencedirect.com/org/science/article/pii/S1450219421000281
- Methodology: Opening and closing football odds (2016-2019) with linear probability/probit tests.
- Key findings: FLB and draw-bias present; opening odds and market structure still contain information beyond closing odds in some settings.
- Relevance to project: CLV is valuable but not sufficient alone; opening-line context and margin regime should be modeled jointly.

## C. Sports Betting Market Efficiency

### 9) Sauer, R. D. (1998). *The Economics of Wagering Markets*
- Source: Journal of Economic Literature (metadata via EconPapers)
- Link: https://econpapers.repec.org/RePEc:aea:jeclit:v:36:y:1998:i:4:p:2021-2064
- Methodology: Comprehensive literature review of wagering markets.
- Key findings: Markets are approximately efficient at first order, but show persistent anomalies tied to heterogeneous information, frictions, and costs.
- Relevance to project: Baseline framing: assume near-efficiency with narrow, conditional edges.

### 10) Levitt, S. D. (2004). *Why are Gambling Markets Organised so Differently from Financial Markets?*
- Source: Economic Journal
- Link: https://academic.oup.com/ej/article/114/495/223/5086012
- Methodology: NFL bookmaker pricing and quantity data; evaluates book behavior vs market-clearing logic.
- Key findings: Bookmakers can profit by setting biased prices that exploit bettor demand patterns rather than purely balancing books.
- Relevance to project: Suggests persistent demand-side distortions can survive in efficient-looking markets.

### 11) Angelini, G., & De Angelis, L. (2019). *Efficiency of online football betting markets*
- Source: International Journal of Forecasting
- Link: https://www.sciencedirect.com/science/article/pii/S0169207018301134
- Methodology: 41 bookmakers, 11 major European leagues, 2006-2017; forecast-based efficiency tests.
- Key findings: Efficiency differs by league and odds construction; mean market odds are more efficient than naive alternatives; best-odds selection can reveal residual inefficiencies.
- Relevance to project: Directly supports bookmaker-panel aggregation and best-price execution logic.

## D. Prediction Market Efficiency

### 12) Wolfers, J., & Zitzewitz, E. (2004). *Prediction Markets*
- Source: Journal of Economic Perspectives / NBER WP
- Link: https://www.nber.org/papers/w10504
- Methodology: Cross-context review of prediction markets and contract design.
- Key findings: Prediction markets are often accurate and competitive with sophisticated benchmarks; design details affect informativeness.
- Relevance to project: Conceptual framework for using event-contract prices as probabilistic forecasts.

### 13) Berg, J. E., Nelson, F. D., & Rietz, T. A. (2008). *Prediction market accuracy in the long run*
- Source: International Journal of Forecasting (metadata via EconPapers)
- Link: https://econpapers.repec.org/RePEc:eee:intfor:v:24:y:2008:i:2:p:285-300
- Methodology: Iowa Electronic Markets vs polling over multiple US presidential cycles.
- Key findings: Markets beat polls more often at long horizons.
- Relevance to project: Supports long-horizon signal extraction from market prices for medium-term contracts.

### 14) Angelini, G., De Angelis, L., & Singleton, C. (2022). *Informational efficiency and behaviour within in-play prediction markets*
- Source: International Journal of Forecasting
- Link: https://www.stir.ac.uk/research/hub/publication/1969462
- Methodology: High-frequency in-play exchange data around first-goal events in football.
- Key findings: Detects in-play inefficiencies and behavioral mispricing (including reverse FLB/favorite bias in contexts).
- Relevance to project: Strong template for event-time studies and post-news overreaction/reversal strategies.

### 15) Diercks, A. M., Katz, J. D., & Wright, J. H. (2026). *Kalshi and the Rise of Macro Markets*
- Source: NBER WP 34702
- Link: https://www.nber.org/papers/w34702
- Methodology: Compares Kalshi-implied macro forecasts with survey and market benchmarks.
- Key findings: Prediction markets can provide high-frequency and distributionally rich expectation signals for policy-sensitive outcomes.
- Relevance to project: Confirms practical value of exchange-like event contracts for real-time probability updating.

## E. Quantitative approaches for implementation

### 16) Hubacek, O., Sourek, G., & Zelezny, F. (2019). *Exploiting sports-betting market using machine learning*
- Source: International Journal of Forecasting (author lab page with citation)
- Link: https://ida.fel.cvut.cz/papers/hubacek2019exploiting.html
- Methodology: NBA model with (i) predictive signal less correlated with bookmaker odds, (ii) neural inputs on player-level data, (iii) portfolio-style stake allocation.
- Key findings: Profitability improves when model objective is not pure accuracy and includes bookmaker-divergence and allocation logic.
- Relevance to project: Very aligned with our objective function design (alpha over market, not headline accuracy).

### 17) Walsh, C., & Joshi, A. (2024). *Machine learning for sports betting: Should model selection be based on accuracy or calibration?*
- Source: Machine Learning with Applications (DOAJ/Bath portal)
- Link: https://doaj.org/article/2e36e6f3ec6a46b7b54308dee2d11c23
- Methodology: NBA modeling and simulated betting; compares model choice by accuracy vs probability calibration.
- Key findings: Calibration-based selection materially outperforms accuracy-based selection in betting return experiments.
- Relevance to project: Direct justification for using Brier/log-loss/ECE and reliability curves as model-selection gates.

## F. Industry reports (for market context, scale, and integrity risk)

### 18) American Gaming Association (2025). *State of the States 2025*
- Link: https://www.americangaming.org/resources/state-of-the-states-2025/
- Focus: US market size, state-by-state revenue/tax structure, growth in mobile betting.
- Relevance: Helps calibrate market selection, liquidity assumptions, and commercialization priorities.

### 19) UK Gambling Commission (2025). *Industry Statistics (Apr 2024 - Mar 2025)*
- Link: https://www.gamblingcommission.gov.uk/statistics-and-research/publication/industry-statistics-annual-report-financial-year-april-2024-to-march-2025
- Focus: UK gross gambling yield, remote vs land-based mix, segment-level trendline.
- Relevance: External benchmark for jurisdiction-specific market growth and regulatory constraints.

### 20) Sportradar Integrity Services (2025). *Integrity in Action: 2024 Global Analysis & Trends*
- Link: https://sportradar.com/content-hub/report/integrity-in-action-2024/
- Focus: Global suspicious-match patterns, sport/region distribution, AI-enabled monitoring trends.
- Relevance: Critical for operational risk filters (league-level integrity risk and event exclusion logic).

### 21) International Betting Integrity Association (2025). *2024 Annual Report*
- Link: https://ibia.bet/category/integrity-reports/  (report listing and open document)
- Focus: suspicious alert counts, sport/region concentration, sanction outcomes, monitoring coverage.
- Relevance: Supports risk governance for model deployment and market whitelist/blacklist policy.

## Cross-paper synthesis for this project
- FLB is robust but not uniform; direction and magnitude can vary by sport, market format, and competition level.
- CLV should be treated as a process KPI, not a standalone strategy. Academic evidence supports opening-to-closing informational improvement, but also shows exploitable path dynamics in some markets.
- Most markets are near-efficient in aggregate, implying edge is conditional, small, and capacity-sensitive.
- Probability calibration and microstructure-aware execution are repeatedly more important than raw classification accuracy.
