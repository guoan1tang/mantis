#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.server.pid"

if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "Stopping server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null
        sleep 1
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            kill -9 "$SERVER_PID" 2>/dev/null
        fi
        echo "Server stopped."
    else
        echo "Server process not running."
    fi
    rm -f "$PID_FILE"
else
    echo "No PID file found, searching for processes..."
    PIDS=$(pgrep -f "agent_proxy.*--server" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "$PIDS" | while read -r pid; do
            echo "  Stopping PID $pid..."
            kill "$pid" 2>/dev/null || true
        done
        echo "Done."
    else
        echo "No server processes found."
    fi
fi

echo "Clearing system proxy..."
networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
