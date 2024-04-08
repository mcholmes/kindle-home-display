from datetime import datetime

from server.event import Event

DT_START = datetime(2024,1,1).date()
DT_END = datetime(2024,1,2).date()
SUMMARY = "blah"

# @pytest.mark.parametrize()
# def test_datetime_to_time():
#     Event.datetime_to_time()

class TestStartDateIsDate:

    def test_start_only(self):
        e = Event.from_datetimes(
            summary=SUMMARY,
            dt_start=DT_START
            )

        assert e.date_start == DT_START
        assert e.date_end is None
        assert e.time_start is None
        assert e.time_end is None

    # def test_end_date(self):
    #     err = "Test not implemented"
    #     raise AssertionError(err)