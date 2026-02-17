## Paper 1: Machine learning for sports betting: should model selection be based on accuracy or calibration?

**Authors:** Conor Walsh, Alok Joshi  
**Year:** 2024  
**Link:** https://arxiv.org/abs/2303.06021

### Key Idea (2-3 sentences)
This paper tests whether sports betting models should be selected using predictive accuracy or probability calibration. The authors show that accuracy alone does not reliably translate into betting profit. In NBA betting simulations, better-calibrated probability estimates produced stronger outcomes for decision-making and staking.

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

### Key Idea (2-3 sentences)
This paper applies multiple machine learning models to European football match prediction and compares both predictive quality and betting profitability. It evaluates models such as LightGBM and AdaBoost and then runs betting simulations using model outputs. The work explicitly links model performance to financial outcomes.

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

### Key Idea (2-3 sentences)
This paper combines neural-network match forecasts with portfolio construction using modern portfolio theory and Kelly-style log-utility objectives. Instead of sizing each wager independently, it allocates capital across a basket of bets. The framework integrates prediction quality with bankroll growth optimization.

### Relevant Findings
- Neural-network forecasts combined with Kelly-informed portfolio sizing showed strong simulated bankroll growth.
- Diversifying across multiple bets reduced risk versus isolated single-bet sizing.
- Capital allocation strategy was a major driver of long-run outcomes, alongside model quality.

### How We Could Use This
Extend our workflow from single-bet expected-value checks to portfolio-level optimization across opportunities in the same slate. This is directly relevant if we want correlated, risk-aware Kelly sizing.

## Paper 4: Exploiting sports-betting markets using machine learning

**Authors:** Franc J.G.M. Klaassen, Jan R. Magnus  
**Year:** 2019  
**Link:** https://doi.org/10.1016/j.ijforecast.2019.01.001

### Key Idea (2-3 sentences)
This paper studies how machine learning can exploit subtle inefficiencies in betting markets rather than just maximizing forecast accuracy. It focuses on identifying cases where bookmaker prices diverge from estimated true probabilities. The core framing is market-relative edge detection.

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

### Key Idea (2-3 sentences)
This paper examines Kelly betting in prediction-market settings with uncertain or misspecified probabilities. It formalizes how estimation error affects long-run growth under log-utility maximization. The analysis highlights the fragility of full Kelly when confidence is overstated.

### Relevant Findings
- Even small probability misestimation can materially reduce long-run growth under full Kelly.
- Log-utility optimization can imply aggressive sizing when forecast confidence is high.
- Robust probability estimation is essential for sustainable bankroll growth.

### How We Could Use This
Run fractional-Kelly experiments and stress-test performance under probability error. This gives a practical safeguard against overbetting when model uncertainty is non-trivial.
