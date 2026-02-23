# Presentation Highlights: Sports Betting and Prediction Markets

## 1) What the literature says in one slide
- Markets are often close to efficient, but not perfectly efficient in all segments or times.
- Favourite-longshot bias is robust across many settings, but mechanism varies (behavioral misperception, insider risk, and market structure).
- Closing prices are typically more informative than opening prices, making CLV a useful execution-quality KPI.
- CLV is not enough on its own: line-path dynamics and market context can still create or erase edge.
- Quant models win when they optimize calibrated probabilities and decision quality, not raw hit rate.

## 2) High-confidence findings for strategy design
- `FLB`: expect systematic price distortion in tails; test by sport/league/market type.
- `CLV`: track as process metric; positive CLV usually indicates better information timing, but does not guarantee positive realized PnL in short samples.
- `Efficiency`: treat alpha as narrow and conditional; require strong cost, limits, and slippage controls.
- `Modeling`: prioritize calibration (Brier/log-loss/ECE), then expected value, then portfolio staking.

## 3) Recommended analytics stack (project-ready)
- Fair-probability engine:
  - remove vig with both proportional normalization and Shin adjustment
  - compare model probabilities vs fair market probabilities
- Bias diagnostics:
  - FLB curves: expected ROI by implied-probability decile
  - favorite vs longshot residual calibration plots
- CLV dashboard:
  - pre-bet line, post-bet close, edge delta by market and timestamp
  - decompose CLV by liquidity class and game profile
- Efficiency tests:
  - opening-to-closing drift predictability
  - autocorrelation and overreaction around major line moves/news
- Staking/risk:
  - fractional Kelly with drawdown caps and correlation-aware sizing

## 4) Quantitative methods from reviewed papers
- Time-series line movement models (real-time inefficiency tests)
- Event-study methodology for in-play shocks (goals, injuries, lineup announcements)
- Panel models across bookmakers (consensus vs best-odds benchmarks)
- ML with probability calibration and market-divergence objective functions
- Portfolio optimization for multi-bet allocation under uncertainty

## 5) What to communicate to stakeholders
- "Beating close" is a necessary quality signal but not the full definition of edge.
- Edges are expected to be small; process discipline matters more than isolated big wins.
- Strategy should combine:
  - pricing bias detection
  - execution timing
  - risk-aware sizing
- Integrity and compliance risk screening is mandatory for deployment.

## 6) Suggested meeting narrative (5 minutes)
1. Market baseline: mostly efficient, small conditional mispricings.
2. Bias evidence: FLB and demand distortions create recurring structure.
3. Execution evidence: closing lines generally assimilate information better.
4. Modeling implication: calibration-first ML + CLV monitoring + Kelly-style risk controls.
5. Action plan: run sport-specific FLB diagnostics, launch CLV tracker, and test line-path alpha hypotheses.

## 7) Immediate action items for our team
1. Build a unified odds panel with opening, intra-day, and closing snapshots.
2. Implement vig removal variants and compare calibration to outcomes.
3. Add CLV metrics to backtests and live paper-trading logs.
4. Segment results by league liquidity, bookmaker, and bet type.
5. Add integrity-risk filters using IBIA/Sportradar flagged contexts.
