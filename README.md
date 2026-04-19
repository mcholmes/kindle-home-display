# Kindle Home Display

## Description

This project repurposes a Kindle as a home display that can go several weeks without charging.
It requires Python 3.11+ and is designed to run on a Raspberry Pi.

:warning: TODO: picture of the dashboard

## Features

- Calendar (Google Calendar)
- Tasks (Todoist)
- Weather, soon (OpenWeatherMap)
- **Low Battery Overlay**: The Kindle will display its battery percentage in the corner when it drops below 10%.

## Installation & usage

[Hatch](https://hatch.pypa.io/latest/) is recommended.

### Server Setup (Raspberry Pi)

1. Install system dependencies on the Pi (one-time):
   ```
   sudo apt install python3-pil python3-venv
   ```
2. Place `config.toml`, `api_keys.json`, and `credentials_service.json` in `~/server/` on the Pi (see [Configuration](#configuration) below)
3. Create the venv on the Pi (one-time, picks up system Pillow):
   ```
   cd server && make setup-venv
   ```
4. Deploy from your dev machine (builds, pushes, installs into venv, and restarts):
   ```
   make deploy
   ```

Other useful targets (run from `server/`):
```
make build              # build .whl locally
make push               # scp .whl to Pi
make install            # pip install on Pi
make start / make stop  # start/stop server on Pi
make restart            # stop + start
make status             # check if server is running
make logs               # print server logs from Pi
make ssh                # open shell on Pi in server dir
```

:warning: TODO: publish builds as downloadable releases.

### Configuration

The server is configured using a TOML file (`config.toml`). This is documented in [CONFIG.md](server/CONFIG.md).

#### Required API Credentials

##### Google Calendar

- You need a Google Cloud service account credentials file (`credentials_service.json`)
- The service account must have access to the calendars you want to display
- Calendar IDs can be found in Google Calendar settings under "Integrate calendar"

##### Todoist

- You need a Todoist API key (stored in `api_keys.json`)
- Project ID can be found in the URL when viewing a project in Todoist web interface

### Device Setup (Kindle)

1. Jailbreak your Kindle, using any method (I used LanguageBreak)
2. Install KUAL and a terminal emulator like [KTerm](https://www.mobileread.com/forums/showthread.php?t=277427) to find your Kindle's IP address.
3. Configure your Kindle environment variables in `device/src/local/env.sh` before deploying:
   - `DASHBOARD_URL`: Point this to your server (e.g. `http://<PI_IP>:8000/dashboard`)
   - `TIMEZONE`: Set your timezone (e.g. `Europe/London`)
   - `REFRESH_SCHEDULE`: Cron schedule for waking up to fetch updates.
4. From your development machine, ensure your `~/.ssh/config` has a `kindle` host entry.
5. Deploy the scripts and compiled binaries to the Kindle (from the `device/` directory):
   ```bash
   make deploy
   ```
   
Other useful targets (run from `device/`):
```bash
make deploy             # build, push, stop, and start the client
make status             # check if the dashboard process is running
make test               # run shell tests and rust unit tests
make format             # auto-format all shell scripts
make start / make stop  # start/stop the dashboard script remotely
make ssh                # open shell on the Kindle
make print-logs         # tail logs from the Kindle
```

## License

This project is licensed under the [MIT License](LICENSE).

## Credits

This project was inspired by and builds upon the work of several excellent projects:

- [kindle-dash](https://github.com/pascalw/kindle-dash) by Pascal Widdershoven
- [life-dashboard](https://github.com/davidhampgonsalves/life-dashboard) by David Hamp-Gonsalves
- [Building an E-ink Weather Display](https://matthealy.com/kindle) by Matt Healy
- [Building eInk Weather Display for Our Home](https://kimmo.blog/posts/7-building-eink-weather-display-for-our-home/) by Kimmo Brunfeldt
