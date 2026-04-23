# One-Click Installation Design

**Goal:** 用户从 GitHub clone 后，只需 `make install && make start` 即可运行完整应用

**Architecture:** Makefile 作为入口，shell 脚本处理依赖安装和进程管理。Python 后端以 `--server` 模式启动，Electron 前端以 `electron:dev` 模式启动。

**Tech Stack:** Makefile, bash, Python (pip), Node.js (npm)

---

## Makefile (根目录)

```makefile
.PHONY: install start stop build clean

PYTHON := python3
NODE := node
NPM := npm

install: check-env python-deps npm-deps mitmproxy-cert
	@echo "✅ All dependencies installed."

check-env:
	@$(PYTHON) -c "import sys; sys.exit(0) if sys.version_info >= (3,12) else sys.exit('Python >= 3.12 required')"
	@$(NODE) -v > /dev/null 2>&1 || (echo "Node.js is required" && exit 1)

python-deps:
	@echo "📦 Installing Python dependencies..."
	$(PYTHON) -m pip install -e ".[dev]"

npm-deps:
	@echo "📦 Installing Node.js dependencies..."
	cd src/web && $(NPM) install

mitmproxy-cert:
	@echo "🔐 Initializing mitmproxy CA certificate..."
	mitmdump --listen-port 0 > /dev/null 2>&1 & sleep 2; kill $$! 2>/dev/null || true
	@echo "CA cert ready at: ~/.mitmproxy/mitmproxy-ca-cert.pem"

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

## scripts/start.sh

- 先检查 Python 后端端口是否空闲
- 启动 `python -m agent_proxy --server --no-system-proxy` (后台)
- 轮询等待 API 就绪 (最多 15 秒)
- 启动 `npm run electron:dev` (前台)
- 捕获 SIGINT/SIGTERM，优雅关闭后端进程

## scripts/stop.sh

- 查找并停止 start.sh 启动的 Python 后端进程
- 清理系统代理设置
