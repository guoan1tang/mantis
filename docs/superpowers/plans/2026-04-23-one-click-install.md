# One-Click Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户从 GitHub clone 后，只需 `make install && make start` 即可运行完整应用

**Architecture:** Makefile 作为统一入口，shell 脚本处理依赖安装、进程启动和优雅退出。Python 后端以 `--server` 模式启动，Electron 前端负责桌面 GUI。

---

### Task 1: Makefile

**Files:**
- Create: `Makefile` (project root)

- [ ] **Step 1: Create Makefile**

```makefile
.PHONY: install start stop build clean

PYTHON := python3
NODE := node
NPM := npm

install: check-env python-deps npm-deps mitmproxy-cert
	@echo "✅ All dependencies installed."

check-env:
	@$(PYTHON) -c "import sys; sys.exit(0) if sys.version_info >= (3,12) else sys.exit('Error: Python >= 3.12 required, found ' + sys.version.split()[0])"
	@$(NODE) -v > /dev/null 2>&1 || (echo "Error: Node.js is required but not found" && exit 1)

python-deps:
	@echo "📦 Installing Python dependencies..."
	$(PYTHON) -m pip install -e ".[dev]"

npm-deps:
	@echo "📦 Installing Node.js dependencies..."
	cd src/web && $(NPM) install

mitmproxy-cert:
	@echo "🔐 Initializing mitmproxy CA certificate..."
	@mkdir -p ~/.mitmproxy
	@mitmdump --listen-port 0 > /dev/null 2>&1 & PID=$$!; sleep 2; kill $$PID 2>/dev/null || true
	@if [ -f ~/.mitmproxy/mitmproxy-ca-cert.pem ]; then echo "  CA cert ready"; else echo "  Warning: cert may not have been generated"; fi

start:
	@bash scripts/start.sh

stop:
	@bash scripts/stop.sh

build:
	cd src/web && $(NPM) run electron:build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	cd src/web && rm -rf node_modules/ dist/ build/ || true
```

- [ ] **Step 2: Verify syntax**

Run: `make -n install` (dry-run, should print commands without executing)
Expected: Shows the sequence of commands for install

---

### Task 2: scripts/start.sh

**Files:**
- Create: `scripts/start.sh`

- [ ] **Step 1: Create the script**

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.server.pid"
PROXY_PORT=8080
API_PORT=9080

cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            kill "$SERVER_PID" 2>/dev/null
            echo "  Server (PID $SERVER_PID) stopped."
        fi
        rm -f "$PID_FILE"
    fi
    # Clear system proxy
    networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
    networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
    echo "✅ Done."
    exit 0
}

trap cleanup INT TERM

# Check if port is already in use
if lsof -i :$PROXY_PORT > /dev/null 2>&1; then
    echo "⚠️  Port $PROXY_PORT is already in use. Attempting to free..."
    lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -i :$API_PORT > /dev/null 2>&1; then
    echo "⚠️  Port $API_PORT is already in use. Attempting to free..."
    lsof -ti:$API_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start Python server in background
echo "🚀 Starting Agent Proxy server..."
cd "$ROOT_DIR"
python3 -m agent_proxy --server --port $PROXY_PORT &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "  Server PID: $SERVER_PID"

# Wait for API to be ready (max 15s)
echo "⏳ Waiting for server to be ready..."
READY=false
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:$API_PORT/health" > /dev/null 2>&1; then
        READY=true
        break
    fi
    sleep 0.5
done

if [ "$READY" = false ]; then
    echo "❌ Server failed to start within 15 seconds."
    echo "  Check logs above for errors."
    kill "$SERVER_PID" 2>/dev/null
    rm -f "$PID_FILE"
    exit 1
fi

echo "✅ Server ready at http://127.0.0.1:$API_PORT"
echo ""

# Start Electron frontend
echo "🖥️  Launching desktop app..."
cd "$ROOT_DIR/src/web"
npm run electron:dev
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/start.sh`

---

### Task 3: scripts/stop.sh

**Files:**
- Create: `scripts/stop.sh`

- [ ] **Step 1: Create the script**

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.server.pid"

if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "🛑 Stopping server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null
        sleep 1
        if kill -0 "$SERVER_PID" 2>/dev/null; then
            kill -9 "$SERVER_PID" 2>/dev/null
        fi
        echo "✅ Server stopped."
    else
        echo "Server process not running."
    fi
    rm -f "$PID_FILE"
else
    echo "No PID file found. Looking for agent-proxy processes..."
    PIDS=$(pgrep -f "agent_proxy.*--server" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "$PIDS" | while read pid; do
            echo "  Stopping PID $pid..."
            kill "$pid" 2>/dev/null || true
        done
        echo "✅ Done."
    else
        echo "No server processes found."
    fi
fi

# Clear system proxy
echo "🔓 Clearing system proxy..."
networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/stop.sh`

---

### Task 4: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with new installation instructions**

Replace the Installation and Usage sections with:

```markdown
## Installation

```bash
git clone https://github.com/xxx/mantis.git
cd mantis
make install
```

Requirements: Python >= 3.12, Node.js

## Usage

```bash
# Start desktop app (auto-launches proxy server)
make start

# Stop the server
make stop

# Build distributable
make build

# Clean up
make clean
```

### Manual Start (advanced)

```bash
# Start TUI mode
agent-proxy

# Start server mode only
agent-proxy --server --port 8080
```
```

---

### Task 5: Verify

- [ ] **Step 1: Dry-run Makefile**

Run: `make -n install`
Expected: Prints command sequence without executing

- [ ] **Step 2: Test start.sh syntax**

Run: `bash -n scripts/start.sh && echo "OK"`
Expected: `OK`

- [ ] **Step 3: Test stop.sh syntax**

Run: `bash -n scripts/stop.sh && echo "OK"`
Expected: `OK`
