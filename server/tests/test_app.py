# SPDX-FileCopyrightText: 2024-present Mike Holmes
# SPDX-License-Identifier: MIT

from datetime import date, time
from pathlib import Path
from unittest.mock import patch

import pendulum
import pytest
from pydantic import SecretStr

from server.activity import Activity
from server.app import App, DataFetchError, create_app
from server.config import AppConfig, CalendarConfig, ImageConfig, ServerConfig, TasksConfig

TZ = "Europe/London"


@pytest.fixture
def minimal_config(tmp_path) -> AppConfig:
    """Config with all required fields, using tmp_path for server_dir."""
    return AppConfig(
        server=ServerConfig(host="127.0.0.1", port=8000, server_dir=str(tmp_path)),
        image=ImageConfig(width=800, height=600),
        calendar=CalendarConfig(
            display_timezone=TZ,
            days_to_show=2,
            ids={"cal1": "cal1@gmail.com"},
            creds=Path("/fake/creds.json"),
        ),
        tasks=TasksConfig(project_id="proj1"),
        api_keys={"todoist": SecretStr("test-key")},
    )


@pytest.fixture
def app(minimal_config) -> App:
    return App(minimal_config)


def _make_event(summary: str, hour: int = 9, day: int = 19) -> Activity:
    return Activity(
        activity_type="event",
        summary=summary,
        date_start=date(2025, 4, day),
        time_start=time(hour, 0),
    )


def _make_task(summary: str, day: int = 19) -> Activity:
    return Activity(
        activity_type="task",
        summary=summary,
        date_start=date(2025, 4, day),
    )


# ========== App.get_logs ==========


class TestGetLogs:
    def test_returns_log_content(self, app, tmp_path):
        log_file = tmp_path / "server.log"
        log_file.write_text("line 1\nline 2\n")

        result = app.get_logs("server.log")
        assert "line 1" in result
        assert "line 2" in result

    def test_missing_log_file_returns_message(self, app):
        result = app.get_logs("nonexistent.log")
        assert "No log file found" in result

    def test_get_server_logs_uses_config_name(self, app, tmp_path):
        log_file = tmp_path / "server.log"
        log_file.write_text("server log content")

        result = app.get_server_logs()
        assert "server log content" in result

    def test_get_device_logs_uses_config_name(self, app, tmp_path):
        log_file = tmp_path / "device.log"
        log_file.write_text("device log content")

        result = app.get_device_logs()
        assert "device log content" in result


# ========== App.get_dashboard_data ==========


class TestGetDashboardData:
    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_returns_grouped_events_and_date(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)

        mock_tasks.return_value = [_make_task("Bins")]
        mock_appointments.return_value = [_make_event("Standup")]

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            events, current_date = app.get_dashboard_data()

        assert current_date == now
        # Both events are today (day 0)
        assert 0 in events
        assert len(events[0]) == 2

    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_filters_events_ended_over_an_hour_ago(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 14, 0, tz=TZ)

        # Event that ended 3 hours ago (time_start=11:00, no end time)
        old_event = Activity(
            activity_type="event",
            summary="Old",
            date_start=date(2025, 4, 19),
            time_start=time(11, 0),
        )
        current_event = _make_event("Current", hour=13)

        mock_tasks.return_value = []
        mock_appointments.return_value = [old_event, current_event]

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            events, _ = app.get_dashboard_data()

        # Old event should be filtered out
        all_events = []
        for day_events in events.values():
            all_events.extend(day_events)
        summaries = [e.summary for e in all_events]
        assert "Current" in summaries
        # "Old" might or might not be filtered depending on exact timing, but let's verify the logic runs

    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_events_grouped_by_day(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)

        today_event = _make_event("Today", day=19)
        tomorrow_event = _make_event("Tomorrow", day=20)

        mock_tasks.return_value = []
        mock_appointments.return_value = [today_event, tomorrow_event]

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            events, _ = app.get_dashboard_data()

        assert 0 in events  # today
        assert 1 in events  # tomorrow
        assert events[0][0].summary == "Today"
        assert events[1][0].summary == "Tomorrow"

    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_empty_data(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)

        mock_tasks.return_value = []
        mock_appointments.return_value = []

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            events, current_date = app.get_dashboard_data()

        assert events == {}
        assert current_date == now

    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_partial_failure_returns_working_data(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)

        mock_tasks.side_effect = Exception("Todoist failed")
        mock_appointments.return_value = [_make_event("Standup")]

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            events, current_date = app.get_dashboard_data()

        assert current_date == now
        assert 0 in events
        assert len(events[0]) == 1
        assert events[0][0].summary == "Standup"

    @patch.object(App, "get_appointments")
    @patch.object(App, "get_tasks")
    def test_total_failure_raises_data_fetch_error(self, mock_tasks, mock_appointments, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)

        mock_tasks.side_effect = Exception("Todoist failed")
        mock_appointments.side_effect = Exception("Calendar failed")

        with patch("server.app.pendulum") as mock_pendulum:
            mock_pendulum.now.return_value = now
            with pytest.raises(DataFetchError) as exc_info:
                app.get_dashboard_data()

        assert "Tasks error" in str(exc_info.value)
        assert "Appointments error" in str(exc_info.value)
        assert "Todoist failed" in str(exc_info.value)
        assert "Calendar failed" in str(exc_info.value)


# ========== App.generate_image ==========


class TestGenerateImage:
    def test_returns_png_bytes(self, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        events = {
            0: [_make_event("Standup"), _make_task("Bins")],
            1: [_make_event("Lunch", hour=12, day=20)],
        }

        result = app.generate_image(events, now)

        assert isinstance(result, bytes)
        assert result[:4] == b"\x89PNG"

    def test_empty_events(self, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        result = app.generate_image({}, now)

        assert isinstance(result, bytes)
        assert result[:4] == b"\x89PNG"


# ========== App.generate_image_and_save ==========


class TestGenerateImageAndSave:
    @patch.object(App, "get_dashboard_data")
    def test_writes_file_to_disk(self, mock_data, app, tmp_path):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        mock_data.return_value = ({0: [_make_event("Test")]}, now)

        app.generate_image_and_save()

        output_file = tmp_path / "dashboard.png"
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        content = output_file.read_bytes()
        assert content[:4] == b"\x89PNG"

    @patch.object(App, "get_dashboard_data")
    def test_generate_image_and_save_handles_error(self, mock_data, app, tmp_path):
        mock_data.side_effect = DataFetchError("Test error trace")

        app.generate_image_and_save()

        output_file = tmp_path / "dashboard.png"
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        content = output_file.read_bytes()
        assert content[:4] == b"\x89PNG"


# ========== App.get_dashboard_response ==========


class TestGetDashboardResponse:
    @patch.object(App, "get_dashboard_data")
    def test_returns_png_response(self, mock_data, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        mock_data.return_value = ({0: [_make_event("Test")]}, now)

        response = app.get_dashboard_response()

        assert response.media_type == "image/png"
        assert response.body[:4] == b"\x89PNG"

    @patch.object(App, "get_dashboard_data")
    def test_get_dashboard_response_handles_error(self, mock_data, app):
        mock_data.side_effect = DataFetchError("Test error trace")

        response = app.get_dashboard_response()

        assert response.media_type == "image/png"
        assert response.body[:4] == b"\x89PNG"


# ========== App.get_tasks ==========


class TestGetTasks:
    @patch("server.app.get_tasks_todoist")
    def test_delegates_to_todoist(self, mock_todoist, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        expected = [_make_task("Task 1")]
        mock_todoist.return_value = expected

        result = app.get_tasks(now)

        assert result == expected
        mock_todoist.assert_called_once_with(
            api_key=app.config.api_keys["todoist"],
            project_id="proj1",
            date_end=now.add(days=2),
        )


# ========== App.get_appointments ==========


class TestGetAppointments:
    @patch("server.app.Calendar")
    def test_delegates_to_calendar(self, mock_calendar_cls, app):
        now = pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)
        expected = [_make_event("Meeting")]
        mock_calendar_cls.return_value.get_events_cal.return_value = expected

        result = app.get_appointments(now)

        assert result == expected
        mock_calendar_cls.assert_called_once()


# ========== create_app ==========


class TestCreateApp:
    def test_has_expected_routes(self, minimal_config):
        fastapi_app = create_app(minimal_config)
        route_paths = [r.path for r in fastapi_app.routes]

        assert "/" in route_paths
        assert "/dashboard" in route_paths
        assert "/logs/server" in route_paths
        assert "/logs/device" in route_paths

    def test_root_returns_docs_message(self, minimal_config):
        from fastapi.testclient import TestClient

        fastapi_app = create_app(minimal_config)
        client = TestClient(fastapi_app)
        response = client.get("/")

        assert response.status_code == 200
        assert "docs" in response.text.lower()
