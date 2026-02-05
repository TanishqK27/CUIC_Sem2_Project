# Research Ideas

This folder contains research ideas and proposals for the CUIC Quant Fund project.

---

## How to Submit an Idea

Add your idea below using this template:

```markdown
## [IDEA] Your Idea Title

**Submitted by:** Your Name
**Date:** YYYY-MM-DD
**Status:** Proposed / In Progress / Completed / Abandoned

### Description
Brief description of the research idea (2-3 sentences).

### Hypothesis
What do you expect to find? State in a falsifiable form.

### Data Required
- Data source 1
- Data source 2

### Methodology
Brief outline of the approach.

### Expected Outcome
What would success look like?

### Priority
Low / Medium / High

### Notes
Any additional context or references.
```

---

## Active Ideas

### [IDEA] Polymarket Market Efficiency Analysis

**Submitted by:** Team
**Date:** 2025-02-01
**Status:** Proposed

#### Description

Analyze the efficiency of Polymarket prices by comparing market probabilities to actual outcomes. Test whether prices systematically deviate from true probabilities.

#### Hypothesis

Polymarket prices are informationally efficient in the short term but may exhibit predictable biases in specific market types (e.g., political vs. sports).

#### Data Required

- Historical Polymarket prices and outcomes
- Market resolution data
- Trading volume data

#### Methodology

1. Collect historical market data
2. Compare implied probabilities to actual outcomes
3. Calculate calibration curves
4. Test for systematic biases by category

#### Expected Outcome

Identification of market types or conditions where alpha opportunities exist.

#### Priority

High

---

### [IDEA] Cross-Platform Arbitrage Detection

**Submitted by:** Team
**Date:** 2025-02-01
**Status:** Proposed

#### Description

Build a system to detect arbitrage opportunities between Polymarket and Kalshi for overlapping event contracts.

#### Hypothesis

Price discrepancies exist between platforms due to:

- Different user bases
- Regulatory differences
- Liquidity variations

#### Data Required

- Real-time prices from Polymarket
- Real-time prices from Kalshi
- Event mapping between platforms

#### Methodology

1. Identify matching events across platforms
2. Monitor price differentials in real-time
3. Calculate arbitrage opportunity after transaction costs
4. Track persistence and profitability

#### Expected Outcome

System that identifies and alerts on arbitrage opportunities with >1% expected profit.

#### Priority

High

---

### [IDEA] Sports Betting Mean Reversion

**Submitted by:** Team
**Date:** 2025-02-01
**Status:** Proposed

#### Description

Test whether sports betting lines exhibit mean reversion after large moves, particularly around injury news and lineup changes.

#### Hypothesis

Large line movements often overshoot fair value, creating mean reversion opportunities within 24-48 hours.

#### Data Required

- Historical odds from The Odds API
- News/injury data
- Game outcomes

#### Methodology

1. Identify large line movements (>2 points in spreads)
2. Track subsequent line evolution
3. Analyze profitability of fading large moves
4. Control for information content

#### Expected Outcome

Strategy with positive expected value for fading overreactions.

#### Priority

Medium

---

### [IDEA] Kelly Criterion Optimization for Multiple Markets

**Submitted by:** Team
**Date:** 2025-02-01
**Status:** Proposed

#### Description

Develop an optimized Kelly Criterion implementation for simultaneous positions across multiple correlated prediction markets.

#### Hypothesis

Standard Kelly criterion is suboptimal for portfolios of correlated bets. An optimized approach accounting for correlations can improve risk-adjusted returns.

#### Data Required

- Historical returns from prediction market positions
- Correlation structure between markets

#### Methodology

1. Estimate correlation matrix for market returns
2. Implement multivariate Kelly optimization
3. Backtest against naive Kelly allocation
4. Analyze drawdown and Sharpe improvements

#### Expected Outcome

Improved position sizing algorithm for multi-market portfolios.

#### Priority

Medium

---

## Completed Ideas

*No completed ideas yet.*

---

## Abandoned Ideas

*No abandoned ideas yet.*

---

## Idea Evaluation Criteria

When prioritizing ideas, consider:

1. **Feasibility**: Do we have the data and skills?
2. **Alpha Potential**: Expected profit if successful?
3. **Risk**: What could go wrong?
4. **Scalability**: Can it handle larger capital?
5. **Learning Value**: Will it teach us something useful?

---

## Resources

- [Research Methodology Guide](../../docs/research/methodology.md)
- [Platform Documentation](../../docs/platforms/)
- [Paper References](../papers/README.md)
