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

Server (Raspberry Pi):
1. Download the latest .whl file and `pip install` it.
2. Create a config file and a file of API keys (currently needed for Todoist and OpenWeatherMap)
3. Run the application with `nohup server start > ~/uvicorn.log &1>2`

:warning: TODO: publish builds as downloadable releases.

Device (Kindle):
1. Jailbreak your Kindle, using any method (I used LanguageBreak).
2. Install KUAL. 
3. Download the latest release and copy it to `/mnt/us/dashboard`.
4. Open KUAL and tap `Start dashboard`.

:warning: TODO: complete this.

## Contributing

Contributions are welcome! 

:warning: TODO: write [CONTRIBUTING.md](CONTRIBUTING.md)

## License

This project is licensed under the [MIT License](LICENSE).

:warning: TODO: credit the projects this was inspired by