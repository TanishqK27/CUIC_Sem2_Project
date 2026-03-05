<!-- markdownlint-disable MD024 -->

## Paper 1: Machine learning for sports betting: should model selection be based on accuracy or calibration?

**Authors:** Conor Walsh, Alok Joshi
**Year:** 2024
**Link:** <https://arxiv.org/abs/2303.06021>

### Key Idea (extended)

This paper asks a very practical question: if a model is going to be used for betting decisions, should we choose it because it predicts winners more accurately, or because its predicted probabilities are well calibrated (for example, when it says 60%, that event happens about 60% of the time)? The authors argue that betting is a probability-pricing problem, not just a classification problem, so calibration should matter more than raw hit rate. They train multiple machine-learning models on multi-season NBA data and then test betting performance using real published bookmaker odds.

The central result is that model-selection by calibration produced materially better return profiles than model-selection by accuracy. In other words, a model can be "good" at picking winners and still be bad for betting if its confidence is mis-scaled. The paper reframes sports betting as a decision-theoretic pipeline where probability quality drives value detection and stake sizing, making calibration a first-class criterion rather than a secondary diagnostic.

### Relevant Findings

- Models selected by calibration metrics produced higher betting returns than models selected by accuracy alone.
- Accuracy was a weak proxy for profitability in betting markets.
- Reliable probability estimation is critical when model outputs are used for value-based bet sizing.

### How We Could Use This

Use calibration-first model evaluation (for example, Brier score and reliability analysis) before betting simulations. This directly supports Kelly-style sizing, where probability quality matters more than raw classification accuracy.

## Paper 2: Sports Betting: an application of machine learning to the game prediction

**Authors:** Eryi Wang, Xinyi Yin, Yao Li, Tianyu Wang
**Year:** 2025
**Link:** <https://ace.ewapub.com/article/view/20626>

### Key Idea (extended)

This paper builds an end-to-end football betting workflow: collect historical European league match data (2008-2016), engineer predictive features, train a broad model set (including Random Forest, Logistic Regression, KNN, Gaussian Process Regression, AdaBoost, XGBoost, and LightGBM), and then evaluate both forecast quality and downstream betting returns. That structure is important because it treats betting as an applied ML decision system rather than a standalone classification benchmark.

The authors report that ensemble tree methods, especially LightGBM and AdaBoost, were among the strongest performers for match-outcome prediction, and they extend the setup with a double-chance framing plus simulation-based staking to test economic viability. Their reported positive margin (around 3%) is less about claiming a universal edge and more about showing how model choice, feature design, and market-aligned bet construction interact. The paper is useful as a reproducible template for connecting model outputs to actionable betting decisions.

### Relevant Findings

- LightGBM and AdaBoost were among the strongest-performing models in the study.
- The simulated probability-based betting strategy reported a positive margin (about 3%).
- Feature engineering and outcome encoding choices materially affected results.

### How We Could Use This

Adopt a similar pipeline that compares several classifiers and evaluates both forecast metrics and realized betting return. It is a practical template for moving from model accuracy to decision-level profitability.

## Paper 3: Sports betting: an application of neural networks and modern portfolio theory to the English Premier League

**Authors:** Vélez Jiménez, Román Alberto, José Manuel Lecuanda Ontiveros, Edgar Possani
**Year:** 2023
**Link:** <https://arxiv.org/abs/2307.13807>

### Key Idea (extended)

This paper combines three layers that are often treated separately: match-outcome forecasting (via deep neural networks), utility-based bet valuation (Von Neumann-Morgenstern expected utility), and capital allocation (Kelly-style plus modern portfolio theory). Rather than deciding each bet in isolation, the method treats a betting slate as a portfolio allocation problem where expected return and risk should be optimized jointly. The experiments are run on English Premier League data, with explicit comparison between broader "complete" and constrained "restricted" betting strategies.

The key conceptual contribution is the shift from "which team wins?" to "how should limited bankroll be distributed across correlated opportunities?" This brings diversification and risk control directly into the betting engine, not as a post-processing step. The paper's high reported simulated growth in the tested period is paired with the broader message that portfolio construction can be as important as predictive accuracy when the objective is long-run capital growth under uncertainty.

### Relevant Findings

- Neural-network forecasts combined with Kelly-informed portfolio sizing showed strong simulated bankroll growth.
- Diversifying across multiple bets reduced risk versus isolated single-bet sizing.
- Capital allocation strategy was a major driver of long-run outcomes, alongside model quality.

### How We Could Use This

Extend our workflow from single-bet expected-value checks to portfolio-level optimization across opportunities in the same slate. This is directly relevant if we want correlated, risk-aware Kelly sizing.

## Paper 4: Exploiting sports-betting markets using machine learning

**Authors:** Ondřej Hubáček, Gustav Šourek, Filip Železný
**Year:** 2019
**Link:** <https://doi.org/10.1016/j.ijforecast.2019.01.001>

### Key Idea (extended)

This paper proposes a forecasting-and-betting framework designed specifically to exploit market inefficiencies, not merely to maximize prediction accuracy. Its first major idea is to optimize models for profitability by reducing dependence on bookmaker consensus embedded in odds, instead of trying to mimic it. That reframes the objective from "predict outcomes best" to "find mispriced outcomes where your beliefs differ from market prices in a useful way."

The second and third ideas are implementation-focused: use convolutional neural networks to leverage high-dimensional player and team information, and apply a portfolio-theoretic staking rule that explicitly balances expected return against variance across many simultaneous bets. In NBA experiments (2007-2014), these components are combined into a system that outperforms simpler baselines in cumulative profitability. The broader takeaway is that edge comes from the interaction between signal generation and disciplined risk allocation, not from model accuracy in isolation.

### Relevant Findings

- Lower dependence on bookmaker consensus could improve profitability in selected setups.
- Detectable inefficiencies existed, but they were small and required careful modeling.
- Including odds-based information in model design improved practical performance.

### How We Could Use This

Benchmark our probabilities against bookmaker implied probabilities and evaluate whether we are finding true edge over the market baseline. This supports a value-betting workflow rather than pure winner prediction.

## Paper 5: Application of the Kelly Criterion to Prediction Markets

**Authors:** Bernhard K. Meister
**Year:** 2024
**Link:** <https://arxiv.org/abs/2412.14144>

### Key Idea (extended)

This paper analyzes Kelly-style allocation in prediction markets through a log-utility lens, where the goal is maximizing long-run growth rather than short-term expected payoff. It starts from a realistic premise: market prices and participant beliefs are often different, and those belief estimates are noisy. To study this, the author uses a stylized biased-coin asset model and derives how growth changes when either the probability estimate is wrong or the chosen stake fraction deviates from the true Kelly-optimal amount.

A central analytical contribution is expressing these growth-rate penalties with information-theoretic structure (via Kullback-Leibler divergence), which makes estimation error costs explicit rather than heuristic. The paper also discusses payout-structure adjustments, reinforcing that both market design and bettor calibration determine realized performance. Practically, it supports cautious Kelly usage under uncertainty and motivates fractional/robust sizing when probability inputs are imperfect.

### Relevant Findings

- Even small probability misestimation can materially reduce long-run growth under full Kelly.
- Log-utility optimization can imply aggressive sizing when forecast confidence is high.
- Robust probability estimation is essential for sustainable bankroll growth.

### How We Could Use This

Run fractional-Kelly experiments and stress-test performance under probability error. This gives a practical safeguard against overbetting when model uncertainty is non-trivial.

## Paper 6: Makers and Takers: The Economics of the Kalshi Prediction Market

**Authors:** Constantin Burgi, Wanying Deng, Karl Whelan
**Year:** 2026
**Link:** <https://ideas.repec.org/p/gwc/wpaper/2026-001.html>

### Key Idea (2-3 sentences)

This paper provides transaction-level evidence on Kalshi market microstructure using more than 300,000 contracts. It studies how price accuracy evolves toward settlement and whether returns differ by trader role (Makers posting quotes vs Takers accepting quotes). The core question is whether quote-driven design and heterogeneous beliefs can explain favorite-longshot patterns in a regulated event-contract venue.

### Relevant Findings

- Kalshi prices become more accurate as contracts approach close, but pricing is not perfectly unbiased across the probability range.
- A clear favorite-longshot pattern appears: low-priced contracts underperform break-even after fees, while high-priced contracts perform relatively better.
- Maker-side and Taker-side returns differ systematically, consistent with a microstructure model where modest disagreement and probability overstatement generate the observed pattern.

### How We Could Use This

Use Maker/Taker role labels in our own microstructure analysis and evaluate edge separately by role, not just by contract. Also add probability-bucket diagnostics (favorite vs longshot) after fee-adjustment to avoid overstating alpha.

## Paper 7: Decomposing Crowd Wisdom: Domain-Specific Calibration Dynamics in Prediction Markets

**Authors:** Nam Anh Le
**Year:** 2026
**Link:** <https://arxiv.org/abs/2602.19520>

### Key Idea (2-3 sentences)

This paper studies calibration dynamics in Kalshi and Polymarket at very large scale (292 million trades across 327,000 binary contracts). Instead of treating miscalibration as one number, it decomposes calibration error into horizon, domain, interaction, and trade-size components. The goal is to explain when market prices should and should not be interpreted as literal probabilities.

### Relevant Findings

- A decomposition framework explains most calibration variance on Kalshi, with strong horizon and domain effects.
- Political markets show persistent underconfidence (prices compressed toward 50%) across both platforms.
- Trade-size effects differ across platforms, suggesting exchange-specific microstructure rather than a single universal calibration rule.

### How We Could Use This

Build calibration surfaces by domain and time-to-resolution rather than one global calibration curve. For model inputs, apply market-specific recalibration before converting contract prices into probabilities for execution and sizing.

## Paper 8: Exploring Decentralized Prediction Markets: Accuracy, Skill, and Bias on Polymarket

**Authors:** Felix Reichenbach, Martin Walther
**Year:** 2025
**Link:** <https://doi.org/10.2139/ssrn.5910522>

### Key Idea (2-3 sentences)

This paper evaluates forecast quality and participant skill on Polymarket using a large resolved-contract and transaction dataset. It tests both overall informational efficiency and whether trader-level behavior can predict which markets will resolve accurately. The paper frames decentralized prediction markets as both forecasting systems and skill-sorting environments.

### Relevant Findings

- The study analyzes large-scale Polymarket data (reported in the paper as over 800,000 resolved contracts and tens of millions of transactions).
- Polymarket prices are broadly informative, with evidence consistent with approximate market efficiency at aggregate level.
- Trader-level signals show modest but statistically meaningful ability to identify market-quality differences ex ante.

### How We Could Use This

Add trader-skill and market-quality features to our market selection layer (for example, confidence weighting by participant quality metrics). This can help prioritize contracts where price signals are more reliable.

## Paper 9: Goal Alpha: A Polymarket and EPL Study

**Authors:** Sahil Puri
**Year:** 2025
**Link:** <https://doi.org/10.2139/ssrn.5103168>

### Key Idea (2-3 sentences)

This paper tests strategy design on Polymarket sports contracts (EPL-focused) using a large panel of market observations over time. It estimates overreaction/underreaction behavior and evaluates both simple and model-informed trading rules. The objective is to determine whether practical alpha remains after transaction costs and platform fees.

### Relevant Findings

- The paper studies a large sports subset within a broader Polymarket panel over an extended period.
- Behaviorally motivated signal construction (reaction-to-news and mispricing proxies) can identify temporary dislocations.
- After realistic costs/fees, tested strategies are difficult to monetize consistently, emphasizing execution frictions.

### How We Could Use This

Treat behavioral mispricing signals as candidate features, but gate them with strict net-of-fee and slippage checks. This is useful for preventing false positives from gross-return backtests.

## Paper 10: Does time series momentum also exist outside traditional financial markets? Near-laboratory evidence from sports betting

**Authors:** Jonas Vandenbruaene, Marc De Ceuster, Jan Annaert
**Year:** 2023
**Link:** <https://doi.org/10.1016/j.socec.2023.102014>

### Key Idea (2-3 sentences)

This paper tests whether classic time-series momentum extends to sportsbook prices, using high-frequency in-play betting data as a near-laboratory setting. It compares trend-following payoffs with standard risk-based explanations. The central question is whether momentum in betting markets is genuine or just compensation for risk characteristics.

### Relevant Findings

- Momentum effects are present in sports betting prices: short-run winners tend to outperform short-run losers.
- The pattern is strongest at shorter horizons and weakens at longer formation windows.
- Standard variance/skewness style risk explanations do not fully account for the return differential, supporting an underreaction interpretation.

### How We Could Use This

Implement short-horizon momentum signals in live market modules, then test robustness net of fees and latency. Segment by sport and liquidity bucket to identify where momentum persists after execution costs.

## Paper 11: History-Dependent Risk Preferences: Evidence from Individual Choices and Implications for the Disposition Effect

**Authors:** Angie Andrikogiannopoulou, Filippos Papakonstantinou
**Year:** 2020
**Link:** <https://doi.org/10.1093/rfs/hhz127>

### Key Idea (2-3 sentences)

Using sports wagering transaction data, this paper estimates dynamic risk preferences in a prospect-theory framework. It asks whether bettor preferences are stable or path-dependent after prior wins/losses. It then links estimated preference dynamics to observed disposition-type behavior.

### Relevant Findings

- Estimated preferences in market data are consistent with prospect-theory ingredients: loss aversion and nonlinear probability weighting.
- Risk preferences are heterogeneous across individuals and depend on prior outcomes (history dependence).
- The estimated preference structure helps explain disposition-like behavior in repeated betting decisions.

### How We Could Use This

Incorporate path-dependent behavior features (recent gain/loss state, streak variables) into price-impact and flow models. This can improve timing around predictable behavioral demand imbalances.

## Paper 12: Estimating expected loss rates in betting markets: theory and evidence

**Authors:** Tadgh Hegarty, Karl Whelan
**Year:** 2025
**Link:** <https://doi.org/10.1080/00036846.2025.2507979>

### Key Idea (2-3 sentences)

This paper develops a framework for translating bookmaker pricing into expected bettor loss rates when margins vary across outcomes. It challenges the common shortcut of reading overround as the bettor loss rate. The paper combines theory and data to measure how pricing asymmetry distorts effective expected losses.

### Relevant Findings

- When bookmaker margins vary by implied probability, overround can materially understate true expected bettor losses.
- Loss rates differ across contract types/probability regions, not just across bookmakers.
- The framework provides a more accurate mapping from posted odds to expected net return after pricing distortions.

### How We Could Use This

Replace naive overround-based filtering with model-based expected-loss estimation before strategy selection. This improves no-vig conversion and helps avoid systematically negative-EV segments.

## Paper 13: Agreeing to Disagree: The Economics of Betting Exchanges

**Authors:** Karl Whelan
**Year:** 2025
**Link:** <https://ideas.repec.org/p/pra/mprapa/126351.html>

### Key Idea (2-3 sentences)

This paper models betting exchanges where participants hold different beliefs yet are correct on average, and then tests the model on transaction-level Betfair soccer trades. It distinguishes Makers (quote posters) from Takers (quote acceptors) to explain return asymmetries. The focus is how exchange microstructure and disagreement jointly shape realized losses/profits.

### Relevant Findings

- The model predicts higher returns for Makers than Takers and higher Taker loss rates for lower-probability accepted bets.
- Transaction-level evidence in pre-match and early in-play periods aligns closely with these predictions.
- Later in-play dynamics shift: longshots generate large losses even for liquidity providers, while accepting favorite-side quotes can become profitable.

### How We Could Use This

Add phase-of-game segmentation (pre-match, early in-play, late in-play) to strategy logic and evaluate role-specific execution rules. This can improve when to provide vs take liquidity on exchange-style markets.

# Biases in Sports Betting Markets

# 1. Favourite–Longshot Bias (FLB)

## Paper

**Authors:** Eric Snowberg, Justin Wolfers
**Year:** 2010
**Title:** *Explaining the Favorite-Longshot Bias: Is it Risk-Love or Misperceptions?*
**Source:** Journal of Political Economy / NBER Working Paper 15923
**Link:** <https://www.nber.org/papers/w15923>

---

## Key Idea

The **Favourite–Longshot Bias (FLB)** refers to a systematic pattern in betting markets where:

- **Longshots (low probability outcomes)** are overpriced
- **Favorites (high probability outcomes)** are slightly underpriced

This occurs because bettors **overestimate the probability of rare events**.

Example:

| True Probability | Bettor Perception |
|---|---|
| 5% | perceived as ~10% |

This behavioural bias is consistent with **Prospect Theory probability weighting**, where individuals overweight small probabilities.

---

## Methodology

The authors analyse a **large horse-racing dataset** covering multiple betting pools.

They test two competing explanations for FLB:

1. **Risk-Loving Preferences**
   - Bettors prefer high payoff bets.

2. **Probability Misperception**
   - Bettors incorrectly perceive probabilities.

Using demand models, they test which explanation better matches observed betting behaviour.

---

## Relevant Findings

Key results from the paper:

- Evidence strongly supports **probability misperception**, not risk-loving behaviour.
- Bettors systematically **overweight small probabilities**.
- Longshots therefore receive **excess betting demand**.
- This pushes bookmakers to **inflate prices on longshots**.

Empirically:

- **Longshots produce negative expected returns**
- **Favorites perform closer to break-even**

This produces the characteristic **favorite-longshot return curve**.

---

## Relevance to Our Project

If FLB exists in basketball betting markets, then:

- Longshot teams (large underdogs) may be **systematically overpriced**
- Favorites may be **slightly underpriced**

This creates predictable **probability calibration errors**.

---

## Implementation in Our Model

### Calibration Testing

Group games by **implied probability buckets**

Example buckets:

```text
0–20%
20–40%
40–60%
60–80%
80–100%
```

Then compare:

```text
Actual win frequency vs implied probability
```

Expected FLB pattern:

```text
Longshots win less often than implied
Favorites win slightly more often than implied
```

---

### Feature Engineering

Include variables such as:

- Spread magnitude
- Underdog indicator
- Moneyline probability

These allow the model to learn **systematic distortions in market pricing**.

---

# 2. Insider Information / Bookmaker Protection Bias

## Paper

**Author:** Hyun Song Shin
**Year:** 1993
**Title:** *Measuring the Incidence of Insider Trading in a Market for State-Contingent Claims*
**Source:** The Economic Journal
**Link:** <https://academic.oup.com/ej/article/103/420/1141/5157258>

---

## Key Idea

Bookmakers may assume that **some bettors possess superior information**.

To protect against these informed bettors, bookmakers adjust odds.

Therefore:

```text
Observed betting odds ≠ true probabilities + bookmaker margin
```

Instead, odds incorporate a correction for **asymmetric information risk**.

---

## Methodology

Shin develops a structural model where:

- A fraction of bettors are **informed traders**
- The rest are **uninformed bettors**

The model estimates:

```text
z = proportion of informed bettors
```

Using observed odds and market spreads, Shin derives a method for estimating the **true probability distribution**.

---

## Relevant Findings

The model shows that:

- Betting odds reflect **information asymmetry**
- Markets price in protection against **informed bettors**
- Standard normalization of odds produces **biased probability estimates**

Shin’s probability extraction method produces **more accurate probability estimates**.

---

## Relevance to Our Project

Most models convert bookmaker odds using **naive normalization**:

```text
p_i = (1 / odds_i) / Σ(1 / odds_i)
```

However, this ignores insider risk.

Using naive probabilities may lead to:

- incorrect calibration
- biased training targets

---

## Implementation in Our Model

We should compute **Shin-implied probabilities**.

Process:

1. Input bookmaker odds
2. Estimate insider parameter **z**
3. Derive corrected probabilities

These probabilities should be used for:

- model calibration
- probability comparisons
- detecting mispricing

This produces a more accurate baseline for **market probability estimates**.

---

# 3. Sentiment / Popular Team Bias

## Paper

**Authors:** Timothy Feddersen, Devin Pope, and others
**Year:** 2013
**Title:** *Sentiment Bias in National Basketball Association Betting*
**Link:** <https://findresearcher.sdu.dk/ws/files/153177361/Sentiment_bias_in_national_basketball_association_betting.pdf>

---

## Key Idea

Bettors often prefer betting on **popular teams**.

Examples include:

- historically successful teams
- teams with star players
- teams from large media markets

This leads sportsbooks to **shade lines against popular teams**, because they know the public will bet them regardless.

---

## Methodology

The paper analyses over:

```text
33,000 NBA games
```

The authors construct measures of **team popularity**, including:

- attendance levels
- fan engagement proxies
- team prestige indicators

They then test whether betting lines are **systematically biased** when popular teams are involved.

---

## Relevant Findings

The study finds that:

- Popular teams attract **disproportionate betting demand**
- Sportsbooks respond by **worsening the betting price** on those teams
- This leads to **inflated spreads or odds**

Example:

```text
True spread: Lakers -4
Market spread: Lakers -5
```

This allows bookmakers to profit from **sentiment-driven betting**.

---

## Relevance to Our Project

Popular teams may be **overbet**, causing:

- spreads to be inflated
- implied probabilities to be biased

This may create value opportunities **betting against heavily supported teams**.

---

## Implementation in Our Model

Introduce **team popularity feature variables**.

Possible proxies include:

- Social media following
- Market size
- Number of All-Star players
- Historical team success
- National TV appearances

Testing approach:

1. Compute model prediction vs market spread
2. Condition results on **team popularity indicators**

If sentiment bias exists, we should observe **systematic pricing distortions**.

---

# 4. Recency Bias

## Paper

**Author:** Gregory Durand
**Year:** 2021
**Title:** *Recency Bias in Sports Betting Markets*
**Source:** Journal of Behavioral and Experimental Finance
**Link:** <https://www.sciencedirect.com/science/article/pii/S2214635021000666>

---

## Key Idea

Bettors tend to overweight **recent performance** when forming expectations.

Examples:

- Teams on winning streaks become **overvalued**
- Teams on losing streaks become **undervalued**

However, sports performance often **regresses toward long-term averages**.

---

## Methodology

The study analyses betting markets to determine whether:

- recent game outcomes
- winning streaks
- short-term performance indicators

affect betting prices more than they should.

---

## Relevant Findings

The results suggest that betting markets:

- **overreact to recent performance**
- adjust prices excessively after winning or losing streaks

This creates **temporary mispricing**.

---

## Relevance to Our Project

Market odds may overweight:

- recent wins
- recent point differentials
- narrative-driven performance trends

This means market prices may diverge from **true team strength**.

---

## Implementation in Our Model

Include variables measuring **recent form**, such as:

```text
last_5_games_win_percentage
recent_ATS_performance
recent_point_differential
```

Then test whether:

```text
market spreads overweight recent performance
```

If recency bias exists, our model can incorporate **mean-reversion adjustments**.

---
