#!/bin/bash

# ============================================================================
# Kortix Development Environment Stop Script
# ============================================================================
# This script stops all services started by start.sh
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/.logs"
PIDS_FILE="$LOGS_DIR/pids.txt"

echo -e "${BLUE}Stopping all services...${NC}"

# Kill all background processes
if [ -f "$PIDS_FILE" ]; then
    while read pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
            # Wait a bit for graceful shutdown
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
    done < "$PIDS_FILE"
    > "$PIDS_FILE"  # Clear PIDs file
else
    echo -e "${YELLOW}No PID file found. Services may not be running.${NC}"
fi

# Stop docker compose services
echo -e "${BLUE}Stopping Docker services...${NC}"
cd "$SCRIPT_DIR"
docker compose down redis 2>/dev/null || true

echo -e "${GREEN}All services stopped.${NC}"

