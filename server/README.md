# Kindle Home Display Server

A FastAPI server that collects data from various APIs (calendar, tasks, weather) and renders it as an image for display on Kindle e-reader devices.

- [Kindle Home Display Server](#kindle-home-display-server)
  - [Quick Start with Docker (Recommended)](#quick-start-with-docker-recommended)
  - [Development Setup](#development-setup)
  - [Usage](#usage)
    - [Command Line Interface](#command-line-interface)
    - [Docker Usage](#docker-usage)
  - [Configuration](#configuration)
  - [API Endpoints](#api-endpoints)
  - [License](#license)

## Quick Start with Docker (Recommended)

The easiest way to run the server is using Docker Compose:

```shell
# Clone the repository
git clone https://github.com/mcholmes/kindle-home-display.git
cd kindle-home-display/server

# Configure your credentials (see Configuration section)
cp config.docker.toml config.toml
# Edit config.toml with your settings

# Start the server
docker-compose up --build
```

The server will be available at `http://localhost:8000`

## Development Setup

For local development using `uv` (recommended):

```console
# Install dependencies
uv sync

# Install the package in development mode
uv pip install -e .

# Run the server
kindle-server --log-to-console start
```

Alternative using pip:

```shell
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run the server
kindle-server --log-to-console start
```

## Usage

### Command Line Interface

The server provides a `kindle-server` console command with the following options:

```shell
# Start the server
kindle-server start

# Start with console logging
kindle-server --log-to-console start

# Run once to generate image without starting server
kindle-server once

# View server logs
kindle-server logs

# Get help
kindle-server --help
```

### Docker Usage

```shell
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down

# Rebuild and start
docker-compose up --build
```

## Configuration

1. Copy the example configuration:

   ```shell
   cp config.docker.toml config.toml
   ```

2. Edit `config.toml` with your settings:
   - Server host/port configuration
   - Calendar IDs and credentials
   - Task project IDs
   - Image dimensions and styling

3. Set up credential files:
   - `api_keys.json` - API keys for weather services
   - `credentials_service.json` - Google Calendar service account credentials
   - `credentials_oauth.json` - OAuth credentials (if needed)

See `CONFIG.md` for detailed configuration options.

## API Endpoints

- `GET /` - Root endpoint, returns rendered dashboard image
- `GET /dashboard` - Same as root, returns the dashboard image
- `GET /health` - Health check endpoint
- `GET /logs` - View recent server logs

## License

`kindle-home-display-server` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
