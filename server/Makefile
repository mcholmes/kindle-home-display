# Server deployment to Raspberry Pi
# Mirrors the device/Makefile pattern: build locally, push to Pi, manage remotely.

# Pi SSH params -- should correspond to your .ssh/config or use user@host
REMOTE_HOST := rpi@raspberrypi.local
REMOTE_DIR := ~/server
REMOTE_VENV := $(REMOTE_DIR)/.venv
REMOTE_BIN := $(REMOTE_VENV)/bin/server

# Derived from __about__.py
VERSION := $(shell sed -n 's/^__version__ = "\(.*\)"/\1/p' src/server/__about__.py)
WHEEL := dist/server-$(VERSION)-py3-none-any.whl

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Build:"
	@echo "  build        Build .whl"
	@echo ""
	@echo "Deploy:"
	@echo "  push         Copy .whl to Pi"
	@echo "  setup-venv   Create/recreate venv on Pi (one-time)"
	@echo "  install      Install .whl on Pi (into venv)"
	@echo "  deploy       Build + push + install + restart"
	@echo ""
	@echo "Remote:"
	@echo "  start        Start server on Pi"
	@echo "  stop         Stop server on Pi"
	@echo "  restart      Stop + start"
	@echo "  status       Check if server is running"
	@echo "  ssh          Open shell on Pi in server dir"
	@echo "  logs         Print server logs from Pi"

# ---------- Build ----------

build:
	hatch build -t wheel
	@echo "Built $(WHEEL)"

# ---------- Deploy ----------

push: $(WHEEL)
	scp $(WHEEL) $(REMOTE_HOST):$(REMOTE_DIR)/
	@echo "Pushed $(WHEEL) to $(REMOTE_HOST):$(REMOTE_DIR)"

setup-venv:
	ssh $(REMOTE_HOST) "\
		rm -rf $(REMOTE_VENV) && \
		python3 -m venv --system-site-packages $(REMOTE_VENV)"

install:
	ssh $(REMOTE_HOST) "\
		$(REMOTE_VENV)/bin/pip install --force-reinstall --no-deps $(REMOTE_DIR)/server-$(VERSION)-py3-none-any.whl && \
		$(REMOTE_VENV)/bin/pip install $(REMOTE_DIR)/server-$(VERSION)-py3-none-any.whl"

deploy: build push install restart
	@echo "Deployed v$(VERSION) and restarted."

# ---------- Remote management ----------

start:
	@ssh $(REMOTE_HOST) "cd $(REMOTE_DIR) && nohup $(REMOTE_BIN) start >> nohup.out 2>&1 < /dev/null &"
	@echo "Started."

stop:
	-@ssh $(REMOTE_HOST) "pkill -f 'server start' 2>/dev/null"
	@echo "Stopped."

restart: stop start

status:
	@ssh $(REMOTE_HOST) "pgrep -af 'server start' | grep -v pgrep || echo 'Not running.'"

ssh:
	ssh $(REMOTE_HOST) -t "cd $(REMOTE_DIR) && exec \$$SHELL"

logs:
	ssh $(REMOTE_HOST) "cat $(REMOTE_DIR)/data/server.log 2>/dev/null || echo 'No log file found.'"

.PHONY: help build push setup-venv install deploy start stop restart status ssh logs
