# AGENTS.md

## Project overview

Kindle e-ink home dashboard. Two independent components:

- **`server/`** -- Python/FastAPI app (runs on Raspberry Pi). Fetches Google Calendar + Todoist data, renders a grayscale PNG, serves it at `/dashboard`.
- **`device/`** -- Shell scripts + small Rust binary (runs on jailbroken Kindle PW3). Periodically wakes from suspend, fetches the PNG, displays it via `eips`, sleeps again.

## Server commands (run from `server/`)

All Python tooling goes through [Hatch](https://hatch.pypa.io/) (uses **uv** as installer internally):

```
hatch run test              # pytest
hatch run test-cov          # pytest + coverage
hatch run types             # mypy
hatch fmt                   # ruff lint + format
hatch run server start      # run FastAPI dev server (127.0.0.1:8000)
hatch run server once       # render a single dashboard image to disk
```

Deployment to Raspberry Pi via Makefile:

```
make deploy                 # build + push + install + restart (full deploy)
make build                  # build .whl locally
make push                   # scp .whl to Pi
make install                # pip install on Pi
make start / make stop      # start/stop server on Pi via SSH
make status                 # check if server is running
make logs                   # print server logs from Pi
make ssh                    # open shell on Pi in server dir
```

There is no Python CI -- tests, types, and linting are local-only. CI only runs shell linting.

## Device commands (run from `device/`)

```
make dist                   # build everything (cross-compile Rust + copy scripts)
make push                   # scp dist/ to Kindle
make format                 # shfmt -i 4
make ssh                    # SSH into Kindle
make start / make stop      # start/stop dashboard on Kindle via SSH
```

Rust binary (`next-wakeup`) cross-compiles to `armv7-unknown-linux-musleabi` using `arm-linux-gnueabihf-ld` as linker. Requires the ARM musl target and linker installed locally.

## Key constraints

- **Python 3.11 minimum** -- targets Raspberry Pi. Use modern syntax: `X | Y` union types (not `Optional`/`Union`), `match/case`, `tomllib` (not the `toml` package), `Self` return types on classmethods.
- **Pillow is installed via apt on the Pi** (`sudo apt install python3-pil`), not pip, to avoid compiling C extensions on ARM. The pip install must have access to system site-packages.
- **Use pendulum for all datetime logic** -- the server uses `pendulum` (not stdlib `datetime`) for timezone handling, date arithmetic, and formatting. Use `pendulum.now()`, `pendulum.datetime()`, `.add()`, `.subtract()`, `.start_of()`, `.format()` etc. The `Activity` model stores stdlib `date` and `time` fields for Pydantic, but all construction and manipulation should go through pendulum. External libraries (e.g. `gcsa`) may still return stdlib `datetime` objects -- the `datetime_to_date`/`datetime_to_time` helpers in `activity.py` handle both types.
- **Shell scripts target BusyBox ash**, not bash. ShellCheck config: `shell=busybox`. Do not use bash-only syntax.
- **Ruff config is extensive** -- `ruff_defaults.toml` (534 lines) is extended by `pyproject.toml` which adds `PTH` rules (prefer `pathlib` over `os.path`). Relative imports are banned.
- **Line length: 120 characters** (Ruff config).
- **shfmt indentation mismatch**: `device/Makefile` uses `-i 4`, CI uses `-i 2`. The Makefile target is what you should use locally.

## Configuration and secrets

- Server config: `server/config.toml` (Pydantic-validated, supports TOML/YAML/JSON)
- API keys: `server/api_keys.json` (gitignored)
- Google Calendar: service account `credentials_service.json` (gitignored)
- Device config: `device/src/local/env.sh` (cron schedule, timezone, battery thresholds)

## Testing

- Server tests live in `server/tests/`. Coverage exists for `activity.py` and `config.py`. No tests for rendering, calendar, todoist, or API routes.
- Device has a minimal shell test in `device/tests/test_logging.sh`.

## CI

GitHub Actions runs only `sh-checker` (ShellCheck + shfmt) on shell scripts in `device/`. No Python CI exists.
