<!-- markdownlint-disable MD024 -->
# Paper Summaries

**Researcher:** Miran
**Week 1 Goal:** 3-5 papers on sports betting / prediction markets

---

## Paper 1: Beating the House: Identifying Inefficiencies in Sports Betting Markets

**Authors:** Sathya Ramesh, Ragib Mostofa, Marco Bornstein, John Dobelman
**Year:** 2019
**Link:** <https://arxiv.org/abs/1910.08858>

### Key Idea (2-3 sentences)

This paper argues that sports betting markets are not fully efficient and demonstrates a betting algorithm that achieves above-market returns across multiple leagues. The authors build a non-parametric win probability model on a novel dataset of bets to identify positive expected value opportunities.

### Relevant Findings

- A non-parametric probability model can surface mispriced bets across NFL, NBA, NCAAF, NCAAB, and WNBA markets.
- The proposed strategy yields above-market returns, suggesting exploitable inefficiencies.
- The work highlights growing relevance of betting market research after U.S. legalization shifts.

### How We Could Use This

We can use a similar win-probability modeling approach to screen for value bets and benchmark our models against market lines. The multi-league angle also informs feature reuse across sports data sources.

---

## Paper 2: Prediction Markets as Bayesian Inverse Problems: Uncertainty Quantification, Identifiability, and Information Gain from Price-Volume Histories under Latent Types

**Authors:** Juan Pablo Madrigal-Cianci, Camilo Monsalve Maya, Lachlan Breakey
**Year:** 2026
**Link:** <https://arxiv.org/abs/2601.18815>

### Key Idea (2-3 sentences)

This paper models prediction markets as Bayesian inverse problems, inferring the binary outcome from price and volume histories. It proposes a latent-type mixture model in log-odds space and derives uncertainty quantification and identifiability conditions for market informativeness.

### Relevant Findings

- A mechanism-agnostic observation model links price increments and volume via latent trader types.
- Identifiability depends on KL separation between outcome-conditional increment laws.
- The framework yields diagnostics for when market histories are informative versus ill-posed.

### How We Could Use This

We can treat Polymarket price and volume series as noisy signals and quantify when they are reliable inputs. The identifiability checks can guide when to trust market prices in our models.

---

## Paper 3: Semantic Non-Fungibility and Violations of the Law of One Price in Prediction Markets

**Authors:** Jonas Gebele, Florian Matthes
**Year:** 2026
**Link:** <https://arxiv.org/abs/2601.01706>

### Key Idea (2-3 sentences)

This paper shows that prediction markets often list economically identical events across platforms but lack a shared notion of event identity. The authors build a semantic alignment framework and a cross-platform dataset to quantify persistent price deviations that enable arbitrage.

### Relevant Findings

- About 6% of events are concurrently listed across platforms in the aligned dataset.
- Semantically equivalent markets show persistent price deviations on the order of 2-4%.
- Structural frictions, not just information disagreement, drive cross-platform arbitrage.

### How We Could Use This

We can incorporate event-identity matching when comparing Polymarket to sportsbook lines or other venues. This helps detect arbitrage opportunities driven by platform fragmentation rather than model error.

---

## Paper 4: Machine Learning in Sports: A Case Study on Using Explainable Models for Predicting Outcomes of Volleyball Matches

**Authors:** Abhinav Lalwani, Aman Saraiya, Apoorv Singh, Aditya Jain, Tirtharaj Dash
**Year:** 2022
**Link:** <https://arxiv.org/abs/2206.09258>

### Key Idea (2-3 sentences)

This paper applies explainable ML to predict volleyball match outcomes and compares interpretable models with black-box models. It uses rule-based models and logistic regression for global interpretability and SVM/DNN with SHAP/ProtoDash for post-hoc explanations.

### Relevant Findings

- Interpretable rule-based models can deliver competitive performance while improving transparency.
- Post-hoc explanation tools like SHAP help attribute feature contributions in black-box models.
- The two-phase approach balances predictive accuracy with explainability requirements.

### How We Could Use This

We can adopt an explainability-first baseline for sports prediction models and then layer on more complex models with SHAP. This supports debugging and trust in model-driven betting decisions.

---

## Paper 5: A Resource Theory of Gambling

**Authors:** Maite Arcos, Renato Renner, Jonathan Oppenheim
**Year:** 2025
**Link:** <https://arxiv.org/abs/2510.08418>

### Key Idea (2-3 sentences)

This paper reinterprets the Kelly criterion as a resource theory of information in gambling, extending it to finite and single-shot betting regimes. It derives optimal strategies for maximizing target success probability and connects them to information-theoretic quantities.

### Relevant Findings

- Kelly can be extended beyond the infinite-bet limit to finite and one-shot settings.
- Optimal strategies reveal a risk-reward trade-off tied to divergences between true and offered odds.
- The framework links gambling strategy to hypothesis testing and expected utility principles.

### How We Could Use This

We can justify fractional or constrained Kelly sizing when bet horizons are short and probabilities are noisy. The information-theoretic framing can guide risk controls for our backtests.

---
