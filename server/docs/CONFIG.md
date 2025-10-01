# Server Configuration

The server component of the Kindle Home Display is configured using a TOML file (`config.toml`). This document describes all available configuration options.

## Configuration Sections

### Server Settings

```toml
[server]
server_dir = "/path/to/server/"  # Directory where the server stores its files
```

### Display Settings

```toml
[image]
width = 1072           # Width of the generated dashboard image (Kindle screen width)
height = 1448          # Height of the generated dashboard image (Kindle screen height)
```

### Calendar Integration

```toml
[calendar]
display_timezone = "Europe/London"   # Timezone for displaying calendar events
days_to_show = 2                     # Number of days of calendar events to display
ids = {                              # Dictionary of calendar IDs to display
    "calendar_name" = "calendar_id@group.calendar.google.com"
}
creds = "/path/to/credentials_service.json"  # Path to Google Calendar service account credentials
```

### Task Integration (Todoist)

```toml
[tasks]
project_id = 1234567890  # Todoist project ID to display tasks from
```

## Setting Up the Configuration

1. Create a new file named `config.toml` in the server directory
2. Copy the template above and adjust the values according to your needs
3. Make sure to update:
   - Server directory path
   - Calendar credentials path
   - Calendar IDs for your Google Calendars
   - Todoist project ID

## Required API Credentials

### Google Calendar

- You need a Google Cloud service account credentials file (`credentials_service.json`)
- The service account must have access to the calendars you want to display
- Calendar IDs can be found in Google Calendar settings under "Integrate calendar"

### Todoist

- You need a Todoist API key
- Project ID can be found in the URL when viewing a project in Todoist web interface

## Example Configuration

```toml
[server]
server_dir = "/var/www/kindle-dashboard/"

[image]
width = 1072
height = 1448

[calendar]
display_timezone = "Europe/London"
days_to_show = 2
ids = {
    "family" = "family.calendar_id@group.calendar.google.com",
    "work" = "work.calendar_id@group.calendar.google.com"
}
creds = "/path/to/credentials_service.json"

[tasks]
project_id = 1234567890
```
