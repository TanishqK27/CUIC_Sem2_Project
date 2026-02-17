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
git clone https://github.com/TanishqK27/CUIC_Sem2_Project.git
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
│   └── papers/            # Academic references
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
| Ismaeel   | TBD |
| Vansheeka | TBD |
| James     | TBD |

---

## Documentation

All documentation lives in the **[GitHub Wiki](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki)**.

### Getting Started
- [Environment Setup](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Environment-Setup)
- [Git Workflow](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Git-Workflow)
- [Claude Code Guide](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Using-Claude-Code)
- [API Keys Setup](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/API-Keys-Configuration)

### Platforms
- [Polymarket Guide](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Polymarket)
- [Kalshi Guide](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Kalshi)
- [Sports Betting Basics](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Sports-Betting)

### Research
- [Methodology](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Methodology)

### Contributing
- [Contribution Guidelines](CONTRIBUTING.md)

---

## Task Management

We use **[GitHub Issues](https://github.com/TanishqK27/CUIC_Sem2_Project/issues)** for task tracking and the **[Sprint Board](https://github.com/users/TanishqK27/projects/3)** for sprint planning.

---

## Polymarket API (Quick Start)

**No database setup required** - fetch live data directly from the API:

```python
from cuic_quant.notebook import pm

# Fetch live markets
df = pm.fetch_markets(limit=100, active=True)
print(df[['question', 'yes_price', 'volume']].head())

# Fetch order book
orderbook = pm.fetch_orderbook("token_id")
```

See the [Polymarket API Guide](research/notebooks/polymarket/API_GUIDE.md) and [example notebook](research/notebooks/polymarket/data_exploration.ipynb) for more.

---

## Key Features

### API Clients
Ready-to-use clients for major platforms:

```python
from cuic_quant.data import PolymarketClient, KalshiClient

# Fetch prediction market data
polymarket = PolymarketClient()
markets = polymarket.get_markets()
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

---

## Development Workflow

### Daily Checklist

1. **Pull latest:** `git pull origin main`
2. **Create branch:** `git checkout -b <name>/<feature>`
3. **Do work, run tests:** `pytest tests/ -v`
4. **Commit & push:** `git add . && git commit -m "message"`
5. **Create PR** when ready for review

### Slash Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/research-template` | Create research notebook | `/research-template polymarket price-discovery` |
| `/weekly-standup` | Generate team summary | `/weekly-standup` |

See [Skills Reference](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Skills-Reference) for detailed documentation.

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
