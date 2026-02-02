# CUIC Quant Fund

**Cardiff University Investment Club - Quantitative Research Project**

A collaborative quantitative research initiative focused on sports betting and prediction markets (Polymarket, Kalshi) for alpha generation through arbitrage, mean reversion, and systematic strategies.

---

## Overview

This project explores quantitative approaches to prediction markets and sports betting, combining academic research with practical implementation. Our focus areas include:

- **Prediction Markets**: Polymarket (decentralized) and Kalshi (regulated)
- **Sports Betting**: Odds analysis and arbitrage opportunities
- **Quantitative Strategies**: Kelly criterion, mean reversion, and systematic approaches

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/CUIC/CUIC_Sem2_Project.git
cd CUIC_Sem2_Project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .[all]

# Set up pre-commit hooks
pre-commit install

# Copy environment template
cp configs/example.env .env
# Edit .env with your API keys
```

### Verify Installation

```bash
# Run tests
pytest tests/ -v

# Check code quality
pre-commit run --all-files

# Start Jupyter Lab
jupyter lab
```

---

## Project Structure

```
CUIC_Sem2_Project/
├── src/cuic_quant/        # Main Python package
│   ├── data/              # API clients (Polymarket, Kalshi, Odds API)
│   ├── models/            # ML and statistical models
│   ├── strategies/        # Trading/betting strategies
│   ├── backtest/          # Backtesting framework
│   └── utils/             # Utility functions
│
├── research/
│   ├── notebooks/         # Jupyter notebooks by category
│   ├── ideas/             # Research idea submissions
│   └── papers/            # Academic references
│
├── team/                  # Team member workspaces
│   ├── PROJECT_LOG.md     # Aggregated project log
│   ├── PROJECT_TASKS.md   # Project-wide tasks
│   └── <name>/            # Individual member folders
│
├── docs/                  # Documentation
│   ├── platforms/         # Platform guides
│   ├── setup/             # Setup instructions
│   └── research/          # Research methodology
│
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── configs/               # Configuration files
└── data/                  # Data storage (gitignored)
```

---

## Team

| Member    | Role / Focus Area |
|-----------|-------------------|
| Tan       | Lead / Infrastructure |
| Andrii    | TBD |
| Dietrich  | TBD |
| Ben       | TBD |
| Alfie     | TBD |
| Max       | TBD |
| Miran     | TBD |
| Mya       | TBD |
| Isameel   | TBD |
| Vansheeka | TBD |

---

## Documentation

### Getting Started
- [Environment Setup](docs/setup/environment-setup.md) - Python, dependencies, IDE
- [Claude Code Guide](docs/setup/claude-code-guide.md) - AI assistant setup
- [API Keys Setup](docs/setup/api-keys.md) - Configuring API access

### Platforms
- [Polymarket Guide](docs/platforms/polymarket.md) - Decentralized prediction market
- [Kalshi Guide](docs/platforms/kalshi.md) - Regulated event contracts
- [Sports Betting Basics](docs/platforms/sports-betting-basics.md) - Odds and fundamentals

### Research
- [Methodology](docs/research/methodology.md) - Research workflow and standards

### Contributing
- [Contribution Guidelines](CONTRIBUTING.md) - How to contribute

---

## Key Features

### API Clients
Ready-to-use clients for major platforms:

```python
from cuic_quant.data import PolymarketClient, KalshiClient, OddsAPIClient

# Fetch prediction market data
polymarket = PolymarketClient()
markets = polymarket.get_markets()

# Get sports odds
odds_client = OddsAPIClient(api_key="your_key")
nba_odds = odds_client.get_odds(sport="basketball_nba")
```

### Strategies
Implemented quantitative strategies:

```python
from cuic_quant.strategies import kelly_criterion, find_arbitrage

# Calculate optimal bet size
fraction = kelly_criterion.calculate_kelly_fraction(
    win_probability=0.55,
    odds=2.0
)

# Find arbitrage opportunities
opportunities = find_arbitrage(bookmaker_odds)
```

---

## Development

### Code Quality

```bash
# Format code
ruff format src/

# Lint code
ruff check src/ --fix

# Type check
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/cuic_quant

# Run specific test file
pytest tests/test_strategies.py -v
```

### Adding Research

1. Create a notebook from template:
   ```
   /research-template polymarket market-efficiency
   ```

2. Document your work in the notebook's markdown cells

3. Update your personal log:
   ```
   /update-log <your-name> Completed market efficiency analysis
   ```

---

## Development Workflow

### Daily Checklist

1. **Pull latest:** `git pull origin main`
2. **Create branch:** `git checkout -b <name>/<feature>`
3. **Do work, run tests:** `pytest tests/ -v`
4. **Update your log:** `/update-log <name> <summary>`
5. **Commit & push:** `git add . && git commit -m "message"`
6. **Create PR** when ready for review

### Slash Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/update-log` | Update your work log | `/update-log tan Fixed API bug` |
| `/research-template` | Create research notebook | `/research-template polymarket price-discovery` |
| `/weekly-standup` | Generate team summary | `/weekly-standup` |

See [Skills Reference](docs/setup/skills-reference.md) for detailed documentation.

### Task Management

We use markdown files for task tracking:

- **[PROJECT_TASKS.md](team/PROJECT_TASKS.md)** - Project milestones and shared tasks
- **`team/<name>/TASKS.md`** - Individual to-do lists

### Weekly Standup

Run `/weekly-standup` to generate a summary from all team logs.

---

## Resources

### External Links
- [Polymarket Documentation](https://docs.polymarket.com/)
- [Kalshi API Documentation](https://docs.kalshi.com/)
- [The Odds API](https://the-odds-api.com/)

### Related Projects
- [georgedouzas/sports-betting](https://github.com/georgedouzas/sports-betting)
- [kyleskom/NBA-ML-Sports-Betting](https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting)
- [bloomberg/quant-research](https://github.com/bloomberg/quant-research)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contact

For questions about this project, contact the CUIC Quant team through the club's official channels.
