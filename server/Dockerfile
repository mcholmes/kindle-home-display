# Stage 1: Generate requirements.txt from uv.lock
FROM --platform=$BUILDPLATFORM python:3.12-slim AS uv-exporter
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /tmp
COPY pyproject.toml uv.lock ./
RUN uv export --format requirements-txt --no-dev > requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements from the first stage
COPY --from=uv-exporter /tmp/requirements.txt ./

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and project files
COPY src/ ./src/
COPY pyproject.toml ./
COPY ruff_defaults.toml ./

# Install the package itself (creates the console script entry point)
RUN pip install --no-cache-dir -e .

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser
RUN chown -R appuser:appuser /app
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["kindle-server", "--log-to-console", "start"]