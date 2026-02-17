#!/bin/bash
# Live NBA data updater — runs incremental updates on a schedule.
#
# Usage:
#   ./scripts/nba_live_update.sh              # run once
#   ./scripts/nba_live_update.sh --loop 30    # run every 30 minutes
#   ./scripts/nba_live_update.sh --loop 60    # run every 60 minutes
#
# What it updates:
#   - New games + box scores since last checkpoint
#   - Current season stats, standings, rosters
#   - Latest injury report (from NBA's official PDFs)
#
# Requires: Java (brew install java) for injury reports
#
# To install as a persistent background job:
#   ./scripts/nba_live_update.sh --install    # creates launchd plist
#   ./scripts/nba_live_update.sh --uninstall  # removes it

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Java setup for nbainjuries
export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"

PLIST_NAME="com.cuicquant.nba-live-update"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

_run_update() {
    source .venv/bin/activate
    mkdir -p logs data

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running incremental NBA update..."
    python scripts/collect_nba_stats.py --mode update --verbose
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update complete."
    echo ""
}

_install_launchd() {
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_DIR}/scripts/nba_live_update.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/logs/nba_live_update.log</string>
    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/logs/nba_live_update.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>JAVA_HOME</key>
        <string>/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home</string>
        <key>PATH</key>
        <string>/opt/homebrew/opt/openjdk/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST

    launchctl load "$PLIST_PATH"
    echo "Installed and started: ${PLIST_NAME}"
    echo "  Updates every 30 minutes, even after reboot"
    echo "  Logs: ${PROJECT_DIR}/logs/nba_live_update.log"
    echo ""
    echo "  To stop:    launchctl unload ${PLIST_PATH}"
    echo "  To remove:  ./scripts/nba_live_update.sh --uninstall"
}

_uninstall_launchd() {
    if [ -f "$PLIST_PATH" ]; then
        launchctl unload "$PLIST_PATH" 2>/dev/null || true
        rm "$PLIST_PATH"
        echo "Removed: ${PLIST_NAME}"
    else
        echo "Not installed."
    fi
}

# Parse args
case "${1:-}" in
    --install)
        _install_launchd
        ;;
    --uninstall)
        _uninstall_launchd
        ;;
    --loop)
        INTERVAL="${2:-30}"
        echo "=== NBA Live Updater (every ${INTERVAL} min) ==="
        echo "  Press Ctrl-C to stop."
        echo ""
        while true; do
            _run_update || echo "[$(date '+%H:%M:%S')] Update failed, retrying next cycle."
            echo "Sleeping ${INTERVAL} minutes..."
            sleep $((INTERVAL * 60))
        done
        ;;
    *)
        _run_update
        ;;
esac
