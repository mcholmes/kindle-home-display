import re
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from server.config import (
    AppConfig,
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
        "project_id": 2306241165
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

def test_invalid_missing_api_key():
    ... # TODO

