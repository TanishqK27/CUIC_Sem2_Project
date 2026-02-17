# NBA Prediction Model Roadmap

**Goal:** Build a MambaNet-style neural network to predict:
1. Win probability
2. Confidence intervals for final scores

**Primary use:** Research → Pre-game betting → (future) Live betting

---

## Data Available

- **Table:** `combined_player_stats` in Railway PostgreSQL
- **Rows:** 136,965 (player-game level)
- **Columns:** 428
- **Coverage:** ~5,274 games, ~1,025 players, seasons 2021-22 through 2025-26

### Key Feature Groups
| Category | Columns | Purpose |
|----------|---------|---------|
| Pregame player avgs | 33 | `season_avg_pts`, `last5_avg_pts`, etc. |
| Pregame team stats | 38 | `team_pre_conf_rank`, `team_pre_days_rest`, etc. |
| Availability | 3 | `played`, `dnp_reason`, `dnp_category` |
| Boxscore (outcome) | 20 | `pts`, `reb`, `ast` - what actually happened |
| Team boxscore | 20 | `team_pts` - final score |

---

## Phases

### Phase 0: Data Understanding (1-2 weeks)
- [ ] EDA on `combined_player_stats`
- [ ] Check distributions of key features
- [ ] Identify missing values and how to handle them
- [ ] Correlation analysis (which features predict wins/scores?)
- [ ] Create game-level dataset (one row per game with both teams)

### Phase 1: Baseline Models (2-3 weeks)
- [ ] Build data pipeline: DB → features → train/test split
- [ ] Train XGBoost/LightGBM for win probability
- [ ] Train XGBoost/LightGBM for score prediction
- [ ] Establish baseline metrics (accuracy, log loss, MAE)
- [ ] Feature importance analysis

### Phase 2: Simple Neural Network (2-3 weeks)
- [ ] Set up PyTorch with MPS (Apple Silicon)
- [ ] Build feedforward network for win probability
- [ ] Learn training loop mechanics
- [ ] Add score prediction head
- [ ] Compare to XGBoost baseline

### Phase 3: Sequence Model (3-4 weeks)
- [ ] Restructure data as sequences (player/team history)
- [ ] Implement LSTM or Transformer
- [ ] Incorporate temporal patterns
- [ ] Experiment with attention mechanisms

### Phase 4: MambaNet Architecture (4+ weeks)
- [ ] Implement Mamba SSM layer
- [ ] Build hybrid architecture (FINs + CNN + Mamba)
- [ ] Add probabilistic output for confidence intervals
- [ ] Quantile regression or mixture density network
- [ ] Final evaluation and tuning

---

## Resources

- [MambaNet Paper](https://link.springer.com/article/10.1007/s42979-024-02977-0)
- [Mamba Architecture](https://arxiv.org/abs/2312.00752)
- [Mamba GitHub](https://github.com/state-spaces/mamba)
- [Visual Guide to Mamba](https://www.maartengrootendorst.com/blog/mamba/)

---

## Compute

- **Local:** Apple M5, 16GB unified memory, Metal 4
- **Backup:** Google Colab (check if Pro available via university)

---

## Database Connection

```python
import psycopg2
import pandas as pd

DB_URL = 'postgresql://postgres:LNpAVdwSgYTvbKNgfipNctUPcChJoMJU@switchyard.proxy.rlwy.net:44650/railway'

def query(sql):
    with psycopg2.connect(DB_URL, connect_timeout=30) as conn:
        return pd.read_sql(sql, conn)
```
