import re
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from server.config import (
    AppConfig,
    MultipleFilesFoundError,
    WeatherConfig,
    find_file_in_dir,
    get_dict_from_file,
    get_required_fields,
)


@pytest.fixture
def valid_server_config():
    return {
        "host": "127.0.0.1",
        "port": 8000,
        "server_dir": "/abc"
    }

@pytest.fixture
def valid_image_config():
    return {
        "width": 1072,
        "height": 1448
    }

@pytest.fixture
def valid_calendar_config():
    return{
        "display_timezone": "Europe/London",
        "days_to_show": 3,
        "ids": {
            "name_1": "id_1@gmail.com"
        },
        "creds": "/path/to/creds"
    }

@pytest.fixture
def valid_tasks_config():
    return {
        "project_id": "2306241165"
    }

# from_dict tests
def test_invalid_empty():
    config = {}
    err = "Config provided is empty."
    with pytest.raises(ValueError, match=err):
        AppConfig.from_dicts(config)

def test_invalid_missing_all_required():
    config = {"random_field": 42}

    err_pattern = re.compile("Missing top-level configs:")
    with pytest.raises(ValueError, match=err_pattern):
        AppConfig.from_dicts(config)

def test_invalid_missing_one_required(valid_server_config):

    config = {"server": valid_server_config}

    err_pattern = re.compile("Missing top-level configs:")
    with pytest.raises(ValueError, match=err_pattern):
        AppConfig.from_dicts(config)

def test_valid_required_only(valid_server_config, valid_image_config):
    config = {
        "server": valid_server_config,
        "image": valid_image_config,
    }

    config = AppConfig.from_dicts(config)

    assert config.server.host == IPv4Address("127.0.0.1")
    assert config.server.port == 8000
    assert config.server.server_dir == "/abc"

    assert config.image.width == 1072
    assert config.image.height == 1448

def test_valid_all_fields(valid_server_config, valid_image_config, valid_calendar_config, valid_tasks_config):


    config = {
        "server": valid_server_config,
        "image": valid_image_config,
        "calendar": valid_calendar_config,
        "tasks": valid_tasks_config
    }

    config = AppConfig.from_dicts(config)

    assert config.server.host == IPv4Address("127.0.0.1")
    assert config.server.port == 8000
    assert config.server.server_dir == "/abc"

    assert config.image.width == 1072
    assert config.image.height == 1448

    assert config.calendar.display_timezone == "Europe/London"
    assert config.calendar.days_to_show == 3
    assert config.calendar.ids == {"name_1": "id_1@gmail.com"}
    assert config.calendar.creds == Path("/path/to/creds")

def test_valid_extraneous_fields(valid_server_config, valid_image_config):
    config = {
        "server": valid_server_config,
        "image": valid_image_config,
        "extra:": "field"
    }

    config = AppConfig.from_dicts(config)

    assert config.server.host == IPv4Address("127.0.0.1")
    assert config.server.port == 8000
    assert config.server.server_dir == "/abc"

    assert config.image.width == 1072
    assert config.image.height == 1448

def test_no_matching_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_file_in_dir(tmp_path, "testfile.json")

def test_one_matching_file(tmp_path):
    f1 = tmp_path / "file1.json"
    f2 = tmp_path / "file2.json"
    f1.touch()
    f2.touch()

    result = find_file_in_dir(tmp_path, "file1")
    assert result == tmp_path / "file1.json"

def test_multiple_matching_files(tmp_path):
    f1 = tmp_path / "file1.json"
    f2 = tmp_path / "file1.yaml"
    f1.touch()
    f2.touch()

    with pytest.raises(MultipleFilesFoundError):
        find_file_in_dir(tmp_path, "file1")

def test_get_dict_from_file_is_directory(tmp_path):
    with pytest.raises(IsADirectoryError):
        get_dict_from_file(tmp_path)

def test_get_dict_from_file_bad_extension(tmp_path):
    f = tmp_path / "file.txt"
    f.touch()

    with pytest.raises(TypeError):
        get_dict_from_file(f)

def test_get_dict_from_file_json(tmp_path):
    f = tmp_path / "file.json"
    f.write_text('{"key": "value"}')

    result = get_dict_from_file(f)
    assert result == {"key": "value"}

def test_get_dict_from_file_yaml(tmp_path):
    f = tmp_path / "file.yaml"
    f.write_text("key: value")

    result = get_dict_from_file(f)
    assert result == {"key": "value"}

def test_get_dict_from_file_toml(tmp_path):
    f = tmp_path / "file.toml"
    f.write_text("key = 'value'")

    result = get_dict_from_file(f)
    assert result == {"key": "value"}

def test_get_dict_from_file_yml(tmp_path):
    """Test .yml extension (in addition to .yaml)."""
    f = tmp_path / "file.yml"
    f.write_text("key: value")

    result = get_dict_from_file(f)
    assert result == {"key": "value"}


# ========== get_required_fields ==========

def test_get_required_fields_non_recursive():
    fields = list(get_required_fields(AppConfig))
    assert "server" in fields
    assert "image" in fields
    # Optional fields should not appear
    assert "api_keys" not in fields
    assert "calendar" not in fields

def test_get_required_fields_recursive():
    """Recursive mode should yield leaf fields from nested models -- covers line 58."""
    fields = list(get_required_fields(AppConfig, recursive=True))
    # Server and Image have no non-optional fields without defaults
    # except ImageConfig.width and ImageConfig.height
    assert "width" in fields
    assert "height" in fields


# ========== WeatherConfig ==========

def test_weather_config():
    w = WeatherConfig(latitude=51.5, longitude=-0.1)
    assert w.latitude == 51.5
    assert w.longitude == -0.1


# ========== AppConfig.from_dir ==========

def test_from_dir_loads_config_and_api_keys(tmp_path, valid_server_config, valid_image_config):
    """from_dir should load config.toml and api_keys.json from a directory."""
    import json

    config_content = f"""
[server]
host = "{valid_server_config['host']}"
port = {valid_server_config['port']}
server_dir = "{valid_server_config['server_dir']}"

[image]
width = {valid_image_config['width']}
height = {valid_image_config['height']}
"""
    (tmp_path / "config.toml").write_text(config_content)

    api_keys = {"todoist": "test-api-key", "owm": "weather-key"}
    (tmp_path / "api_keys.json").write_text(json.dumps(api_keys))

    config = AppConfig.from_dir(tmp_path)

    assert config.server.host == IPv4Address("127.0.0.1")
    assert config.server.port == 8000
    assert config.image.width == 1072
    assert config.image.height == 1448
    assert config.api_keys is not None
    assert config.api_keys["todoist"].get_secret_value() == "test-api-key"

def test_from_dir_without_api_keys(tmp_path, valid_server_config, valid_image_config):
    """from_dir should work even when api_keys file is missing."""
    config_content = f"""
[server]
host = "{valid_server_config['host']}"
port = {valid_server_config['port']}
server_dir = "{valid_server_config['server_dir']}"

[image]
width = {valid_image_config['width']}
height = {valid_image_config['height']}
"""
    (tmp_path / "config.toml").write_text(config_content)

    config = AppConfig.from_dir(tmp_path)

    assert config.server.host == IPv4Address("127.0.0.1")
    assert config.api_keys is None

def test_from_dir_no_config_file(tmp_path):
    """from_dir should raise FileNotFoundError if no config file exists."""
    with pytest.raises(FileNotFoundError):
        AppConfig.from_dir(tmp_path)
