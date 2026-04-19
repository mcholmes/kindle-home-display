from datetime import date, time

import pendulum
import pytest
from pydantic import ValidationError

from server.activity import (
    Activity,
    calculate_short_time,
    datetime_to_date,
    datetime_to_time,
    group_events_by_relative_day,
    sort_by_time,
)

TZ = "Europe/London"
SUMMARY = "event summary here"

@pytest.fixture
def date_future() -> date:
    return pendulum.datetime(9999, 1, 1, tz=TZ).date()

@pytest.fixture
def datetime_future() -> pendulum.DateTime:
    return pendulum.datetime(9999, 1, 1, 0, 5, tz=TZ)

@pytest.fixture
def date_past() -> date:
    return pendulum.datetime(1900, 1, 1, tz=TZ).date()

@pytest.fixture
def datetime_past() -> pendulum.DateTime:
    return pendulum.datetime(1900, 1, 1, 0, 5, tz=TZ)

# ========== Valid cases ==========

def test_start_only(date_future):
    e = Activity.from_datetimes(
        activity_type="event",
        summary=SUMMARY,
        datetime_start=date_future
        )

    assert e.date_start == date_future
    assert e.date_end is None
    assert e.time_start is None
    assert e.time_end is None

def test_start_datetime_but_no_end(datetime_future):
    e = Activity.from_datetimes(
            activity_type="task",
            summary=SUMMARY,
            datetime_start=datetime_future,
            datetime_end=None
    )

    assert e.date_start == datetime_future.date()
    assert e.time_start == datetime_future.time()
    assert e.date_end is None
    assert e.time_end is None

def test_time_start_short():
    e = Activity.from_datetimes(
        activity_type="event",
        summary=SUMMARY,
        datetime_start=pendulum.datetime(1970, 1, 1, 12, 30),
        datetime_end=pendulum.datetime(1970, 1, 1, 13, 30),
        )

    assert e.time_start_short == "12.30pm"
    assert e.time_end_short == "1.30pm"

def test_get_relative_days_start(date_future):
    e = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date_future
        )

    d_minus_1 = date_future - pendulum.duration(days=1)
    d_plus_1 = date_future + pendulum.duration(days=1)

    assert e.get_relative_days_start(d_minus_1) == 1
    assert e.get_relative_days_start(date_future) == 0
    assert e.get_relative_days_start(d_plus_1) == -1

def test_group_events_by_relative_day():
    e1 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date(2022, 1, 1)
        )

    e2 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date(2022, 1, 2)
        )

    e3 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date(2022, 1, 1)
        )

    events = [e1, e2, e3]

    grouped = group_events_by_relative_day(events, date(2022, 1, 1))

    assert len(grouped) == 2
    assert len(grouped[0]) == 2
    assert len(grouped[1]) == 1

# ========== Invalid cases ==========

def test_missing_summary(date_future):
    with pytest.raises(ValidationError):
        Activity.from_datetimes(
            activity_type="event",
            summary=None,
            datetime_start=date_future
        )

def test_end_before_start_date(date_past, date_future):
    with pytest.raises(ValidationError):
        Activity.from_datetimes(
            activity_type="event",
            summary=SUMMARY,
            datetime_start=date_future,
            datetime_end=date_past
        )

def test_end_before_start_time(datetime_past, datetime_future):
    with pytest.raises(ValidationError):
        Activity.from_datetimes(
            activity_type="event",
            summary=SUMMARY,
            datetime_start=datetime_future,
            datetime_end=datetime_past
        )

def test_end_but_no_start(datetime_future):
    with pytest.raises(ValidationError):
        Activity.from_datetimes(
            activity_type="event",
            summary=SUMMARY,
            datetime_start=None,
            datetime_end=datetime_future
        )

# ========== Properties ==========
def test_is_all_day(date_future):
    e = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date_future,
        time_start=None
        )

    assert e.is_all_day

def test_is_not_all_day(date_future):
    e = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date_future,
        time_start=time(12, 30)
        )

    assert not e.is_all_day

def test_is_multi_day(date_future):
    day_plus_one = date_future + pendulum.duration(days=1)
    e = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=date_future,
        date_end=day_plus_one
    )

    assert e.is_multi_day

def test_ends_today():
    now = pendulum.now(TZ)

    e1 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=now.date(),
        time_start=None
    )

    tomorrow = now.add(days=1)
    e2 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=tomorrow.date(),
        time_start=None
    )

    assert e1.ends_today
    assert not e2.ends_today

def test_ended_over_an_hour_ago():
    now = pendulum.now(TZ)
    now_minus_2_hours = now.subtract(hours=2)
    now_minus_30_minutes = now.subtract(minutes=30)
    now_plus_30_minutes = now.add(minutes=30)
    now_plus_2_hours = now.add(hours=2)

    e1 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=now_minus_2_hours.date(),
        time_start=now_minus_2_hours.time()
    )

    e2 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=now_minus_30_minutes.date(),
        time_start=now_minus_30_minutes.time()
    )

    e3 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=now_plus_30_minutes.date(),
        time_start=now_plus_30_minutes.time()
    )

    e4 = Activity(
        activity_type="event",
        summary=SUMMARY,
        date_start=now_plus_2_hours.date(),
        time_start=now_plus_2_hours.time()
    )

    assert e1.ended_over_an_hour_ago
    assert not e2.ended_over_an_hour_ago
    assert not e3.ended_over_an_hour_ago
    assert not e4.ended_over_an_hour_ago

# ========== Functions ==========
@pytest.mark.parametrize("any_datetime,expected",[
        (None, None),
        (pendulum.datetime(1970, 1, 1,  0, 0), "12am"),
        (pendulum.datetime(1970, 1, 1,  0, 30), "12.30am"),
        (pendulum.datetime(1970, 1, 1,  1, 0), "1am"),
        (pendulum.datetime(1970, 1, 1,  1, 30), "1.30am"),
        (pendulum.datetime(1970, 1, 1,  12, 0), "12pm"),
        (pendulum.datetime(1970, 1, 1,  12, 30), "12.30pm"),
        (pendulum.datetime(1970, 1, 1,  13, 0), "1pm"),
        (pendulum.datetime(1970, 1, 1,  13, 30), "1.30pm")
    ])
def test_calculate_short_time(any_datetime, expected):
    if any_datetime is None:
        assert calculate_short_time(any_datetime) is None
    else:
        assert calculate_short_time(any_datetime) == expected

def test_calculate_short_time_invalid_type():
    with pytest.raises(TypeError):
        calculate_short_time("abc")

@pytest.mark.parametrize("dt,expected", [
    (None, None),
    (date(1970, 1, 1), None),
    (pendulum.datetime(9999, 1, 1), time(0, 0)),
    (pendulum.datetime(9999, 1, 1, 0, 5), time(0, 5))
    ])
def test_datetime_to_time(dt, expected):
    if dt is None or (isinstance(dt, date) and not isinstance(dt, pendulum.DateTime) and dt.year == 1970):
        assert datetime_to_time(dt) is None
    else:
        assert datetime_to_time(dt) == expected

def test_datetime_to_time_invalid_type():
    with pytest.raises(TypeError):
        datetime_to_time("abc")

def test_datetime_to_time_stdlib_datetime():
    """stdlib datetime (not pendulum) should extract time correctly -- covers line 113."""
    from datetime import datetime as stdlib_datetime
    dt = stdlib_datetime(2025, 4, 19, 14, 30)  # noqa: DTZ001
    result = datetime_to_time(dt)
    assert result == time(14, 30)

def test_datetime_to_date_invalid_type():
    with pytest.raises(TypeError):
        datetime_to_date("abc")

def test_datetime_to_date_stdlib_datetime():
    """stdlib datetime (not pendulum) should extract date correctly -- covers line 141."""
    from datetime import datetime as stdlib_datetime
    dt = stdlib_datetime(2025, 4, 19, 14, 30)  # noqa: DTZ001
    result = datetime_to_date(dt)
    assert result == date(2025, 4, 19)

def test_datetime_to_date_plain_date():
    """Plain date should be returned as-is."""
    d = date(2025, 4, 19)
    result = datetime_to_date(d)
    assert result == d

def test_from_datetimes_with_description_and_location():
    """from_datetimes should pass through description and location."""
    dt = pendulum.datetime(2025, 4, 19, 10, 0, tz="Europe/London")
    e = Activity.from_datetimes(
        activity_type="event",
        summary="Team lunch",
        datetime_start=dt,
        description="Bring cake",
        location="Office kitchen",
    )
    assert e.description == "Bring cake"
    assert e.location == "Office kitchen"

def test_sort_by_time(date_past):

    activities = [
        (Activity(activity_type="event", summary="0", date_start=date_past, time_start=None)),
        (Activity(activity_type="event", summary="1", date_start=date_past, time_start=time(23, 59))),
        (Activity(activity_type="event", summary="2", date_start=date_past, time_start=time(13, 00))),
        (Activity(activity_type="event", summary="3", date_start=date_past, time_start=time(12, 00))),
        (Activity(activity_type="event", summary="4", date_start=date_past, time_start=time(0, 30))),
        (Activity(activity_type="event", summary="5", date_start=date_past, time_start=time(0, 0))),
    ]

    activities_sorted = sort_by_time(activities)

    assert activities_sorted[0].summary in ["5", "0"]
    assert activities_sorted[1].summary in ["5", "0"]
    assert activities_sorted[2].summary == "4"
    assert activities_sorted[3].summary == "3"
    assert activities_sorted[4].summary == "2"
    assert activities_sorted[5].summary == "1"
