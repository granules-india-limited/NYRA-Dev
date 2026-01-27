#!/bin/bash

# ============================================================================
# Kortix Development Environment Startup Script
# ============================================================================
# This script starts all required services for local development:
# 1. Redis (via Docker Compose)
# 2. Frontend (Next.js)
# 3. Backend API (FastAPI)
# 4. Background Worker
#
# Usage:
#   ./start.sh              - Start all services
#   ./start.sh --migrate     - Run migrations before starting
#   ./start.sh --logs        - Start services and tail logs
#   ./start.sh --help        - Show this help message
# ============================================================================

set -e  # Exit on error

# Show help if requested
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Kortix Development Environment Startup Script"
    echo ""
    echo "Usage:"
    echo "  ./start.sh              Start all services"
    echo "  ./start.sh --migrate     Run database migrations before starting"
    echo "  ./start.sh --logs        Start services and tail logs"
    echo "  ./start.sh --help        Show this help message"
    echo ""
    exit 0
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
LOGS_DIR="$SCRIPT_DIR/.logs"
mkdir -p "$LOGS_DIR"

# PID file to track background processes
PIDS_FILE="$LOGS_DIR/pids.txt"
> "$PIDS_FILE"  # Clear previous PIDs

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill all background processes
    if [ -f "$PIDS_FILE" ]; then
        while read pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${BLUE}Stopping process $pid...${NC}"
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PIDS_FILE"
    fi
    
    # Stop docker compose services
    echo -e "${BLUE}Stopping Docker services...${NC}"
    docker compose down redis 2>/dev/null || true
    
    echo -e "${GREEN}Cleanup complete.${NC}"
    exit 0
}

# Trap signals to cleanup
trap cleanup SIGINT SIGTERM EXIT

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required commands
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker compose; then
    echo -e "${RED}Error: docker compose is not installed${NC}"
    exit 1
fi

if ! command_exists pnpm; then
    echo -e "${RED}Error: pnpm is not installed${NC}"
    exit 1
fi

if ! command_exists uv; then
    echo -e "${RED}Error: uv is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}\n"

# Check for required environment files
echo -e "${BLUE}Checking configuration files...${NC}"

if [ ! -f "$SCRIPT_DIR/backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found${NC}"
    echo -e "${YELLOW}  Run 'python3 setup.py' to configure the project${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ backend/.env found${NC}"
fi

if [ ! -f "$SCRIPT_DIR/apps/frontend/.env.local" ]; then
    echo -e "${YELLOW}Warning: apps/frontend/.env.local not found${NC}"
    echo -e "${YELLOW}  Run 'python3 setup.py' to configure the project${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ apps/frontend/.env.local found${NC}"
fi

# Check if migrations have been applied (optional check)
if [ -f "$SCRIPT_DIR/backend/.env" ]; then
    # Extract SUPABASE_URL from .env if possible
    if grep -q "SUPABASE_URL" "$SCRIPT_DIR/backend/.env"; then
        SUPABASE_URL=$(grep "^SUPABASE_URL=" "$SCRIPT_DIR/backend/.env" | cut -d '=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$SUPABASE_URL" ] && [[ "$SUPABASE_URL" == *"supabase.co"* ]]; then
            echo -e "${BLUE}Checking database migrations...${NC}"
            MIGRATIONS_DIR="$SCRIPT_DIR/backend/supabase/migrations"
            if [ -d "$MIGRATIONS_DIR" ] && [ "$(ls -A $MIGRATIONS_DIR/*.sql 2>/dev/null)" ]; then
                MIGRATION_COUNT=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | wc -l)
                echo -e "${GREEN}✓ Found $MIGRATION_COUNT migration files${NC}"
                echo -e "${YELLOW}  Note: Ensure migrations are applied to your Supabase database${NC}"
                echo -e "${YELLOW}  Run 'python3 apply_migrations.py' if needed${NC}"
            else
                echo -e "${YELLOW}⚠ No migration files found${NC}"
            fi
        fi
    fi
fi

echo ""

# Function to kill existing services
kill_existing_services() {
    # Temporarily disable exit on error for cleanup
    set +e
    
    echo -e "${YELLOW}Checking for existing services...${NC}"
    
    # Kill processes from previous PID file if it exists
    if [ -f "$PIDS_FILE" ]; then
        while read pid; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Killing existing process $pid...${NC}"
                kill "$pid" 2>/dev/null || true
                sleep 1
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done < "$PIDS_FILE"
    fi
    
    # Kill any processes matching our services by command pattern
    # Frontend: pnpm run dev (in apps/frontend directory)
    pkill -f "pnpm.*run.*dev" 2>/dev/null || true
    
    # Backend: uv run api.py (in backend directory)
    pkill -f "uv.*run.*api.py" 2>/dev/null || true
    
    # Worker: uv run run_worker.py (in backend directory)
    pkill -f "uv.*run.*run_worker.py" 2>/dev/null || true
    
    # Also check for processes on specific ports (if lsof is available)
    if command_exists lsof; then
        # Frontend port 3000 - kill multiple times to ensure it's free
        for i in {1..3}; do
            if lsof -ti:3000 >/dev/null 2>&1; then
                echo -e "${YELLOW}Killing process on port 3000 (Frontend)... (attempt $i)${NC}"
                lsof -ti:3000 | xargs kill -9 2>/dev/null || true
                sleep 1
            else
                break
            fi
        done
        
        # Backend port 8000 - kill multiple times to ensure it's free
        for i in {1..3}; do
            if lsof -ti:8000 >/dev/null 2>&1; then
                echo -e "${YELLOW}Killing process on port 8000 (Backend)... (attempt $i)${NC}"
                lsof -ti:8000 | xargs kill -9 2>/dev/null || true
                sleep 1
            else
                break
            fi
        done
    fi
    
    # Also kill any Next.js processes that might be holding port 3000
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "next-server" 2>/dev/null || true
    
    # Stop existing docker compose services
    if docker compose ps redis 2>/dev/null | grep -q "running"; then
        echo -e "${YELLOW}Stopping existing Redis container...${NC}"
        docker compose down redis 2>/dev/null || true
    fi
    
    # Wait for processes to fully terminate and ports to be released
    sleep 3
    
    # Verify ports are free
    if command_exists lsof; then
        if lsof -ti:3000 >/dev/null 2>&1; then
            echo -e "${RED}Warning: Port 3000 is still in use after cleanup${NC}"
            lsof -ti:3000 | xargs -I {} sh -c 'echo "  Process {}: $(ps -p {} -o comm= 2>/dev/null || echo unknown)"' || true
        fi
        if lsof -ti:8000 >/dev/null 2>&1; then
            echo -e "${RED}Warning: Port 8000 is still in use after cleanup${NC}"
            lsof -ti:8000 | xargs -I {} sh -c 'echo "  Process {}: $(ps -p {} -o comm= 2>/dev/null || echo unknown)"' || true
        fi
    fi
    
    # Re-enable exit on error
    set -e
    
    echo -e "${GREEN}✓ Existing services cleaned up${NC}\n"
}

# Function to check and optionally install dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check frontend dependencies
    if [ ! -d "$SCRIPT_DIR/apps/frontend/node_modules" ]; then
        echo -e "${YELLOW}Frontend dependencies not found${NC}"
        read -p "Install frontend dependencies now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Installing frontend dependencies...${NC}"
            cd "$SCRIPT_DIR/apps/frontend"
            pnpm install
            cd "$SCRIPT_DIR"
            echo -e "${GREEN}✓ Frontend dependencies installed${NC}\n"
        fi
    else
        echo -e "${GREEN}✓ Frontend dependencies found${NC}"
    fi
    
    # Check backend dependencies
    if [ ! -d "$SCRIPT_DIR/backend/.venv" ]; then
        echo -e "${YELLOW}Backend virtual environment not found${NC}"
        read -p "Install backend dependencies now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Installing backend dependencies...${NC}"
            cd "$SCRIPT_DIR/backend"
            uv venv
            uv sync
            cd "$SCRIPT_DIR"
            echo -e "${GREEN}✓ Backend dependencies installed${NC}\n"
        fi
    else
        echo -e "${GREEN}✓ Backend virtual environment found${NC}"
    fi
    
    echo ""
}

# Check dependencies
check_dependencies

# Run migrations if requested (before starting services)
if [ "$1" == "--migrate" ] || [ "$1" == "-m" ]; then
    echo -e "${BLUE}Running database migrations...${NC}"
    if [ -f "$SCRIPT_DIR/apply_migrations.py" ]; then
        python3 "$SCRIPT_DIR/apply_migrations.py"
        echo ""
    else
        echo -e "${YELLOW}Migration script not found. Skipping migrations.${NC}"
        echo -e "${YELLOW}  Run 'python3 apply_migrations.py' manually if needed${NC}\n"
    fi
fi

# Clean up any existing services
kill_existing_services

# Step 1: Start Infrastructure (Redis)
echo -e "${BLUE}[1/4] Starting Infrastructure (Redis)...${NC}"
docker compose up redis -d

# Wait for Redis to be healthy
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
timeout=30
counter=0
while ! docker compose ps redis | grep -q "healthy"; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}Error: Redis failed to start within $timeout seconds${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Redis is ready${NC}\n"

# Step 2: Start Frontend
echo -e "${BLUE}[2/4] Starting Frontend...${NC}"

# Check if production mode is enabled
FRONTEND_ENV_FILE="$SCRIPT_DIR/apps/frontend/.env.local"
IS_PRODUCTION_MODE=false
if [ -f "$FRONTEND_ENV_FILE" ]; then
    if grep -q "^NEXT_PUBLIC_ENV_MODE=PRODUCTION" "$FRONTEND_ENV_FILE" || \
       grep -q "^NEXT_PUBLIC_ENV_MODE=production" "$FRONTEND_ENV_FILE"; then
        IS_PRODUCTION_MODE=true
        echo -e "${YELLOW}Production mode detected - will build and run production server${NC}"
    fi
fi

# Final check to ensure port 3000 is free
if command_exists lsof; then
    if lsof -ti:3000 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 3000 still in use, attempting to free it...${NC}"
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -ti:3000 >/dev/null 2>&1; then
            echo -e "${RED}Error: Port 3000 is still in use. Please manually free it and try again.${NC}"
            exit 1
        fi
    fi
fi

cd "$SCRIPT_DIR/apps/frontend"

if [ "$IS_PRODUCTION_MODE" = true ]; then
    # Production mode: Build first, then run production server
    echo -e "${BLUE}Building frontend for production...${NC}"
    echo -e "${YELLOW}  This may take a few minutes...${NC}"
    
    # Temporarily disable exit on error for build
    set +e
    cd "$SCRIPT_DIR/apps/frontend"
    pnpm run build > "$LOGS_DIR/frontend-build.log" 2>&1
    BUILD_EXIT_CODE=$?
    set -e
    
    # Check if build failed
    if [ $BUILD_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}Error: Frontend build failed. Check logs: $LOGS_DIR/frontend-build.log${NC}"
        echo -e "${YELLOW}Last 50 lines of build log:${NC}"
        tail -50 "$LOGS_DIR/frontend-build.log" 2>/dev/null || true
        exit 1
    else
        echo -e "${GREEN}✓ Frontend build completed successfully${NC}"
    fi
    
    echo -e "${GREEN}✓ Frontend build completed${NC}"
    echo -e "${BLUE}Starting production server...${NC}"
    
    # Next.js production server - binds to localhost by default (fine for nginx proxy)
    # If you need 0.0.0.0, you can modify package.json "start" script to: "next start -H 0.0.0.0"
    PORT=3000 pnpm start > "$LOGS_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
else
    # Development mode: Run dev server
    PORT=3000 pnpm run dev > "$LOGS_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
fi

echo "$FRONTEND_PID" >> "$PIDS_FILE"

# Wait a moment and verify the process is still running
sleep 2
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${RED}Error: Frontend process failed to start. Check logs: $LOGS_DIR/frontend.log${NC}"
    tail -20 "$LOGS_DIR/frontend.log" 2>/dev/null || true
    exit 1
fi

if [ "$IS_PRODUCTION_MODE" = true ]; then
    echo -e "${GREEN}✓ Frontend started in PRODUCTION mode (PID: $FRONTEND_PID) on port 3000${NC}"
else
    echo -e "${GREEN}✓ Frontend started in DEVELOPMENT mode (PID: $FRONTEND_PID) on port 3000${NC}"
fi
echo -e "${YELLOW}  Logs: $LOGS_DIR/frontend.log${NC}\n"
cd "$SCRIPT_DIR"

# Step 3: Start Backend
echo -e "${BLUE}[3/4] Starting Backend API...${NC}"

# Final check to ensure port 8000 is free
if command_exists lsof; then
    if lsof -ti:8000 >/dev/null 2>&1; then
        echo -e "${YELLOW}Port 8000 still in use, attempting to free it...${NC}"
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -ti:8000 >/dev/null 2>&1; then
            echo -e "${RED}Error: Port 8000 is still in use. Please manually free it and try again.${NC}"
            exit 1
        fi
    fi
fi

cd "$SCRIPT_DIR/backend"
uv run api.py > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PIDS_FILE"

# Wait a moment and verify the process is still running
sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${RED}Error: Backend process failed to start. Check logs: $LOGS_DIR/backend.log${NC}"
    tail -20 "$LOGS_DIR/backend.log" 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID) on port 8000${NC}"
echo -e "${YELLOW}  Logs: $LOGS_DIR/backend.log${NC}\n"
cd "$SCRIPT_DIR"

# Step 4: Start Background Worker
echo -e "${BLUE}[4/4] Starting Background Worker...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if run_worker.py exists, otherwise try alternative worker command
if [ -f "run_worker.py" ]; then
    WORKER_CMD="uv run run_worker.py"
elif [ -f "run_agent_background.py" ]; then
    WORKER_CMD="uv run dramatiq run_agent_background"
else
    echo -e "${YELLOW}Warning: No worker script found, trying default...${NC}"
    WORKER_CMD="uv run dramatiq run_agent_background"
fi

$WORKER_CMD > "$LOGS_DIR/worker.log" 2>&1 &
WORKER_PID=$!
echo "$WORKER_PID" >> "$PIDS_FILE"

# Wait a moment and verify the process is still running
sleep 2
if ! kill -0 "$WORKER_PID" 2>/dev/null; then
    echo -e "${RED}Error: Worker process failed to start. Check logs: $LOGS_DIR/worker.log${NC}"
    tail -20 "$LOGS_DIR/worker.log" 2>/dev/null || true
    echo -e "${YELLOW}Note: Worker may require additional configuration. Continuing without worker...${NC}"
else
echo -e "${GREEN}✓ Worker started (PID: $WORKER_PID)${NC}"
echo -e "${YELLOW}  Logs: $LOGS_DIR/worker.log${NC}\n"
fi
cd "$SCRIPT_DIR"

# Wait a moment for services to initialize
sleep 2

# Display status
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "${BLUE}Services:${NC}"
echo -e "  • Redis:        ${GREEN}Running${NC} (Docker)"
if [ "$IS_PRODUCTION_MODE" = true ]; then
    echo -e "  • Frontend:     ${GREEN}Running${NC} (PID: $FRONTEND_PID) - PRODUCTION mode - http://localhost:3000"
else
    echo -e "  • Frontend:     ${GREEN}Running${NC} (PID: $FRONTEND_PID) - DEVELOPMENT mode - http://localhost:3000"
fi
echo -e "  • Backend:      ${GREEN}Running${NC} (PID: $BACKEND_PID) - http://localhost:8000"
if [ -n "$WORKER_PID" ] && kill -0 "$WORKER_PID" 2>/dev/null; then
echo -e "  • Worker:       ${GREEN}Running${NC} (PID: $WORKER_PID)"
else
    echo -e "  • Worker:       ${YELLOW}Not running${NC}"
fi
echo -e ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  • Frontend:     $LOGS_DIR/frontend.log"
echo -e "  • Backend:      $LOGS_DIR/backend.log"
echo -e "  • Worker:       $LOGS_DIR/worker.log"
echo -e ""
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  • View logs:    tail -f $LOGS_DIR/*.log"
echo -e "  • Stop all:     ./stop.sh"
echo -e "  • Apply migrations: python3 apply_migrations.py"
echo -e ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e ""

# Function to tail logs (optional)
tail_logs() {
    echo -e "${BLUE}Tailing logs (Ctrl+C to stop tailing, services will continue)...${NC}"
    tail -f "$LOGS_DIR/frontend.log" "$LOGS_DIR/backend.log" "$LOGS_DIR/worker.log" 2>/dev/null || true
}

# Check if user wants to tail logs
if [ "$1" == "--logs" ] || [ "$1" == "-l" ]; then
    tail_logs
elif [ "$1" == "--migrate" ] || [ "$1" == "-m" ]; then
    # Already ran migrations, continue with normal startup
    :
else
    # Keep script running and wait for interrupt
    while true; do
        # Check if processes are still running
        if [ -f "$PIDS_FILE" ]; then
            all_running=true
            while read pid; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    all_running=false
                    echo -e "${RED}Warning: Process $pid has stopped${NC}"
                fi
            done < "$PIDS_FILE"
            
            if [ "$all_running" = false ]; then
                echo -e "${YELLOW}Some services have stopped. Check logs for details.${NC}"
            fi
        fi
        sleep 5
    done
fi

