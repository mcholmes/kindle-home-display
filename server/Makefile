# Makefile for server project
# Replaces Hatch scripts with make targets

.PHONY: install server test test-cov cov-report cov types perf clean help

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies and project in development mode
	uv sync
	uv pip install -e .

# Python development tasks (using uv run)
server: ## Run the server with optional args (use ARGS="--help" for options)
	uv run uvicorn server.main:app --host 0.0.0.0 --port 8000 $(ARGS)

server-dev: ## Run the server in development mode with auto-reload
	uv run uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload $(ARGS)

generate-image: ## Generate dashboard image once
	uv run python generate_image.py

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

# Docker targets
docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f server

docker-dev: ## Start development server with hot reload
	@echo "Dev server removed from Docker. Use 'make server-dev' instead."

docker-shell: ## Shell into running Docker container
	docker-compose exec server bash

docker-health: ## Check Docker container health
	curl -f http://localhost:8000/health || echo "Health check failed"