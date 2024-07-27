from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from server.activity import Activity

TZ = ZoneInfo("Europe/London")
SUMMARY = "event summary here"

@pytest.fixture
def date_future() -> date:
    return datetime(9999,1,1,tzinfo=TZ).date()

@pytest.fixture
def datetime_future() -> datetime:
    return datetime(9999,1,1,0,5,tzinfo=TZ)

@pytest.fixture
def date_past() -> date:
    return datetime(1900,1,1,tzinfo=TZ).date()

@pytest.fixture
def datetime_past() -> datetime:
    return datetime(1900,1,1,0,5,tzinfo=TZ)

def test_start_only(date_future):
    e = Activity.from_datetimes(
        activity_type="event",
        summary=SUMMARY,
        dt_start=date_future
        )

    assert e.date_start == date_future
    assert e.date_end is None
    assert e.time_start is None
    assert e.time_end is None

def test_missing_summary(date_future):
    with pytest.raises(ValidationError):
        Activity.from_datetimes(
            activity_type="event",
            summary=None,
            dt_start=date_future
        )

def test_start_datetime_but_no_end(datetime_future):
    e = Activity.from_datetimes(
            activity_type="task",
            summary=SUMMARY,
            dt_start=datetime_future,
            dt_end=None
    )

    assert e.date_start == datetime_future.date()
    assert e.time_start == datetime_future.time()
    assert e.date_end is None
    assert e.time_end is None
