## Paper 1: Machine learning for sports betting: should model selection be based on accuracy or calibration?

**Authors:** Conor Walsh, Alok Joshi  
**Year:** 2024  
**Link:** https://arxiv.org/abs/2303.06021

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
**Link:** https://ace.ewapub.com/article/view/20626

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
**Link:** https://arxiv.org/abs/2307.13807

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
**Link:** https://doi.org/10.1016/j.ijforecast.2019.01.001

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
**Link:** https://arxiv.org/abs/2412.14144

### Key Idea (extended)
This paper analyzes Kelly-style allocation in prediction markets through a log-utility lens, where the goal is maximizing long-run growth rather than short-term expected payoff. It starts from a realistic premise: market prices and participant beliefs are often different, and those belief estimates are noisy. To study this, the author uses a stylized biased-coin asset model and derives how growth changes when either the probability estimate is wrong or the chosen stake fraction deviates from the true Kelly-optimal amount.

A central analytical contribution is expressing these growth-rate penalties with information-theoretic structure (via Kullback-Leibler divergence), which makes estimation error costs explicit rather than heuristic. The paper also discusses payout-structure adjustments, reinforcing that both market design and bettor calibration determine realized performance. Practically, it supports cautious Kelly usage under uncertainty and motivates fractional/robust sizing when probability inputs are imperfect.

### Relevant Findings
- Even small probability misestimation can materially reduce long-run growth under full Kelly.
- Log-utility optimization can imply aggressive sizing when forecast confidence is high.
- Robust probability estimation is essential for sustainable bankroll growth.

### How We Could Use This
Run fractional-Kelly experiments and stress-test performance under probability error. This gives a practical safeguard against overbetting when model uncertainty is non-trivial.
