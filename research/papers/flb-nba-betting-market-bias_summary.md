# FLB NBA Betting Market & Bias Papers: In-Depth Summary

This note summarizes six NBA betting-market and bias papers with a focus on: (1) what each paper finds, (2) why it matters for our project, and (3) how to operationalize it in our pipeline.

## Paper 1: Revisiting the "Hot Hand" Hypothesis in the NBA Betting Market Using Actual Sportsbook Betting Percentages on Favorites and Underdogs

**Authors:** Rodney J. Paul, Andrew P. Weinbach, Brad R. Humphreys  
**Year:** 2011 (JGBE Vol. 5 No. 2; online publication listed as 2013)  
**Link:** https://www.ubplj.org/index.php/jgbe/article/view/569/0  
**DOI:** https://doi.org/10.5750/jgbe.v5i2.569

### In-Depth Summary of Findings
This paper revisits classic "hot hand" work in NBA betting by using actual sportsbook betting percentages, rather than assuming point spreads always represent a balanced book. That distinction matters because if books are not balancing risk, observed prices may partially reflect bookmaker strategy and bettor demand, not only unbiased probability forecasts.

Using a six-season NBA sample, the authors show two results that can appear contradictory but are actually complementary:
- Contrarian betting against streaking ("hot") teams did not produce abnormal profit beyond what an efficient market would allow.
- Bettors still exhibited a behavioral hot-hand belief: teams on winning streaks attracted significantly more bets, including in OLS and 2SLS frameworks.

Interpretation: bettor bias is visible in order flow, even when closing lines remain hard to beat ex post. This is a key microstructure result: demand can be biased while final prices are near efficient after market clearing.

### Why It Is Important for Our Project
- It separates `belief bias` from `tradable edge`, which is central to FLB-style work.
- It warns us not to infer inefficiency from sentiment or betting-share skew alone.
- It supports modeling the market as `public bias + bookmaker shading + informed correction`, not as a single unbiased mechanism.

### How We Can Use It
- Build a `streak sentiment` feature set (e.g., recent win/loss run, run quality, opponent-adjusted run).
- Track whether sentiment loads more strongly into `public bet share` proxies than into closing-line error.
- Test two-stage hypotheses:
  - Stage 1: bias exists in sentiment and ticket-share direction.
  - Stage 2: after vig and execution timing, edge survives or not.
- Add a report split: `bias-detection metrics` vs `profitability metrics`, so we do not conflate the two.

## Paper 2: Testing Profitability in the NBA Season Wins Total Betting Market

**Authors:** Bill M. Woodland, Linda M. Woodland  
**Year:** 2015  
**Journal:** International Journal of Sport Finance, 10(2), 160-174  
**Links:** https://ideas.repec.org/a/jsf/intjsf/v10y2015i2p160-174.html, https://fitpublishing.com/journals/international-journal-sport-finance-ijsf-102

### In-Depth Summary of Findings
This study shifts from single-game markets to `season wins totals` and asks whether that futures-style market is efficient. The authors frame betting rules around behavioral heuristics and compare NBA results with prior NFL season-wins evidence.

Core conclusions from the abstracted evidence:
- NBA season wins totals are somewhat more efficient than NFL analogs, but still show pockets of profitability.
- Profitable rules appear on both over and under sides, implying mispricing is not purely one-directional.
- The paper links inefficiency to systematic bettor behavior, including overweighting prior-season performance and sentiment for stronger teams.

Methodologically, this is important because season totals aggregate many latent factors (injuries, schedule strength, depth, coaching, variance, tanking incentives) into one quoted number, creating a longer-horizon sentiment test than daily spreads.

### Why It Is Important for Our Project
- It expands FLB/bias analysis beyond game lines to `long-horizon contracts`, which resemble prediction-market positions we may trade.
- It identifies a repeatable bias channel: recency and team-strength sentiment can distort pricing.
- It provides a template for rule-based profitability testing where transaction costs and vig-equivalent thresholds are explicit.

### How We Can Use It
- Add a `season totals` module with features such as prior-season wins, offseason roster shock, and consensus power ratings.
- Include sentiment-adjusted priors for popular teams and regress toward fundamentals.
- Backtest over/under strategies with conservative frictions and sample splits:
  - train on pre-season historical windows
  - test on out-of-sample seasons
- Compare results to game-level market efficiency metrics to see where edge is structurally stronger.

## Paper 3: An Examination of Prediction Market Efficiency: NBA Contracts on Tradesports

**Author:** Richard Borghesi  
**Year:** 2009 issue (JPM Vol. 3 No. 2; online publication listed as 2012)  
**Link:** https://www.ubplj.org/index.php/jpm/article/view/462  
**DOI:** https://doi.org/10.5750/jpm.v3i2.462

### In-Depth Summary of Findings
Borghesi tests absolute and relative efficiency in NBA contracts on Tradesports. Instead of point spreads, the paper studies binary-contract prices directly, which allows cleaner probability interpretation (price ~ implied probability under assumptions).

Main findings:
- Certain price buckets are systematically misvalued.
- Mid-range contracts around 25 and 75 showed calibration errors in opposite directions.
- Contrary to some theory expecting very low-priced contracts to be overpriced, contracts near 2.5 sometimes won more often than expected.
- The NBA prediction market appeared more efficient than the NFL counterpart studied in related work, but still not perfectly calibrated.

This is effectively an FLB-style calibration analysis on contract prices: errors are not uniform across probability bands.

### Why It Is Important for Our Project
- Directly relevant to prediction-market trading logic (Kalshi/Polymarket style framing).
- Shows that `bucketed calibration` can uncover exploitable structure even when global efficiency appears high.
- Supports probability-band diagnostics as a core monitoring tool.

### How We Can Use It
- Add probability-bin reliability tests (e.g., 0-5%, 5-10%, ... , 95-100%).
- Track per-bin realized win rate vs quoted probability and convert gaps into expected value maps.
- Use bin-aware position sizing caps to avoid over-allocation to historically noisy tails.
- Report market quality by band, not only aggregate Brier/log-loss.

## Paper 4: Do Gamblers Correctly Price Momentum in NBA Betting Markets?

**Author:** Jeremy Arkes  
**Year:** 2011 issue (JPM Vol. 5 No. 1; online publication listed as 2012)  
**Link:** https://www.ubplj.org/index.php/jpm/article/view/485  
**DOI:** https://doi.org/10.5750/jpm.v5i1.485

### In-Depth Summary of Findings
Arkes evaluates whether gamblers correctly process momentum information. A key contribution is improved momentum measurement: the signal includes opponent strength and characteristics of wins/losses, rather than crude streak counts.

Main results from the abstract:
- Evidence supports a real momentum effect in NBA outcomes under the improved measurement design.
- Bettors do incorporate momentum into prices/beliefs.
- Bettors significantly overstate momentum magnitude.
- Despite this misperception, the distortion is generally not large enough to produce robust profit opportunities.

So the paper identifies an information-processing bias that is directionally correct but quantitatively exaggerated.

### Why It Is Important for Our Project
- It suggests that `feature quality` (how momentum is measured) is decisive.
- It aligns with a recurring theme: detectable bias does not guarantee net tradable alpha.
- It reinforces the need to model `effect size overstatement`, not only sign errors.

### How We Can Use It
- Engineer opponent-adjusted momentum features instead of raw win streaks.
- Estimate separate coefficients for:
  - true predictive momentum effect
  - market-implied momentum premium
- Trade only when the premium exceeds uncertainty and cost thresholds.
- Add shrinkage/regularization so momentum-driven signals do not become overconfident.

## Paper 5: NBA Gambling Inefficiencies: A Second Look

**Authors:** William Compton, Kevin Sigler  
**Year:** 2012 (The Sport Journal posting date)  
**Link:** https://thesportjournal.org/article/nba-gambling-inefficiencies-a-second-look/

### In-Depth Summary of Findings
Compton and Sigler re-test NBA market efficiency using log-likelihood ratio methods for both point spreads and totals over 2000-01 through 2007-08 (over 10,000 games).

Key results:
- Totals market: betting overs was broadly a fair bet; high-total subsets showed elevated hit rates at times but generally did not reject fair-bet nulls.
- Spread market: overall evidence favored efficiency; broad underdog strategies were not persistently profitable.
- Exception: home underdogs of +10 or more showed profitability in a very small sub-sample, with inefficiency fading in more recent data.

The paper emphasizes market adaptation: anomalies documented in earlier periods can attenuate as informed bettors and line adjustment mechanisms arbitrage them away.

### Why It Is Important for Our Project
- It is a caution against overfitting legacy anomalies.
- It highlights sample-size fragility in extreme subgroups (e.g., large home dogs).
- It supports rolling revalidation and regime checks as mandatory.

### How We Can Use It
- Implement walk-forward backtests by era and rule-decay tracking.
- Require minimum sample and uncertainty-adjusted thresholds before promoting a rule.
- Maintain an anomaly half-life dashboard: when a pattern weakens, reduce allocation automatically.
- Distinguish statistically significant edges from economically meaningful edges after vig.

## Paper 6: Machine Learning for Sports Betting: Should Model Selection Be Based on Accuracy or Calibration?

**Authors:** Conor Walsh, Alok Joshi  
**Year:** 2023 preprint; peer-reviewed publication in 2024 (Machine Learning with Applications, Vol. 16, 100539)  
**Links:** https://arxiv.org/abs/2303.06021, https://doi.org/10.1016/j.mlwa.2024.100539

### In-Depth Summary of Findings
Walsh and Joshi compare two model-selection philosophies on NBA betting:
- choose models by predictive accuracy
- choose models by probability calibration

Their experiments show calibration-led model selection outperformed accuracy-led selection in betting ROI. The practical argument is that betting is a pricing decision under uncertainty, so probability quality matters more than top-1 classification rate.

This paper also links naturally to Kelly logic: miscalibrated probabilities can cause systematically wrong stake sizing, even when direction accuracy seems acceptable.

### Why It Is Important for Our Project
- It gives a concrete model governance rule: optimize for calibration when outputs feed betting decisions.
- It helps bridge older behavioral-bias literature with modern ML execution.
- It provides a defensible framework for model choice, especially for probability-based position sizing.

### How We Can Use It
- Make calibration metrics first-class in model selection (`Brier`, reliability curves, ECE-style diagnostics).
- Apply post-hoc calibration methods (e.g., isotonic/Platt) and compare ROI impact.
- Tie staking to confidence only after calibration validation.
- In model reports, rank candidates by `risk-adjusted betting return + calibration`, not raw accuracy.

## Cross-Paper Synthesis for FLB/NBA Work

### What these papers jointly suggest
- Behavioral biases are real (hot-hand belief, momentum overstatement, team-strength sentiment).
- Markets can still be close to efficient at tradeable horizons after informed correction.
- Mispricing is often local (specific probability bands, specific subgroups, specific regimes), not universal.
- Calibration and market microstructure diagnostics are essential for extracting durable edge.

### Recommended project implementation priorities
1. Build a `bias diagnostics layer`:
   - streak/momentum sentiment factors
   - favorite/longshot and popularity indicators
   - probability-bin calibration curves
2. Build an `edge qualification layer`:
   - net-of-vig EV
   - uncertainty bands and minimum sample requirements
   - out-of-sample and rolling-window decay tests
3. Build an `execution layer`:
   - calibration-first model governance
   - fractional Kelly with confidence caps
   - regime-aware exposure limits for fragile anomalies

