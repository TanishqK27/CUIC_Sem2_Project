# Environment Setup Guide

Complete guide to setting up your development environment for the CUIC Quant Fund project.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Python Installation](#python-installation)
3. [Project Setup](#project-setup)
4. [IDE Configuration](#ide-configuration)
5. [Jupyter Setup](#jupyter-setup)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- [ ] Git installed
- [ ] Python 3.10 or higher
- [ ] A code editor (VS Code or PyCharm recommended)
- [ ] Terminal access (Terminal on Mac, Command Prompt/PowerShell on Windows)

---

## Python Installation

### macOS

**Option 1: Using Homebrew (Recommended)**

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
```

**Option 2: Official Installer**

1. Download from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. Check "Add Python to PATH"

### Windows

**Option 1: Official Installer (Recommended)**

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"

**Option 2: Using Chocolatey**

```powershell
# Install Chocolatey (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install Python
choco install python --version=3.11.0
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip

# Verify
python3.11 --version
```

### Verify Python Installation

```bash
# Check Python version (should be 3.10+)
python3 --version

# Check pip is installed
pip3 --version
```

---

## Project Setup

### 1. Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/CUIC/CUIC_Sem2_Project.git

# Or via SSH (if you have SSH keys set up)
git clone git@github.com:CUIC/CUIC_Sem2_Project.git

# Navigate to project
cd CUIC_Sem2_Project
```

### 2. Create Virtual Environment

A virtual environment isolates project dependencies from your system Python.

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment

# macOS/Linux:
source .venv/bin/activate

# Windows (Command Prompt):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

**You should see `(.venv)` in your terminal prompt when activated.**

### 3. Install Dependencies

```bash
# Install all dependencies (recommended)
pip install -e .[all]

# Or install specific groups:
pip install -e .           # Core only
pip install -e .[dev]      # Core + development tools
pip install -e .[research] # Core + Jupyter + ML libraries
```

### 4. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (first time)
pre-commit run --all-files
```

### 5. Configure Environment Variables

```bash
# Copy example environment file
cp configs/example.env .env

# Edit .env with your API keys
# (Use your favorite editor)
```

### 6. Verify Setup

```bash
# Run tests
pytest tests/ -v

# Check code quality
ruff check src/
mypy src/

# Start Jupyter (optional)
jupyter lab
```

---

## IDE Configuration

### VS Code (Recommended)

#### 1. Install VS Code

Download from [code.visualstudio.com](https://code.visualstudio.com/)

#### 2. Install Extensions

Open VS Code, go to Extensions (Cmd+Shift+X / Ctrl+Shift+X), and install:

| Extension | Purpose |
|-----------|---------|
| **Python** | Python language support |
| **Pylance** | Advanced Python IntelliSense |
| **Jupyter** | Notebook support |
| **Ruff** | Linting and formatting |
| **GitLens** | Enhanced Git integration |
| **Error Lens** | Inline error display |

#### 3. Configure Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "jupyter.notebookFileRoot": "${workspaceFolder}",
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/*.pyc": true,
        ".venv": true
    },
    "editor.rulers": [88],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

#### 4. Select Python Interpreter

1. Open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

### PyCharm

#### 1. Install PyCharm

Download from [jetbrains.com/pycharm](https://www.jetbrains.com/pycharm/)

- Community Edition (free) is sufficient
- Professional Edition adds more features

#### 2. Open Project

1. File → Open → Select `CUIC_Sem2_Project` folder
2. Click "Trust Project"

#### 3. Configure Interpreter

1. File → Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing environment"
4. Browse to `.venv/bin/python` (or `.venv\Scripts\python.exe`)
5. Click OK

#### 4. Enable Ruff

1. File → Settings → Tools → External Tools
2. Add new tool:
   - Name: Ruff Format
   - Program: `$PyInterpreterDirectory$/ruff`
   - Arguments: `format $FilePath$`
   - Working directory: `$ProjectFileDir$`

#### 5. Configure File Watchers (Optional)

Install File Watchers plugin for auto-formatting on save.

---

## Jupyter Setup

### Starting Jupyter Lab

```bash
# Activate virtual environment first
source .venv/bin/activate  # or Windows equivalent

# Start Jupyter Lab
jupyter lab

# Or classic notebook
jupyter notebook
```

### Recommended Jupyter Extensions

In Jupyter Lab:

```bash
# Install extensions via pip
pip install jupyterlab-git
pip install jupyterlab-code-formatter
```

### Jupyter Kernel Setup

If the kernel doesn't appear:

```bash
# Install kernel spec
python -m ipykernel install --user --name=cuic-quant --display-name="CUIC Quant"
```

### nbstripout (Notebook Cleaning)

We use nbstripout to remove output from notebooks before committing:

```bash
# Already installed via pre-commit hooks
# Manually strip output:
nbstripout research/notebooks/*.ipynb
```

---

## Troubleshooting

### Common Issues

#### "python: command not found"

**macOS/Linux:**

```bash
# Use python3 explicitly
python3 --version

# Or create alias
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

**Windows:**

- Reinstall Python with "Add to PATH" checked
- Or add manually: Settings → Environment Variables → PATH

#### "pip: command not found"

```bash
# Use pip3
pip3 install -e .[all]

# Or use python -m pip
python3 -m pip install -e .[all]
```

#### Virtual Environment Issues

**Can't activate on Windows PowerShell:**

```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.venv\Scripts\Activate.ps1
```

**Wrong Python version in venv:**

```bash
# Delete and recreate with specific version
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[all]
```

#### Pre-commit Hook Failures

```bash
# Update hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```

#### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e .[all]

# Check installation
pip list | grep cuic-quant
```

#### Jupyter Kernel Not Found

```bash
# Install kernel
python -m ipykernel install --user --name=cuic-quant

# List available kernels
jupyter kernelspec list
```

### Getting Help

1. Check error message carefully
2. Search the error on Google/Stack Overflow
3. Ask in team chat
4. Create an issue in the repository

---

## Quick Reference

### Daily Commands

```bash
# Activate environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Format code
ruff format src/

# Lint code
ruff check src/ --fix

# Type check
mypy src/

# Start Jupyter
jupyter lab

# Update dependencies
pip install -e .[all] --upgrade
```

### Git Commands

```bash
# Pull latest
git pull origin main

# Create branch
git checkout -b <name>/<feature>

# Stage changes
git add <files>

# Commit
git commit -m "feat: description"

# Push
git push origin <branch-name>
```

---

## Next Steps

1. [Configure API Keys](api-keys.md)
2. [Set up Claude Code](using-claude-code.md)
3. Review [CONTRIBUTING.md](../../CONTRIBUTING.md)
4. Start exploring notebooks in `research/notebooks/`
