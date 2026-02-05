#!/usr/bin/env python3
"""Auto-generate .claude/CONTEXT.md with current project state.

This script scans the codebase and generates an up-to-date context file
for Claude Code sessions. Run it whenever you want to refresh the context.

Usage:
    python scripts/update_context.py
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
CONTEXT_FILE = PROJECT_ROOT / ".claude" / "CONTEXT.md"


def get_git_info() -> dict[str, str]:
    """Get current git branch and recent commits."""
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        ).stdout.strip()

        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        ).stdout.strip()

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        ).stdout.strip()

        return {
            "branch": branch or "unknown",
            "commits": log or "No commits",
            "status": "clean" if not status else f"{len(status.splitlines())} changes",
        }
    except Exception:
        return {
            "branch": "unknown",
            "commits": "Error reading git",
            "status": "unknown",
        }


def get_team_status() -> list[dict[str, str]]:
    """Scan team folders for activity and tasks."""
    team_dir = PROJECT_ROOT / "team"
    members = [
        "tan",
        "andrii",
        "ben",
        "dietrich",
        "alfie",
        "max",
        "miran",
        "mya",
        "isameel",
        "vansheeka",
        "james",
    ]
    roles = {
        "tan": "Lead / Infrastructure",
    }

    team_status = []
    for member in members:
        member_dir = team_dir / member
        log_file = member_dir / "LOG.md"
        tasks_file = member_dir / "TASKS.md"

        # Get last activity from LOG.md
        last_activity = "Unknown"
        if log_file.exists():
            content = log_file.read_text()
            # Find dates in format ## YYYY-MM-DD
            dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", content)
            if dates:
                last_activity = dates[0]

        # Count active tasks
        active_tasks = "None assigned"
        if tasks_file.exists():
            content = tasks_file.read_text()
            # Count uncompleted tasks (lines with - [ ])
            incomplete = len(re.findall(r"- \[ \]", content))
            if incomplete > 0:
                active_tasks = f"{incomplete} tasks"

        team_status.append(
            {
                "name": member.capitalize(),
                "role": roles.get(member, "TBD"),
                "last_activity": last_activity,
                "tasks": active_tasks,
            }
        )

    return team_status


def count_lines(filepath: Path) -> int:
    """Count lines in a file."""
    try:
        return len(filepath.read_text().splitlines())
    except Exception:
        return 0


def get_code_status() -> dict[str, list[dict]]:
    """Analyze source code implementation status."""
    src_dir = PROJECT_ROOT / "src" / "cuic_quant"

    strategies = []
    strategy_dir = src_dir / "strategies"
    if strategy_dir.exists():
        for py_file in strategy_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            lines = count_lines(py_file)
            strategies.append(
                {
                    "name": py_file.name,
                    "lines": lines,
                    "status": "Complete" if lines > 50 else "Stub",
                }
            )

    clients = []
    data_dir = src_dir / "data"
    if data_dir.exists():
        for py_file in data_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            lines = count_lines(py_file)
            clients.append(
                {
                    "name": py_file.name,
                    "lines": lines,
                    "status": "Framework ready" if lines > 30 else "Stub",
                }
            )

    return {"strategies": strategies, "clients": clients}


def count_tasks() -> dict[str, int]:
    """Count tasks by status in PROJECT_TASKS.md."""
    tasks_file = PROJECT_ROOT / "team" / "PROJECT_TASKS.md"
    if not tasks_file.exists():
        return {"total": 0, "completed": 0, "pending": 0}

    content = tasks_file.read_text()
    total = len(re.findall(r"### TASK-\d+", content))
    completed = len(re.findall(r"- \[x\]", content))
    pending = len(re.findall(r"- \[ \]", content))

    return {"total": total, "completed": completed, "pending": pending}


def generate_context() -> str:
    """Generate the full context markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    git = get_git_info()
    team = get_team_status()
    code = get_code_status()
    tasks = count_tasks()

    # Build team table
    team_rows = "\n".join(
        f"| {m['name']} | {m['role']} | {m['last_activity']} | {m['tasks']} |"
        for m in team
    )

    # Build strategy table
    strategy_rows = "\n".join(
        f"| {s['name']} | {s['status']} | {s['lines']} |" for s in code["strategies"]
    )

    # Build client table
    client_rows = "\n".join(
        f"| {c['name']} | {c['status']} | {c['lines']} |" for c in code["clients"]
    )

    # Git commits (format nicely)
    git_commits = "\n".join(f"- {line}" for line in git["commits"].split("\n") if line)

    return f"""# CUIC Quant Project Context (Auto-Generated)

> **Last Updated:** {today}
> **Run `python scripts/update_context.py` to refresh this file**

---

## Quick Summary

**Project:** Cardiff University Investment Club quantitative research for sports betting and prediction markets (Polymarket, Kalshi).

**Stage:** Alpha v0.1.0 - Infrastructure complete, awaiting team research execution.

**Key Dates:**
- Feb 2025: Phase 1 (Infrastructure) - Mostly Complete
- Mar 2025: Phase 2 (Research) - Not Started
- Apr 2025: Phase 3 (Strategy Development) - Not Started
- May 2025: Phase 4 (Paper Trading) - Not Started

---

## Team Status ({len(team)} members)

| Member | Role | Last Activity | Active Tasks |
|--------|------|---------------|--------------|
{team_rows}

---

## Code Implementation Status

### Strategies (src/cuic_quant/strategies/)
| Module | Status | Lines |
|--------|--------|-------|
{strategy_rows}

### Data Clients (src/cuic_quant/data/)
| Client | Status | Lines |
|--------|--------|-------|
{client_rows}

---

## Research Tasks ({tasks['total']} total)

- **Completed:** {tasks['completed']}
- **Pending:** {tasks['pending']}

**Task file:** `team/PROJECT_TASKS.md`

---

## Git Status

**Branch:** {git['branch']}
**Working tree:** {git['status']}

**Recent Commits:**
{git_commits}

---

## Key File Paths

### Configuration
- `pyproject.toml` - Dependencies and tool config
- `configs/example.env` - Environment template
- `.pre-commit-config.yaml` - Code quality hooks

### Documentation
- `CLAUDE.md` - Main project context (checked into repo)
- `docs/setup/` - Environment, API keys, Claude Code guides
- `docs/platforms/` - Polymarket, Kalshi, sports betting guides

### Team Management
- `team/PROJECT_LOG.md` - Aggregated activity log
- `team/PROJECT_TASKS.md` - All research tasks
- `team/<name>/LOG.md` - Individual work logs
- `team/<name>/TASKS.md` - Individual task assignments

### Custom Skills
- `/update-log <name> <message>` - Update team member log
- `/research-template <category> <name>` - Create research notebook
- `/weekly-standup` - Generate progress summary

---

## Quick Commands

```bash
# Environment
source .venv/bin/activate
pip install -e .[dev,research]

# Development
pytest tests/ -v              # Run tests
ruff check src/               # Lint
ruff format src/              # Format

# Context
python scripts/update_context.py  # Refresh this file
python scripts/sync_logs.py       # Sync team logs
```

---

*This file is auto-generated by `scripts/update_context.py`*
"""


def main() -> None:
    """Generate and write the context file."""
    print(f"Generating context file: {CONTEXT_FILE}")

    # Ensure .claude directory exists
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Generate and write
    content = generate_context()
    CONTEXT_FILE.write_text(content)

    print(f"Context file updated: {CONTEXT_FILE}")
    print(f"Lines: {len(content.splitlines())}")


if __name__ == "__main__":
    main()
