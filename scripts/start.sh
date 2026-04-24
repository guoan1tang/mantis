#!/usr/bin/env bash
set -e

PROXY_PORT=8080
API_PORT=9080

# Free ports if occupied by old processes
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

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Start Electron (which manages Python server + Vite)
echo "Launching desktop app..."
cd "$ROOT_DIR/src/web"
npm run electron:dev
