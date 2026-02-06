# Max's Work Log

Personal work log for the CUIC Quant Fund project. Entries are in reverse chronological order.

---

## How to Update

Use the `/update-log` skill:
```
/update-log max <description of work>
```

---

## Log Entries

### 2026-02-06

- Errors encountered: VS Code/Pylance unresolved imports for `numpy` and `pytest` due to incorrect interpreter path; PowerShell activation blocked by execution policy; Pylance `reportArgumentType` for `rsi` tests because `list[int]` passed where `list[float]` was expected.
- Changes made: updated `.vscode/settings.json` to use Windows venv interpreter path and added `python.terminal.activateEnvironment` + `python.venvPath`; fixed RSI tests to use `list[float]` and committed as "Fix RSI test price types for Pylance".

### 2025-02-01

- Joined CUIC Quant Fund project

---

<!-- New entries will be added above this line -->
