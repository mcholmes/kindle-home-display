# Stage 1: Generate requirements.txt from uv.lock
FROM --platform=$BUILDPLATFORM python:3.13-slim AS uv-exporter
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /tmp
COPY pyproject.toml uv.lock ./
RUN uv export --format requirements-txt --no-dev --no-hashes --no-editable > requirements.txt

# Stage 2: Base image with common dependencies
FROM python:3.13-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements from the first stage
COPY --from=uv-exporter /tmp/requirements.txt ./

# Copy project files needed for dependency resolution
COPY pyproject.toml ./

# Install dependencies using pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source code and remaining project files
COPY src/ ./src/
COPY ruff_defaults.toml ./

# Install the package itself (non-editable for production base)
RUN pip install --no-cache-dir .

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -s /bin/bash appuser
RUN chown -R appuser:appuser /app
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser

# Stage 3: Production image
FROM base AS production

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]