# CUIC Quant: 1-Month Sprint Plan

**Start Date:** February 5, 2026
**End Date:** March 5, 2026
**Goal:** Presentation-ready notebook with full pipeline: Data → Strategy → Backtest → Results

---

## Critical Rules

> ⚠️ **Infrastructure before research. No exceptions.**
>
> We've had issues with people wanting to skip to the "fun" model/research work before the data pipelines are built. This doesn't work. If your data pipeline is broken, your model is worthless.
>
> **You cannot work on models/research until your infrastructure task is complete and validated.**

> 📋 **Weekly accountability requirements:**
>
> 1. **Update your LOG.md** — Every week before Thursday meeting
> 2. **Update your TASKS.md** — Mark progress, blockers, completed items
> 3. **Prepare 5-min presentation** — Each team presents progress at Thursday meeting
>
> No updates = no voice in the meeting.

---

## Deliverable Standards

Every deliverable must meet these criteria before it's considered "done":

| Requirement | Description |
|-------------|-------------|
| **Working code** | Runs without errors, handles edge cases |
| **Documentation** | Clear docstrings, README or markdown explanation |
| **Example notebook** | Jupyter notebook showing how to use it |
| **Validated** | Tested with real data, reviewed by at least one other person |

**If it doesn't have documentation and an example notebook, it's not finished.**

---

## Team Assignments

| Workstream | Members | Lead |
|------------|---------|------|
| **Data Team** | Alfie, Max, Miran | Dietrich (advisor) |
| **Backtester Team** | James, Ben, Vansheeka | James |
| **Models Team** | Mya, Isameel | Mya |
| **Oversight/Support** | Tan, Andrii, Dietrich | Tan |

**Notes:**
- Weaker members paired with stronger ones
- Dietrich advises Data Team (owns Railway DB)
- Tan and Andrii float between teams to unblock issues
- Each team lead is responsible for their team's Thursday presentation

---

## Weekly Schedule

| Week | Dates | Thursday Meeting | Primary Focus |
|------|-------|------------------|---------------|
| **1** | Feb 5-11 | Feb 12 | Data infrastructure |
| **2** | Feb 12-18 | Feb 19 | EDA + Backtester skeleton |
| **3** | Feb 19-25 | Feb 26 | Models implemented |
| **4** | Feb 26-Mar 4 | **Mar 5 (Final)** | Integration + presentation-ready notebook |

---

## Thursday Meeting Format

| Segment | Description |
|---------|-------------|
| Data Team | Demo deliverables, show working queries/data |
| Backtester Team | Demo deliverables, show notebook running |
| Models Team | Demo deliverables, show predictions/results |
| Next week assignments | Assign specific tasks for next week |

**Rules:**
- Thursdays are for **demos and deliverables**, not questions and problem-solving
- Come prepared — no "I didn't have time"
- Demo working code, not slides

---

## Parallel Workstreams

Three teams work in parallel, converging in Week 4:

```
DATA TEAM              BACKTESTER TEAM         MODELS TEAM
    │                        │                       │
    ▼                        ▼                       ▼
Week 1: Build            Week 1: Design          Week 1: Research only
Week 2: Validate         Week 2: Build           Week 2: Prototype
Week 3: Support          Week 3: Integrate       Week 3: Build
Week 4: ──────────────── ALL CONVERGE ────────────────────
```

---

## Week 1: Data Infrastructure (Feb 5-11)

**Objective:** All data sources flowing into Railway PostgreSQL database.

### Data Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| OddsHarvester pipeline | Alfie, Max | Historical NBA odds in Railway DB, documented schema, example query notebook |
| NBA Stats pipeline | Miran | Player/team stats in Railway DB via `nba_api`, documented schema, example query notebook |
| Data validation report | Team | Markdown doc confirming row counts, date ranges, data quality |

### Backtester Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Backtester design doc | James | Markdown spec: interfaces, data flow, strategy format |
| Framework research | Ben, Vansheeka | Summary of `sports-betting` library and patterns we'll use |

### Models Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Literature review | Mya | Markdown doc: Markov chains, XGBoost for sports betting, with paper links |
| Feature wishlist | Isameel | List of features models will need (price gaps, NBA stats, etc.) |

### Thursday Meeting (Feb 12)
- [ ] Data Team: Demo query showing OddsHarvester + NBA data in Railway DB
- [ ] Backtester Team: Present design document
- [ ] Models Team: Present research notes and feature wishlist

---

## Week 2: EDA + Backtester Skeleton (Feb 12-18)

**Objective:** Understand the data, have a working backtester notebook.

### Data Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| EDA notebook | Alfie, Max | Notebook analyzing Polymarket vs Sportsbook gaps, visualizations, insights |
| Feature engineering | Miran | Derived columns added to DB (gap %, rolling averages, etc.), documented |

### Backtester Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Backtester notebook v1 | James, Ben | Core loop working: iterate dates, apply strategy, track P&L |
| Metrics module | Vansheeka | Functions for win rate, ROI, Sharpe ratio, max drawdown |
| Dummy strategy test | Team | Backtester validated with simple "always bet home" strategy |

### Models Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Baseline model | Mya | Logistic regression on Polymarket data, notebook with results |
| Model interface spec | Isameel | Document defining Input → Output format for all models |

### Thursday Meeting (Feb 19)
- [ ] Data Team: Demo EDA notebook with key insights
- [ ] Backtester Team: Demo backtester running dummy strategy
- [ ] Models Team: Demo baseline model producing predictions

---

## Week 3: Models Implemented (Feb 19-25)

**Objective:** Multiple models producing signals, integrated with backtester.

### Data Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Query optimization | Team | Common queries documented and optimized |
| Additional data | As needed | Fill any gaps other teams identify |

### Backtester Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Strategy integration | James | Models plugged into backtester, producing results |
| Comparison framework | Ben | Run multiple strategies side-by-side |
| Visualization | Vansheeka | P&L curves, drawdown charts, comparison tables |

### Models Team Deliverables

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Markov Chain model | Mya | State transition model on price gaps, notebook with backtest results |
| XGBoost model | Mya, Isameel | ML model using combined features, notebook with backtest results |

### Thursday Meeting (Feb 26)
- [ ] Data Team: Confirm all data needs are met
- [ ] Backtester Team: Demo comparing multiple strategies
- [ ] Models Team: Demo each model's performance metrics

---

## Week 4: Integration + Polish (Feb 26-Mar 4)

**Objective:** Single presentation-ready notebook demonstrating the full pipeline.

### All Teams Converge

| Deliverable | Owner | Definition of Done |
|-------------|-------|-------------------|
| Master notebook | All | One notebook running complete workflow |
| Clean visualizations | Backtester Team | Charts suitable for presentation |
| Documentation | All | Clear markdown cells explaining each step |
| Error handling | All | Graceful handling of missing data, edge cases |
| Performance summary | Models Team | Which strategy won? By how much? |

### Master Notebook Structure

```
1. Introduction & Setup
   - What this notebook does
   - Required dependencies

2. Load Data
   - Connect to Railway DB
   - Pull Polymarket, Sportsbook, NBA Stats

3. Feature Engineering
   - Create derived features
   - Prepare model inputs

4. Select Strategy
   - Parameter: choose Markov, XGBoost, or rules-based
   - Parameter: date range, bet sizing

5. Run Backtest
   - Execute strategy over historical data
   - Track all trades and P&L

6. Results & Visualization
   - P&L curve
   - Key metrics (Sharpe, ROI, win rate)
   - Comparison charts

7. Conclusions
   - What worked
   - Recommendations
   - Next steps
```

### Final Meeting (Mar 5)
- [ ] Full demo of master notebook
- [ ] Present findings and strategy recommendations
- [ ] Discuss next iteration improvements

---

## End State

A Jupyter notebook where you can:
1. Select a strategy (Markov, XGBoost, simple rules-based)
2. Set date range and parameters
3. Run cells
4. See visualized P&L, metrics, and comparison charts

**Presentation-ready for stakeholders.**

---

## Individual Accountability

### Weekly Requirements (Every Week)

| Task | Where | Deadline |
|------|-------|----------|
| Update your LOG.md | `team/<your-name>/LOG.md` | Wednesday night |
| Update your TASKS.md | `team/<your-name>/TASKS.md` | Wednesday night |
| Prepare team demo | Working code/notebook | Thursday meeting |

### When You're Stuck

**Do NOT wait for Thursday meetings to ask questions.** Try these first, in order:

1. **Google / Stack Overflow / ChatGPT** — Most technical issues are solved
2. **Ask your team lead** — They should know or can point you to someone
3. **Ask in team chat** — Someone else may have hit the same issue
4. **Ask Andrii or Dietrich** — For architecture/data questions
5. **Ask Tan** — Only after exhausting the above

If you're blocked for more than a day without asking for help, that's on you.

---

## Resources

### Data Collection
- [OddsHarvester](https://github.com/jordantete/OddsHarvester) — Sports odds scraper
- [nba_api](https://github.com/swar/nba_api) — NBA.com stats API

### Backtesting
- [sports-betting](https://github.com/georgedouzas/sports-betting) — Backtesting framework reference

### Models
- [NBA-ML-Sports-Betting](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting) — XGBoost reference
- [NFL Markov Predictor](https://github.com/flancast90/NFL_Markov_Predictor) — Markov chain reference

### Existing Infrastructure
- Database Guide: `docs/reference/database-guide.md`
- Connection Guide: `docs/guides/connecting-to-database.md`
- Data Exploration: `tools/polymarket_data_exploration.ipynb`

---

## Questions?

See "When You're Stuck" above. Exhaust all other options before escalating to Tan.
