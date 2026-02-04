#!/bin/bash
# Run historic Polymarket data collection
# Called by cron at midnight

PROJECT_DIR="/Users/tanishq/Desktop/VSCode Folders/CUIC Quant /CUIC_Sem2_Project"

cd "$PROJECT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Run collection script
python scripts/collect_historic_data.py

# Deactivate
deactivate
