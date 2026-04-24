#!/usr/bin/env bash
set -e

echo "Stopping all processes..."

# Kill electron and python proxy processes
pkill -f "electron.*mantis" 2>/dev/null || true
pkill -f "agent_proxy.*--server" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# Clear system proxy
echo "Clearing system proxy..."
networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
echo "Done."
