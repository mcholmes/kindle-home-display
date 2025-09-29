#!/bin/bash
# Entry point for the Kindle Home Display Server
# This script runs the server directly without needing to install it as a package

# Navigate to the server directory
cd "$(dirname "$0")" || exit 1

# Set PYTHONPATH to include src directory so Python can find server modules
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Run the CLI directly
exec uv run python -c "from server.cli import cli; cli()" "$@"