# Verified Paper Summary: CLV Modeling and NBA Betting Volume

This summary covers the two verified papers plus one additional refereeing-bias paper requested for project framing.

## 1) Counting Your Customers the Easy Way: An Alternative to the Pareto/NBD Model

**Authors:** Peter S. Fader, Bruce G. S. Hardie, Ka Lok Lee  
**Year:** 2005  
**Journal:** Marketing Science  
**DOI:** https://doi.org/10.1287/mksc.1040.0098

### What the paper does
This paper introduces the **BG/NBD model** as a practical alternative to the Pareto/NBD model for non-contractual settings where customer churn is not directly observed. Instead of trying to observe "alive vs churned" status, BG/NBD infers latent customer activity from transaction histories using:
- `frequency` (how often a customer purchased),
- `recency` (how recently they purchased),
- observation window length.

The authors show BG/NBD is substantially easier to estimate while delivering similar managerial usefulness for predicting repeat transactions.

### Key findings
- BG/NBD provides a simpler and more stable estimation workflow than Pareto/NBD.
- Despite simplification, predictive performance is strong for future transaction counts.
- Customer-level heterogeneity in purchase rate and dropout risk is critical to forecast long-run value.

### Why this matters for NBA betting
For sportsbook-style NBA data, bettors often appear, disappear, and reappear without explicit cancellation events. This is exactly the non-contractual environment BG/NBD was designed for. It enables:
- estimating bettor survival probability,
- predicting expected future number of bets,
- building a forward-looking CLV framework using behavioral data rather than assumptions about stated intent.

### How we can use it in our project
- Build a bettor-activity model from bet-level histories (`recency`, `frequency`, `tenure`).
- Predict expected future betting events by user segment (casual, regular, high-frequency).
- Combine BG/NBD outputs with monetary value estimates (average stake, hold contribution, net margin) to estimate CLV.
- Use model outputs for retention targeting, promo allocation, and cohort forecasting around key NBA windows (opening week, Christmas slate, playoffs).

### Interesting insight
The paper’s most useful practical insight is that we do not need the most mathematically complex CLV model to get actionable predictions; a simpler model can deliver most of the value with less operational friction.

---

## 2) The Determinants of Betting Volume for Sports in North America: Evidence of Sports Betting as Consumption in the NBA and NHL

**Authors:** Rodney J. Paul, Andrew P. Weinbach  
**Year:** 2010  
**Journal:** International Journal of Sport Finance  
**DOI:** https://doi.org/10.1177/155862351000500205

### What the paper does
This paper analyzes what drives **betting volume (handle)** in NBA and NHL games using sportsbook transaction/market data. Instead of focusing only on market efficiency, it studies betting demand as a behavioral outcome.

The central framing is that sports betting is often partly a **consumption activity** (entertainment/fandom), not purely an investment activity.

### Key findings
- **Team quality** and game attractiveness are significant drivers of betting volume.
- **Television exposure/media visibility** materially increases handle.
- **Calendar and timing effects** (day/time/month context) influence volume.
- Aggregate betting behavior is consistent with bettors purchasing entertainment utility, not just expected-value opportunities.

### Why this matters for NBA
NBA betting markets are high-frequency and media-driven. If handle is strongly consumption-driven, then:
- market demand can shift with narratives and attention cycles,
- liquidity and price pressure may vary systematically by game visibility,
- bettor behavior may be less price-sensitive in marquee events.

This helps explain why some lines move with public demand even when informational content is limited.

### How we can use it in our project
- Build a **betting-demand layer** separate from outcome prediction.
- Include handle/attention features such as:
  - national TV flag,
  - team popularity proxy,
  - star-player availability,
  - prime-time/weekend indicator,
  - rivalry/playoff-race context.
- Use predicted demand for execution strategy:
  - identify high-liquidity windows,
  - adjust expected slippage,
  - time entries around likely public-driven moves.

### Interesting insight
A major insight is that market participation volume itself carries behavioral signal. In practical terms, we should model both **who is betting/how much** and **what is likely to happen in the game**; these are related but distinct processes.

---

## 3) Do Star Players Receive Preferential Treatment?

**Topic:** NBA officiating bias and superstar treatment

### What the paper does
This paper tests whether NBA referees call games differently for star players versus non-stars, with additional focus on high-pressure moments.

### Key findings
- Star players receive more foul calls in their favor than comparable non-star players.
- The preferential effect is stronger in late-game situations.
- The pattern is consistent with referees responding to player reputation and pressure, not only on-court contact.

### Why this matters for NBA betting
If officiating is systematically tilted toward stars, then late-game outcomes can shift in ways not fully captured by standard team-strength models. That affects:
- spread-cover probability in close games,
- total points via free-throw volume,
- player prop markets tied to points and fouls drawn.

### How we can use it in our project
- Add referee-star interaction features:
  - star presence indicator,
  - late-game state indicator (for example, last 5 minutes in close-score games),
  - crew-level foul tendency.
- Track whether star-biased whistle rates create pricing gaps in spreads/totals/props.
- Use this as a conditional adjustment, not a global rule, and validate out-of-sample by season and officiating crew.

### Interesting insight
The core takeaway is microstructure-oriented: reputation effects can enter the game through officiating, which then propagates into betting markets through late-game scoring and possession outcomes.

---

## Combined implications for our NBA project

Using these papers together gives a three-layer framework:

1. **User-value layer (BG/NBD):**
   Forecast long-run bettor activity and CLV at user/cohort level.

2. **Market-demand layer (Paul & Weinbach):**
   Forecast game-level betting volume and demand pressure.

3. **Officiating-bias layer (star treatment):**
   Model how reputation-sensitive officiating may alter late-game outcomes and market pricing.

Integrated together, this supports:
- better forecasting of revenue and risk by NBA schedule segment,
- smarter promotion spend (target users with highest incremental lifetime value),
- improved market execution by anticipating when public attention may distort demand and line dynamics,
- stronger game-level pricing adjustments in star-driven, high-leverage game states.

## Suggested implementation roadmap
1. Build a bettor transaction table and estimate BG/NBD baseline.
2. Validate holdout forecasts for future bet counts by cohort.
3. Build a game-level betting volume model with TV/team/time features.
4. Add officiating-bias features for star players in late-game contexts and test lift.
5. Link user CLV forecasts to game-demand and officiating signals for planning and strategy.
6. Add monitoring dashboards for calibration drift and seasonality (regular season vs playoffs).

## Sources
- Fader, Hardie, Lee (2005): https://ideas.repec.org/a/inm/ormksc/v24y2005i2p275-284.html
- Hardie paper page: https://www.brucehardie.com/papers/018/
- Paul & Weinbach (2010): https://ideas.repec.org/a/jsf/intjsf/v5y2010i2p128-140.html
- Journal issue page: https://journals.fitpublishing.com/ijsf/5-2/
- Star-player officiating paper: title provided by project notes (`Do Star Players Receive Preferential Treatment?`).
