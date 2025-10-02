# Kindle Home Display Server

A FastAPI server that collects data from various APIs (calendar, tasks, weather) and renders it as an image for display on Kindle e-reader devices.

## Prerequisites

`make` and `uv`.

## Usage

`./run.sh` starts the server on `localhost:8000`.

## Configuration

Edit `config.toml` with your settings:

- Calendar IDs and credentials
- Task project IDs
- Image dimensions and styling

Set up credential files:

- `.env` - API keys for weather services
- `credentials_service.json` - Google Calendar service account credentials

See `CONFIG.md` for detailed configuration options.

## API Endpoints

- `GET /` - Root endpoint, returns rendered dashboard image
- `GET /dashboard` - Same as root, returns the dashboard image
- `GET /health` - Health check endpoint

## License

`kindle-home-display-server` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
