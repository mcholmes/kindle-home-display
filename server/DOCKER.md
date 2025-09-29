# Docker Setup for Kindle Home Display Server

This directory contains the Docker configuration for the Kindle Home Display Server, allowing you to easily run the application with any Python version and simplified dependency management.

## Features

- 🐍 **Modern Python Runtime**: Uses Python 3.12 (easily configurable)
- 📦 **UV Package Manager**: Fast, reliable dependency resolution
- 🔒 **Security**: Runs as non-root user
- 🏥 **Health Checks**: Built-in health monitoring
- 📁 **Volume Mounts**: Persistent data and easy configuration
- 🔄 **Development Mode**: Hot reload support

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- Your configuration files ready (see Configuration section)

### 2. Build and Run

```bash
# Build and start the server
docker-compose up --build

# Run in the background
docker-compose up -d --build

# View logs
docker-compose logs -f server
```

The server will be available at `http://localhost:8000`

### 3. Development Mode

For development with hot reload:

```bash
# Start development server
docker-compose --profile dev up server-dev

# This runs on port 8001 with hot reload enabled
```

## Configuration

### Required Files

Create these files in the server directory before running:

1. **`config.toml`** - Main configuration (use `config.docker.toml` as template)
2. **`api_keys.json`** - API keys for external services
3. **`credentials_service.json`** - Google Calendar service account credentials  
4. **`credentials_oauth.json`** - Google Calendar OAuth credentials (if needed)

### Configuration Template

Copy and modify `config.docker.toml`:

```bash
cp config.docker.toml config.toml
# Edit config.toml with your settings
```

Key Docker-specific settings in `config.toml`:
- `host = "0.0.0.0"` - Listen on all interfaces
- `server_dir = "/app/data/"` - Use mounted data directory
- `creds = "/app/credentials_service.json"` - Path to mounted credentials

### Example API Keys File

Create `api_keys.json`:

```json
{
  "openweather": {
    "api_key": "your-openweather-api-key"
  },
  "todoist": {
    "api_key": "your-todoist-api-key"
  }
}
```

## Docker Commands

### Basic Operations

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# Stop services  
docker-compose down

# View logs
docker-compose logs -f server

# Restart service
docker-compose restart server
```

### Health Check

```bash
# Check health status
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-01-01T12:00:00"}
```

### Development

```bash
# Shell into running container
docker-compose exec server bash

# Run tests in container
docker-compose exec server uv run pytest

# Install additional packages
docker-compose exec server uv add package-name
```

## Volumes

The Docker setup uses these volume mounts:

- `./config.toml:/app/config.toml:ro` - Configuration (read-only)
- `./api_keys.json:/app/api_keys.json:ro` - API keys (read-only)  
- `./credentials_service.json:/app/credentials_service.json:ro` - Google credentials (read-only)
- `./data:/app/data` - Persistent data (logs, generated images)

## Environment Variables

You can override settings with environment variables:

```bash
# In docker-compose.yml or .env file
PYTHONPATH=/app/src
LOG_LEVEL=DEBUG
```

## Upgrading Python Version

To upgrade the Python version:

1. Edit `Dockerfile`:
   ```dockerfile
   FROM python:3.13-slim  # Change version here
   ```

2. Rebuild:
   ```bash
   docker-compose build --no-cache
   ```

## Production Deployment

### Using Docker Compose

1. Copy production configuration:
   ```bash
   cp config.docker.toml config.prod.toml
   # Edit config.prod.toml for production
   ```

2. Create production compose file:
   ```yaml
   # docker-compose.prod.yml
   services:
     server:
       build: .
       ports:
         - "80:8000"  # or behind reverse proxy
       volumes:
         - ./config.prod.toml:/app/config.toml:ro
         - ./api_keys.json:/app/api_keys.json:ro
         - ./credentials_service.json:/app/credentials_service.json:ro
         - /var/lib/kindle-display:/app/data
       restart: always
   ```

3. Deploy:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Using Docker Run

```bash
docker build -t kindle-server .

docker run -d \
  --name kindle-server \
  -p 8000:8000 \
  -v $(pwd)/config.toml:/app/config.toml:ro \
  -v $(pwd)/api_keys.json:/app/api_keys.json:ro \
  -v $(pwd)/credentials_service.json:/app/credentials_service.json:ro \
  -v kindle-data:/app/data \
  --restart unless-stopped \
  kindle-server
```

## Troubleshooting

### Common Issues

1. **Permission denied errors**:
   ```bash
   # Fix file permissions
   chmod 644 config.toml api_keys.json credentials_service.json
   ```

2. **Health check failures**:
   ```bash
   # Check if server is starting properly
   docker-compose logs server
   
   # Test health endpoint manually
   docker-compose exec server curl http://localhost:8000/health
   ```

3. **Configuration not found**:
   ```bash
   # Verify files are mounted correctly
   docker-compose exec server ls -la /app/
   ```

### Debugging

```bash
# Run with debug logging
docker-compose exec server uv run server start --log-level DEBUG --log-to-console

# Interactive shell in container
docker-compose exec server bash

# Check running processes
docker-compose exec server ps aux
```

## Migration from Non-Docker Setup

1. **Backup existing data**:
   ```bash
   cp server.log dashboard.png /backup/
   ```

2. **Update configuration**:
   - Change `host` from `127.0.0.1` to `0.0.0.0`
   - Update `server_dir` to `/app/data/`
   - Update credential paths to `/app/credentials_*.json`

3. **Test migration**:
   ```bash
   docker-compose up server
   # Verify dashboard works: http://localhost:8000/dashboard
   ```

## Monitoring

The Docker setup includes health checks and structured logging:

- Health endpoint: `GET /health`  
- Server logs: `GET /logs/server`
- Container logs: `docker-compose logs server`
- Health status: `docker-compose ps` (shows healthy/unhealthy)

For production monitoring, consider integrating with:
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)  
- Docker logging drivers