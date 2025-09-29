# Makefile for server project
# Replaces Hatch scripts with make targets

.PHONY: install server test test-cov cov-report cov types perf clean help

# Variables
PYTHON := .venv/bin/python
PYTEST_ARGS ?= tests
MYPY_ARGS ?= src/server tests

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies and project in development mode
	uv venv --seed
	uv pip install -e .
	uv pip install coverage[toml] pytest mypy tuna

server: ## Run the server with optional args (use ARGS="--help" for options)
	$(PYTHON) -m server $(ARGS)

test: ## Run tests with pytest
	$(PYTHON) -m pytest $(PYTEST_ARGS)

test-cov: ## Run tests with coverage
	$(PYTHON) -m coverage run -m pytest $(PYTEST_ARGS)

cov-report: ## Generate coverage report
	-$(PYTHON) -m coverage combine
	$(PYTHON) -m coverage report

cov: test-cov cov-report ## Run tests with coverage and generate report

types: ## Run type checking with mypy
	$(PYTHON) -m mypy --install-types --non-interactive $(MYPY_ARGS)

perf: ## Run performance profiling
	$(PYTHON) -mcProfile -o program.prof src/server/__main__.py $(ARGS) && $(PYTHON) -m tuna program.prof

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