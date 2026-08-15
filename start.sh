#!/usr/bin/env bash
# start.sh - Single-command native startup for Fake News Detection

# Determine project root dynamically
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Track background process IDs
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function to gracefully terminate child processes
cleanup() {
    echo -e "\nShutting down FND..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    exit 0
}

# Trap signals for reliable cleanup
trap cleanup SIGINT SIGTERM EXIT

# Verify Python virtual environment
if [ ! -d "$DIR/.venv" ]; then
    echo "ERROR: Python virtual environment not found at $DIR/.venv"
    echo "Please create it and install requirements:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Verify uvicorn exists
if [ ! -f "$DIR/.venv/bin/uvicorn" ]; then
    echo "ERROR: uvicorn not found in $DIR/.venv/bin/uvicorn"
    echo "Please ensure you have installed the requirements:"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Verify Node.js and npm
if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: node is not installed or not in PATH."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed or not in PATH."
    exit 1
fi

# Verify lsof
if ! command -v lsof >/dev/null 2>&1; then
    echo "ERROR: 'lsof' command not found."
    echo "Please install lsof to allow port checking (e.g. 'sudo apt-get install lsof' or 'brew install lsof')."
    exit 1
fi

# Check if ports are already occupied
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "ERROR: Port 8000 is currently occupied. Please free this port for the backend."
    exit 1
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "ERROR: Port 5173 is currently occupied. Please free this port for the frontend."
    exit 1
fi

# Create runtime directory for logs
mkdir -p "$DIR/.runtime"
BACKEND_LOG="$DIR/.runtime/backend.log"
FRONTEND_LOG="$DIR/.runtime/frontend.log"

echo "Starting FND services... (Logs saved to .runtime/)"

# Start FastAPI backend
"$DIR/.venv/bin/python" -m uvicorn backend.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --app-dir "$DIR" > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

# Wait for backend health
echo -n "Waiting for backend..."
BACKEND_READY=false
for i in {1..30}; do
    if "$DIR/.venv/bin/python" -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        BACKEND_READY=true
        break
    fi
    # If process died prematurely
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Handle backend failure
if [ "$BACKEND_READY" = false ]; then
    echo "ERROR: Backend failed to start!"
    echo "--- BACKEND LOG ---"
    cat "$BACKEND_LOG"
    exit 1
fi

# Start Frontend
cd "$DIR/frontend" || exit 1
npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend port 5173
echo -n "Waiting for frontend..."
FRONTEND_READY=false
for i in {1..30}; do
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
        FRONTEND_READY=true
        break
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Handle frontend failure
if [ "$FRONTEND_READY" = false ]; then
    echo "ERROR: Frontend failed to start!"
    echo "--- FRONTEND LOG ---"
    cat "$FRONTEND_LOG"
    exit 1
fi

# Print clean startup screen
cat << "EOF"
========================================
                 FND
          Fake News Detection
========================================

✓ Backend ready
✓ Frontend ready

========================================
             FND IS READY
========================================

Web UI:
http://localhost:5173

API:
http://localhost:8000

Health:
http://localhost:8000/health

Press Ctrl+C to stop.
EOF

# Wait indefinitely for the trap to catch SIGINT/SIGTERM
wait