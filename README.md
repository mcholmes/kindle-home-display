# Kindle Home Display

## Description

This project repurposes a Kindle as a home display that can go several weeks without charging.
It's implemented in Python 3.9 due to that being natively available on a Raspberry Pi 2.

:warning: TODO: picture of the dashboard

## Features

- Calendar (Google Calendar)
- Tasks (Todoist)
- Weather, soon (OpenWeatherMap)

## Installation & usage

[Hatch](https://hatch.pypa.io/latest/) is recommended.

### Server Setup (Raspberry Pi)

1. Download the latest .whl file and `pip install` it.
2. Create configuration files (see [Configuration](#configuration) below)
3. Run the application with `nohup server start > ~/uvicorn.log &1>2`

:warning: TODO: publish builds as downloadable releases.

### Configuration

The server is configured using a TOML file (`config.toml`). This is documented in `server/CONFIG.md`.

#### Required API Credentials

##### Google Calendar

- You need a Google Cloud service account credentials file (`credentials_service.json`)
- The service account must have access to the calendars you want to display
- Calendar IDs can be found in Google Calendar settings under "Integrate calendar"

##### Todoist

- You need a Todoist API key (stored in `api_keys.json`)
- Project ID can be found in the URL when viewing a project in Todoist web interface

Device (Kindle):

1. Jailbreak your Kindle, using any method (I used LanguageBreak).
2. Install KUAL.
3. Download the latest release and copy it to `/mnt/us/dashboard`.
4. Open KUAL and tap `Start dashboard`.

:warning: TODO: complete this.

## License

This project is licensed under the [MIT License](LICENSE).

## Credits

This project was inspired by and builds upon the work of several excellent projects:

- [kindle-dash](https://github.com/pascalw/kindle-dash) by Pascal Widdershoven
- [life-dashboard](https://github.com/davidhampgonsalves/life-dashboard) by David Hamp-Gonsalves
- [Building an E-ink Weather Display](https://matthealy.com/kindle) by Matt Healy
- [Building eInk Weather Display for Our Home](https://kimmo.blog/posts/7-building-eink-weather-display-for-our-home/) by Kimmo Brunfeldt