# Development Setup

This project now uses `uv` for dependency management and `make` for task automation (replacing Hatch).

## Prerequisites

Install `uv`:

```bash
brew install uv
```

## Setup

1. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

1. Install the project and development dependencies:

```bash
make install
```

## Available Commands

Run `make help` to see all available targets:

- `make server` - Run the server (use `make server ARGS="--help"` for options)
- `make test` - Run tests
- `make test-cov` - Run tests with coverage
- `make cov` - Run tests with coverage and generate report
- `make types` - Run type checking
- `make perf` - Run performance profiling
- `make clean` - Clean up generated files

## Migration from Hatch

The following Hatch commands have been replaced:

| Old Hatch Command | New Make Command |
|-------------------|------------------|
| `hatch run server` | `make server` |
| `hatch run test` | `make test` |
| `hatch run test-cov` | `make test-cov` |
| `hatch run cov` | `make cov` |
| `hatch run types` | `make types` |
| `hatch run perf` | `make perf` |