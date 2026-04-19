# SPDX-FileCopyrightText: 2024-present Mike Holmes
# SPDX-License-Identifier: MIT

from datetime import date, time
from pathlib import Path
from unittest.mock import patch

import pendulum
import pytest

from server.activity import Activity
from server.cal import Calendar

TZ = "Europe/London"


@pytest.fixture
def now() -> pendulum.DateTime:
    return pendulum.datetime(2025, 4, 19, 10, 0, tz=TZ)


@pytest.fixture
def calendar(now) -> Calendar:
    return Calendar(
        credentials=Path("/fake/creds.json"),
        calendar_ids=["cal1@gmail.com", "cal2@gmail.com"],
        current_date=now,
        days_to_show=2,
    )


# ========== Properties ==========


class TestCalendarProperties:
    def test_start_date_is_start_of_day(self, calendar, now):
        assert calendar.start_date == now.start_of("day")
        assert calendar.start_date.hour == 0
        assert calendar.start_date.minute == 0

    def test_end_date_is_days_ahead(self, calendar, now):
        expected = now.start_of("day").add(days=2)
        assert calendar.end_date == expected

    def test_custom_days_to_show(self, now):
        cal = Calendar(
            credentials=Path("/fake/creds.json"),
            calendar_ids=["cal1@gmail.com"],
            current_date=now,
            days_to_show=5,
        )
        expected = now.start_of("day").add(days=5)
        assert cal.end_date == expected

    def test_default_days_to_show(self, now):
        cal = Calendar(
            credentials=Path("/fake/creds.json"),
            calendar_ids=["cal1@gmail.com"],
            current_date=now,
        )
        assert cal.days_to_show == 2

    def test_exclude_default_calendar_default_false(self, calendar):
        assert calendar.exclude_default_calendar is False


# ========== get_events_cal ==========


class TestGetEventsCal:
    @patch("server.cal.GCal")
    def test_delegates_to_gcal(self, mock_gcal_cls, calendar):
        mock_gcal = mock_gcal_cls.return_value
        expected = [
            Activity(
                activity_type="event",
                summary="Meeting",
                date_start=date(2025, 4, 19),
                time_start=time(14, 0),
            )
        ]
        mock_gcal.get_events.return_value = expected

        result = calendar.get_events_cal()

        assert result == expected
        mock_gcal_cls.assert_called_once_with(Path("/fake/creds.json"))
        mock_gcal.get_events.assert_called_once_with(
            date_from=calendar.start_date,
            date_to=calendar.end_date,
            additional_calendars=["cal1@gmail.com", "cal2@gmail.com"],
            exclude_default_calendar=False,
        )

    @patch("server.cal.GCal")
    def test_passes_exclude_default_calendar(self, mock_gcal_cls, now):
        cal = Calendar(
            credentials=Path("/fake/creds.json"),
            calendar_ids=["cal1@gmail.com"],
            current_date=now,
            exclude_default_calendar=True,
        )
        mock_gcal = mock_gcal_cls.return_value
        mock_gcal.get_events.return_value = []

        cal.get_events_cal()

        mock_gcal.get_events.assert_called_once_with(
            date_from=cal.start_date,
            date_to=cal.end_date,
            additional_calendars=["cal1@gmail.com"],
            exclude_default_calendar=True,
        )

    @patch("server.cal.GCal")
    def test_returns_empty_list_when_no_events(self, mock_gcal_cls, calendar):
        mock_gcal_cls.return_value.get_events.return_value = []

        result = calendar.get_events_cal()
        assert result == []

    @patch("server.cal.GCal")
    def test_gcal_error_propagates(self, mock_gcal_cls, calendar):
        mock_gcal_cls.side_effect = RuntimeError("Auth failed")

        with pytest.raises(RuntimeError, match="Auth failed"):
            calendar.get_events_cal()
