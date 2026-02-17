#!/bin/bash
# One-shot cron wrapper — runs collection then removes itself from crontab.
set -euo pipefail

PROJECT_DIR="/Users/tanishq/Desktop/iCloud Backup - Desktop/VSCode Folders/CUIC Quant /CUIC_Sem2_Project"
cd "$PROJECT_DIR"

export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

PYTHON="${PROJECT_DIR}/.venv/bin/python3"
mkdir -p logs data

# Run collection (caffeinate keeps machine awake)
caffeinate -s "$PYTHON" scripts/collect_nba_stats.py \
    --mode full --resume --verbose \
    >> logs/nba_collection.log 2>&1

# Remove this cron entry after completion
crontab -l 2>/dev/null | grep -v "cron_nba_collect" | crontab -
