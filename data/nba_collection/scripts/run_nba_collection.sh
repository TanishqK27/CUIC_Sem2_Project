#!/bin/bash
# NBA data collection — single command, loading bar, hourly updates.
#
# Usage:
#   ./scripts/run_nba_collection.sh               # all 5 seasons (2021-22 to 2025-26)
#   ./scripts/run_nba_collection.sh 2024-25        # single season
#   ./scripts/run_nba_collection.sh 2024-25 2025-26 # specific seasons
#
# What you'll see:
#   - Phase banners (1/8, 2/8, ...) for each stage
#   - tqdm loading bar with ETA during box score collection
#   - Hourly progress summaries printed above the bar
#   - Final summary with row counts for all CSVs
#
# Survives MacBook lid close:
#   - caffeinate prevents idle sleep
#   - --resume auto-skips already-collected games
#   - Auto-retries on wake after sleep interruption
#
# Output:
#   - CSVs:  data/
#   - Logs:  logs/nba_collection.log
#
# Stop cleanly: Ctrl-C twice (once to kill python, once to exit loop)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Java setup for nbainjuries (injury report PDF parsing)
export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"

# Ensure src is on PYTHONPATH (spaces in path break .pth files)
export PYTHONPATH="${PROJECT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

PYTHON="${PROJECT_DIR}/.venv/bin/python3"
mkdir -p logs data

SEASONS="${*:-}"  # pass seasons as args, or empty for all

SEASON_FLAG=""
if [ -n "$SEASONS" ]; then
    SEASON_FLAG="--seasons $SEASONS"
fi

MAX_RETRIES=50   # enough for a full day of lid-open/close cycles
RETRY_DELAY=15   # seconds to wait before restarting after failure

echo ""
echo "  Closing your MacBook lid is fine — collection auto-resumes on wake."
echo "  All output also saved to: logs/nba_collection.log"
echo "  Press Ctrl-C twice to stop."
echo ""

attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
    attempt=$((attempt + 1))

    if [ $attempt -gt 1 ]; then
        echo "[$(date '+%H:%M:%S')] Attempt $attempt — resuming from checkpoint..."
    fi

    # caffeinate -s: prevent system idle sleep while this runs
    # tee: mirror all output to log file while keeping the terminal live
    if caffeinate -s "$PYTHON" scripts/collect_nba_stats.py \
        --mode full --resume --verbose $SEASON_FLAG \
        2>&1 | tee -a logs/nba_collection.log; then
        echo ""
        echo "CSVs are in: $PROJECT_DIR/data/"
        echo ""
        echo "Run audit:   python scripts/audit_nba_collection.py --verbose"
        break
    fi

    echo "[$(date '+%H:%M:%S')] Process interrupted (sleep/error). Resuming in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

if [ $attempt -ge $MAX_RETRIES ]; then
    echo "Hit max retries ($MAX_RETRIES). Check logs/nba_collection.log for errors."
    exit 1
fi
