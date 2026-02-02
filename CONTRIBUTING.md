# Contributing to CUIC Quant Fund

Welcome to the CUIC Quant Fund project! This guide will help you contribute effectively.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Pull Request Guidelines](#pull-request-guidelines)
5. [Commit Messages](#commit-messages)
6. [Code Review](#code-review)
7. [Research Contributions](#research-contributions)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Your favorite IDE (VS Code or PyCharm recommended)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/CUIC/CUIC_Sem2_Project.git
cd CUIC_Sem2_Project

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install all dependencies
pip install -e .[all]

# Install pre-commit hooks
pre-commit install

# Copy environment template
cp configs/example.env .env
```

### Verify Setup

```bash
pytest tests/ -v
pre-commit run --all-files
```

---

## Development Workflow

### 1. Create a Feature Branch

Always work on a feature branch, never directly on `main`.

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b <your-name>/<feature-description>

# Examples:
# git checkout -b tan/polymarket-client
# git checkout -b andrii/kelly-optimization
```

### 2. Make Your Changes

- Write clean, documented code
- When using AI/Claude/Codex, be thorough and don't just push AI stuff without understanding and checking it first. 
- Add tests for new functionality
- Update relevant documentation

### 3. Test Your Changes

```bash
# Run tests
pytest tests/ -v

# Run linting
ruff check src/
ruff format src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### 4. Update Your Log

Update your personal log in `team/<your-name>/LOG.md`:

```markdown
## 2025-01-15

- Implemented Polymarket API client
- Added caching for market data
- Fixed rate limiting issue
```

Or use the skill: `/update-log <your-name> Implemented Polymarket API client`

### 5. Create Pull Request

```bash
# Push your branch
git push origin <your-name>/<feature-description>

# Then create PR on GitHub
```

---

## Code Standards

### Python Style

We use **ruff** for linting and formatting (Black-compatible).

```python
# Good: Type hints, docstrings, descriptive names
def calculate_expected_value(
    probability: float,
    odds: float,
    stake: float = 1.0,
) -> float:
    """Calculate the expected value of a bet.

    Args:
        probability: Estimated probability of winning (0-1).
        odds: Decimal odds offered.
        stake: Amount wagered.

    Returns:
        Expected value of the bet.

    Example:
        >>> calculate_expected_value(0.5, 2.0, 100)
        0.0
    """
    return (probability * odds - 1) * stake


# Bad: No types, no docs, unclear names
def calc_ev(p, o, s=1):
    return (p * o - 1) * s
```

### Docstring Format (Google Style)

```python
def function_name(param1: type, param2: type) -> return_type:
    """Short description of the function.

    Longer description if needed. Can span multiple lines.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something is wrong.

    Example:
        >>> function_name(1, 2)
        3
    """
```

### File Organization

```python
"""Module docstring explaining purpose."""

# Standard library imports
from collections.abc import Sequence
from typing import Any

# Third-party imports
import pandas as pd
import numpy as np

# Local imports
from cuic_quant.utils import helper_function


# Constants
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"


# Classes
class MyClass:
    """Class docstring."""
    pass


# Functions
def my_function() -> None:
    """Function docstring."""
    pass
```

### Testing Standards

```python
# tests/test_strategies.py
import pytest
from cuic_quant.strategies.kelly_criterion import calculate_kelly_fraction


class TestKellyCriterion:
    """Tests for Kelly Criterion calculations."""

    def test_positive_edge(self) -> None:
        """Kelly fraction should be positive when edge exists."""
        result = calculate_kelly_fraction(0.6, 2.0)
        assert result > 0

    def test_no_edge(self) -> None:
        """Kelly fraction should be zero with no edge."""
        result = calculate_kelly_fraction(0.5, 2.0)
        assert result == 0

    def test_invalid_probability(self) -> None:
        """Should raise ValueError for invalid probability."""
        with pytest.raises(ValueError):
            calculate_kelly_fraction(1.5, 2.0)

    @pytest.mark.parametrize(
        "prob,odds,expected",
        [
            (0.6, 2.0, 0.2),
            (0.7, 2.0, 0.4),
            (0.55, 2.0, 0.1),
        ],
    )
    def test_kelly_values(self, prob: float, odds: float, expected: float) -> None:
        """Kelly fraction should match expected values."""
        result = calculate_kelly_fraction(prob, odds)
        assert abs(result - expected) < 0.001
```

---

## Pull Request Guidelines

### PR Title Format

Use a clear, descriptive title:

```
feat: Add Polymarket API client
fix: Correct Kelly criterion edge case
docs: Update API key setup guide
test: Add arbitrage strategy tests
refactor: Simplify odds conversion logic
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Added X
- Fixed Y
- Updated Z

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manually tested the changes

## Related Issues
Closes #123 (if applicable)

## Screenshots
(if applicable)
```

### PR Checklist

Before requesting review:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Documentation updated if needed
- [ ] Personal LOG.md updated
- [ ] PR has clear description

---

## Commit Messages

### Format

```
<type>: <short description>

<optional longer description>

<optional footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding tests |
| `chore` | Maintenance tasks |

### Examples

```bash
# Good
git commit -m "feat: add Polymarket market data fetching"
git commit -m "fix: handle rate limiting in API client"
git commit -m "docs: add Kalshi API setup instructions"

# Bad
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "WIP"
```

---

## Code Review

### As a Reviewer

- Be constructive and specific
- Explain the "why" behind suggestions
- Approve when satisfied, don't block on minor issues
- Use GitHub's suggestion feature for small changes

### As an Author

- Respond to all comments
- Explain your decisions when not implementing suggestions
- Request re-review after making changes

### Review Checklist

- [ ] Code is readable and well-documented
- [ ] Logic is correct and handles edge cases
- [ ] Tests cover the new functionality
- [ ] No security issues (API keys, etc.)
- [ ] Performance is acceptable

---

## Research Contributions

### Adding a Research Notebook

1. **Create from template**:
   ```
   /research-template <category> <name>
   ```
   Categories: `polymarket`, `kalshi`, `sports`, `exploratory`

2. **Structure your notebook**:
   - Clear introduction with hypothesis
   - Data loading and exploration
   - Analysis with visualizations
   - Conclusions and next steps

3. **Document findings**:
   - Update `research/ideas/README.md` with insights
   - Add relevant papers to `research/papers/README.md`

### Submitting Research Ideas

Add to `research/ideas/README.md`:

```markdown
## [IDEA] Your Idea Title

**Submitted by:** Your Name
**Date:** 2025-01-15
**Status:** Proposed / In Progress / Completed

### Description
Brief description of the research idea.

### Hypothesis
What you expect to find.

### Data Required
- Data source 1
- Data source 2

### Next Steps
- Step 1
- Step 2
```

---

## Getting Help

- Check existing documentation in `docs/`
- Review `CLAUDE.md` for project context
- Ask in team communication channels
- Create an issue for bugs or feature requests

---

## Security

**Never commit:**
- API keys or secrets
- `.env` files with real values
- Credentials or passwords
- Personal access tokens

If you accidentally commit secrets:
1. Immediately rotate the exposed credentials
2. Contact the team lead
3. Use `git filter-branch` or BFG Repo-Cleaner to remove from history
