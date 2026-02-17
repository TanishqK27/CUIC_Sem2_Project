# CUIC Quant Fund - Project Context

## Project Overview

Cardiff University Investment Club (CUIC) quantitative research project focused on **sports betting and prediction markets** (Kalshi, The Odds API) for alpha generation through arbitrage, mean reversion, and systematic strategies.

**Semester:** Spring 2025
**Focus Areas:** Prediction Markets, Sports Betting, Quantitative Strategies

---

## Team Roster

| Member     | Focus Area (TBD) |
|------------|------------------|
| Tan        | Lead / Infrastructure |
| Andrii     | - |
| Dietrich   | - |
| Ben        | - |
| Alfie      | - |
| Max        | - |
| Miran      | - |
| Mya        | - |
| Ismaeel    | - |
| Vansheeka  | - |
| James      | - |

> Team pages and logs are on the [GitHub Wiki](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki).

---

## Common Commands

```bash
# Environment setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e .[dev,research]

# Run tests
pytest tests/ -v

# Code quality
pre-commit run --all-files
ruff check src/
ruff format src/

# Start Jupyter
jupyter lab
```

---

## Code Standards

- **Python Version:** 3.10+
- **Type Hints:** Required for all functions
- **Docstrings:** Google style
- **Formatting:** ruff format (Black-compatible)
- **Linting:** ruff check
- **Testing:** pytest with fixtures in `tests/conftest.py`

### Example Function

```python
def calculate_kelly_fraction(
    win_probability: float,
    odds: float,
    bankroll_fraction: float = 1.0,
) -> float:
    """Calculate optimal Kelly Criterion bet size.

    Args:
        win_probability: Estimated probability of winning (0-1).
        odds: Decimal odds offered by bookmaker.
        bankroll_fraction: Fraction of Kelly to use (default full Kelly).

    Returns:
        Optimal fraction of bankroll to bet.

    Raises:
        ValueError: If win_probability not in [0, 1].

    Example:
        >>> calculate_kelly_fraction(0.6, 2.0)
        0.2
    """
    if not 0 <= win_probability <= 1:
        raise ValueError("win_probability must be between 0 and 1")

    q = 1 - win_probability
    kelly = (win_probability * odds - q) / odds
    return max(0, kelly * bankroll_fraction)
```

---

## Workflow Instructions

### Daily Workflow
1. Pull latest changes: `git pull origin main`
2. Create feature branch: `git checkout -b <name>/<feature>`
3. Run tests before committing: `pytest tests/ -v`
4. Create PR when ready for review

> **Full Git guide:** See the [Git Workflow](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Git-Workflow) wiki page.

### Research Workflow
1. Use `/research-template <category> <name>` to create notebook from template
2. Document findings in notebook markdown cells
3. Move successful experiments to `src/cuic_quant/`

---

## Key File Locations

| Purpose | Location |
|---------|----------|
| Main package | `src/cuic_quant/` |
| API clients | `src/cuic_quant/data/` |
| Trading strategies | `src/cuic_quant/strategies/` |
| Research notebooks | `research/notebooks/` |
| Configuration | `configs/` |
| Documentation | [GitHub Wiki](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki) |
| Task tracking | [GitHub Issues](https://github.com/TanishqK27/CUIC_Sem2_Project/issues) |

---

## Platform Quick Reference

### Kalshi
- **Type:** CFTC-regulated event contracts exchange
- **Currency:** USD
- **Docs:** https://docs.kalshi.com/
- **Client:** `src/cuic_quant/data/kalshi_client.py`

### Sports Betting (The Odds API)
- **Type:** Aggregated odds from bookmakers
- **Docs:** https://the-odds-api.com/
- **Client:** `src/cuic_quant/data/odds_api.py`

---

## Security Warnings

> **CRITICAL: Never commit API keys, passwords, or credentials!**

- Use `.env` files for secrets (already in `.gitignore`)
- Reference `configs/example.env` for required variables
- See [API Keys Configuration](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/API-Keys-Configuration) wiki page

---

## Custom Skills

| Skill | Usage | Description |
|-------|-------|-------------|
| `/research-template` | `/research-template <category> <name>` | Creates notebook from template |
| `/weekly-standup` | `/weekly-standup` | Generates weekly progress summary |

> **Full documentation:** See the [Skills Reference](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki/Skills-Reference) wiki page.

---

## Dependencies Overview

**Core:**
- pandas, numpy - Data manipulation
- requests, aiohttp, httpx - API clients
- pydantic - Data validation

**Research:**
- jupyter, jupyterlab - Notebooks
- matplotlib, plotly - Visualization
- scikit-learn - ML models

**Development:**
- pytest - Testing
- ruff - Linting/formatting
- mypy - Type checking
- pre-commit - Git hooks

---

## Getting Help

1. Check the [GitHub Wiki](https://github.com/TanishqK27/CUIC_Sem2_Project/wiki) for guides and references
2. Review `research/papers/README.md` for academic references
3. Ask in team chat
4. Create a [GitHub Issue](https://github.com/TanishqK27/CUIC_Sem2_Project/issues) for bugs or feature requests
