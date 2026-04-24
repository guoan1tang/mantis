.PHONY: install start stop build clean

PYTHON := python3
NODE := node
NPM := npm
VENV := .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

install: check-env python-deps npm-deps mitmproxy-cert
	@echo "All dependencies installed."

check-env:
	@$(PYTHON) -c "import sys; sys.exit(0) if sys.version_info >= (3,12) else sys.exit('Error: Python >= 3.12 required, found ' + sys.version.split()[0])"
	@$(NODE) -v > /dev/null 2>&1 || (echo "Error: Node.js is required but not found" && exit 1)

python-deps: $(VENV)/bin/activate
	@echo "Installing Python dependencies..."
	@echo "Clearing system proxy before install..."
	@networksetup -setwebproxystate Wi-Fi off 2>/dev/null || true
	@networksetup -setsecurewebproxystate Wi-Fi off 2>/dev/null || true
	@unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy 2>/dev/null; PIP_CONFIG_FILE=$$(pwd)/pip.conf $(VENV_PIP) install -e ".[dev]"

$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)

npm-deps:
	@echo "Installing Node.js dependencies..."
	cd src/web && $(NPM) install

mitmproxy-cert:
	@echo "Initializing mitmproxy CA certificate..."
	@mkdir -p ~/.mitmproxy
	@$(VENV)/bin/mitmdump --listen-port 0 > /dev/null 2>&1 & PID=$$!; sleep 2; kill $$PID 2>/dev/null || true
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
	rm -rf build/ dist/ *.egg-info src/*.egg-info $(VENV)/
	cd src/web && rm -rf node_modules/ dist/ build/ || true
