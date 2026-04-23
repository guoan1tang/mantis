#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.server.pid"
PROXY_PORT=8080
API_PORT=9080

cleanup() {
    echo ""
    echo "Shutting down..."
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            kill "$SERVER_PID" 2>/dev/null
            echo "  Server (PID $SERVER_PID) stopped."
        fi
        rm -f "$PID_FILE"
    fi
    networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
    networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
    echo "Done."
    exit 0
}

trap cleanup INT TERM

# Free ports if occupied
if lsof -i :$PROXY_PORT > /dev/null 2>&1; then
    echo "Port $PROXY_PORT in use, freeing..."
    lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -i :$API_PORT > /dev/null 2>&1; then
    echo "Port $API_PORT in use, freeing..."
    lsof -ti:$API_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start Python server
echo "Starting Agent Proxy server..."
cd "$ROOT_DIR"
python3 -m agent_proxy --server --port $PROXY_PORT &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "  Server PID: $SERVER_PID"

# Wait for API ready (max 15s)
echo "Waiting for server..."
READY=false
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:$API_PORT/health" > /dev/null 2>&1; then
        READY=true
        break
    fi
    sleep 0.5
done

if [ "$READY" = false ]; then
    echo "Server failed to start within 15 seconds."
    kill "$SERVER_PID" 2>/dev/null
    rm -f "$PID_FILE"
    exit 1
fi

echo "Server ready at http://127.0.0.1:$API_PORT"
echo ""

# Start Electron frontend
echo "Launching desktop app..."
cd "$ROOT_DIR/src/web"
npm run electron:dev
