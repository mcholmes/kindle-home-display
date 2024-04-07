from configparser import ConfigParser

config = ConfigParser()

config.read("config.ini")

config.add_section("image")
config.set("image", "width", "1072")
config.set("image", "height", "1448")
config.set("image", "rotate_angle", "0")

config.add_section("calendar")
config.set("calendar", "display_timezone", "Europe/London")
config.set("calendar", "days_to_show", "2")

config.add_section("calendar_ids")
config.set(
    "calendar_ids",
    "Holmbergs",
    "10a2dd68e51bb17689c7ccf4f4722d1f445c59c86430577b425c33ccee27be2e@group.calendar.google.com",
)

config.add_section("weather")
config.set("weather", "latitude", "51.424340")
config.set("weather", "longitude", "-0.142855")

config.add_section("output")
config.set("output", "image_name", "dashboard.png")
config.set("output", "server_dir", "/var/www/html/")

with open("config.ini", "w") as f:
    config.write(f)
