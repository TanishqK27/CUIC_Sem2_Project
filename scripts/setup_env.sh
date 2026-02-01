#!/bin/bash
# CUIC Quant Fund - Environment Setup Script
#
# This script sets up the development environment for the project.
#
# Usage:
#   chmod +x scripts/setup_env.sh
#   ./scripts/setup_env.sh
#
# Options:
#   --no-venv    Skip virtual environment creation
#   --dev        Install dev dependencies only
#   --research   Install research dependencies only
#   --all        Install all dependencies (default)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
CREATE_VENV=true
INSTALL_MODE="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-venv)
            CREATE_VENV=false
            shift
            ;;
        --dev)
            INSTALL_MODE="dev"
            shift
            ;;
        --research)
            INSTALL_MODE="research"
            shift
            ;;
        --all)
            INSTALL_MODE="all"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "CUIC Quant Fund - Environment Setup"
echo "=========================================="
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}Python $PYTHON_VERSION - OK${NC}"

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
echo "Working directory: $PROJECT_ROOT"
echo ""

# Create virtual environment
if [ "$CREATE_VENV" = true ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"

    if [ -d ".venv" ]; then
        echo "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv .venv
        echo -e "${GREEN}Virtual environment created.${NC}"
    fi

    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate

    # Upgrade pip
    echo -e "${YELLOW}Upgrading pip...${NC}"
    pip install --upgrade pip
fi

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies (mode: $INSTALL_MODE)...${NC}"

case $INSTALL_MODE in
    dev)
        pip install -e ".[dev]"
        ;;
    research)
        pip install -e ".[research]"
        ;;
    all)
        pip install -e ".[all]"
        ;;
esac

echo -e "${GREEN}Dependencies installed.${NC}"

# Install pre-commit hooks
echo ""
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}Pre-commit hooks installed.${NC}"
else
    echo -e "${RED}Warning: pre-commit not found. Install with 'pip install pre-commit'${NC}"
fi

# Create .env file if it doesn't exist
echo ""
echo -e "${YELLOW}Checking environment file...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "configs/example.env" ]; then
        cp configs/example.env .env
        echo -e "${GREEN}Created .env from template.${NC}"
        echo -e "${YELLOW}Remember to add your API keys to .env${NC}"
    else
        echo -e "${YELLOW}No .env file found. Create one from configs/example.env${NC}"
    fi
else
    echo ".env file already exists."
fi

# Run initial checks
echo ""
echo -e "${YELLOW}Running initial checks...${NC}"

# Check if package is importable
echo -n "Checking package import... "
if python3 -c "import cuic_quant" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Run tests
echo ""
echo -e "${YELLOW}Running tests...${NC}"
if python3 -m pytest tests/ -v --tb=short 2>/dev/null; then
    echo -e "${GREEN}Tests passed.${NC}"
else
    echo -e "${YELLOW}Some tests failed. This may be expected for integration tests.${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Add your API keys to .env"
echo "     See docs/setup/api-keys.md for details"
echo ""
echo "  3. Start developing!"
echo "     pytest tests/ -v       # Run tests"
echo "     jupyter lab            # Start Jupyter"
echo "     pre-commit run --all   # Run linters"
echo ""
