# Makefile for server project
# Replaces Hatch scripts with make targets

.PHONY: install server test test-cov cov-report cov types perf clean help

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development
run-dev:
	uv sync
	fastapi run src/server/main.py --host 0.0.0.0 --port 8000

# Build & version management
bump-patch:
	uv version --bump patch

bump-minor:
	uv version --bump minor

bump-major:
	uv version --bump major

build:
	uv build --wheel

clean: ## Clean up generated files
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Deployment
PI_HOST=rpi@raspberrypi.local
PI_DIR=/home/rpi/server
CRED_FILES=config.toml credentials_service.json .env

copy-package:
	scp dist/*.whl $(PI_HOST):$(PI_DIR)

copy-creds:
	scp $(CRED_FILES) $(PI_HOST):$(PI_DIR)/

install-remote:
	ssh $(PI_HOST) "cd $(PI_DIR) && uv venv && source .venv/bin/activate && uv pip install --upgrade server-*.whl"

deploy: copy-package copy-creds install-remote


# Testing
test: ## Run tests with pytest
	uv run pytest tests

test-cov: ## Run tests with coverage
	uv run coverage run -m pytest tests

cov-report: ## Generate coverage report
	uv run coverage report

cov-html: ## Generate HTML coverage report
	uv run coverage html

cov: test-cov cov-report ## Run tests with coverage and generate report

types: ## Run type checking with mypy
	uv run mypy src/server tests

lint: ## Run linting with ruff
	uv run ruff check src tests

lint-fix: ## Run linting with ruff and fix issues
	uv run ruff check --fix src tests

format: ## Format code with ruff
	uv run ruff format src tests

format-check: ## Check code formatting
	uv run ruff format --check src tests

profile: ## Run performance profiling  
	PYTHONPATH=src uv run python -m cProfile -o program.prof -m server.main $(ARGS) && uv run tuna program.prof

