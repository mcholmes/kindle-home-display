# SPDX-FileCopyrightText: 2024-present Mike Holmes
# SPDX-License-Identifier: MIT

from datetime import date, datetime, time
from unittest.mock import MagicMock, patch

import pendulum
import pytest
from pydantic import SecretStr
from todoist_api_python.models import Collaborator, Due, Task

from server.todoist import get_tasks_todoist

TZ = "Europe/London"


def _make_due(due_date: date | datetime, is_recurring: bool = False) -> Due:
    """Helper to create a Due object with the v4 API shape."""
    due = MagicMock(spec=Due)
    due.date = due_date
    due.string = "some date string"
    due.is_recurring = is_recurring
    due.lang = "en"
    due.timezone = None
    return due


def _make_task(
    task_id: str = "1",
    content: str = "Test task",
    description: str = "",
    due: Due | None = None,
    is_completed: bool = False,
    assignee_id: str | None = None,
) -> Task:
    """Helper to create a mock Task object."""
    task = MagicMock(spec=Task)
    task.id = task_id
    task.content = content
    task.description = description
    task.due = due
    task.is_completed = is_completed
    task.assignee_id = assignee_id
    task.project_id = "proj1"
    return task


def _make_collaborator(collab_id: str = "c1", name: str = "Alice") -> Collaborator:
    """Helper to create a mock Collaborator object."""
    collab = MagicMock(spec=Collaborator)
    collab.id = collab_id
    collab.name = name
    collab.email = f"{name.lower()}@example.com"
    return collab


API_KEY = SecretStr("test-api-key")
PROJECT_ID = "proj1"


class TestGetTasksTodoist:
    """Tests for the get_tasks_todoist function."""

    @patch("server.todoist.TodoistAPI")
    def test_empty_project_returns_empty_list(self, mock_api_cls):
        """A project with no tasks returns an empty list."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])
        api.get_tasks.return_value = iter([[]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert result == []
        mock_api_cls.assert_called_once_with("test-api-key")

    @patch("server.todoist.TodoistAPI")
    def test_completed_tasks_are_excluded(self, mock_api_cls):
        """Completed tasks should be filtered out (v4 API client-side filtering)."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        due = _make_due(date(2025, 1, 5))
        completed_task = _make_task(content="Done", due=due, is_completed=True)
        open_task = _make_task(content="Open", due=due, is_completed=False)
        api.get_tasks.return_value = iter([[completed_task, open_task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Open"

    @patch("server.todoist.TodoistAPI")
    def test_tasks_without_due_date_excluded(self, mock_api_cls):
        """Tasks with no due date should not appear on the dashboard."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        task_no_due = _make_task(content="No due", due=None)
        task_with_due = _make_task(content="Has due", due=_make_due(date(2025, 1, 5)))
        api.get_tasks.return_value = iter([[task_no_due, task_with_due]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Has due"

    @patch("server.todoist.TodoistAPI")
    def test_tasks_after_date_end_excluded(self, mock_api_cls):
        """Tasks due after date_end should be excluded."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        before = _make_task(content="Before", due=_make_due(date(2025, 1, 5)))
        after = _make_task(content="After", due=_make_due(date(2025, 1, 15)))
        api.get_tasks.return_value = iter([[before, after]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Before"

    @patch("server.todoist.TodoistAPI")
    def test_due_date_is_datetime_with_time(self, mock_api_cls):
        """v4 API: due.date can be a datetime (with time info). Time should be extracted."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        due_dt = datetime(2025, 1, 5, 14, 30)  # noqa: DTZ001
        task = _make_task(content="Timed task", due=_make_due(due_dt))
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].date_start == date(2025, 1, 5)
        assert result[0].time_start == time(14, 30)
        assert result[0].activity_type == "task"

    @patch("server.todoist.TodoistAPI")
    def test_due_date_is_date_only(self, mock_api_cls):
        """v4 API: due.date as a plain date (no time). time_start should be None."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        task = _make_task(content="Date-only task", due=_make_due(date(2025, 1, 5)))
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].date_start == date(2025, 1, 5)
        assert result[0].time_start is None

    @patch("server.todoist.TodoistAPI")
    def test_assignee_appended_to_summary(self, mock_api_cls):
        """When a task has an assignee, their name should be appended in brackets."""
        api = mock_api_cls.return_value
        collab = _make_collaborator(collab_id="c1", name="Alice")
        api.get_collaborators.return_value = iter([[collab]])

        task = _make_task(
            content="Take out bins",
            due=_make_due(date(2025, 1, 5)),
            assignee_id="c1",
        )
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Take out bins [Alice]"

    @patch("server.todoist.TodoistAPI")
    def test_no_assignee_no_brackets(self, mock_api_cls):
        """When a task has no assignee, summary should be just the content."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        task = _make_task(
            content="Mow the lawn",
            due=_make_due(date(2025, 1, 5)),
            assignee_id=None,
        )
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert result[0].summary == "Mow the lawn"

    @patch("server.todoist.TodoistAPI")
    def test_description_is_preserved(self, mock_api_cls):
        """Task description should be passed through to the Activity."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        task = _make_task(
            content="Important task",
            description="Don't forget the details",
            due=_make_due(date(2025, 1, 5)),
        )
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert result[0].description == "Don't forget the details"

    @patch("server.todoist.TodoistAPI")
    def test_paginated_responses(self, mock_api_cls):
        """v4 API returns paginated iterators. Tasks from multiple pages should be collected."""
        api = mock_api_cls.return_value

        collab1 = _make_collaborator(collab_id="c1", name="Alice")
        collab2 = _make_collaborator(collab_id="c2", name="Bob")
        api.get_collaborators.return_value = iter([[collab1], [collab2]])

        task1 = _make_task(task_id="1", content="Task page 1", due=_make_due(date(2025, 1, 5)))
        task2 = _make_task(task_id="2", content="Task page 2", due=_make_due(date(2025, 1, 6)))
        api.get_tasks.return_value = iter([[task1], [task2]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 2
        summaries = {r.summary for r in result}
        assert summaries == {"Task page 1", "Task page 2"}

    @patch("server.todoist.TodoistAPI")
    def test_collaborators_api_failure_raises(self, mock_api_cls):
        """If get_collaborators fails, the exception should propagate."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([])
        api.get_collaborators.side_effect = RuntimeError("API error")

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        with pytest.raises(RuntimeError, match="API error"):
            get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

    @patch("server.todoist.TodoistAPI")
    def test_tasks_api_failure_raises(self, mock_api_cls):
        """If get_tasks fails, the exception should propagate."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])
        api.get_tasks.side_effect = RuntimeError("API error")

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        with pytest.raises(RuntimeError, match="API error"):
            get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

    @patch("server.todoist.TodoistAPI")
    def test_due_on_exact_boundary_included(self, mock_api_cls):
        """A task due exactly on date_end should be included."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        task = _make_task(content="Boundary", due=_make_due(date(2025, 1, 10)))
        api.get_tasks.return_value = iter([[task]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Boundary"

    @patch("server.todoist.TodoistAPI")
    def test_overdue_tasks_included(self, mock_api_cls):
        """Overdue tasks (due before current window) should be included."""
        api = mock_api_cls.return_value
        api.get_collaborators.return_value = iter([[]])

        overdue = _make_task(content="Overdue", due=_make_due(date(2024, 12, 1)))
        api.get_tasks.return_value = iter([[overdue]])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        assert len(result) == 1
        assert result[0].summary == "Overdue"

    @patch("server.todoist.TodoistAPI")
    def test_mixed_scenario(self, mock_api_cls):
        """End-to-end: mix of completed, no-due, overdue, in-range, and future tasks."""
        api = mock_api_cls.return_value

        collab = _make_collaborator(collab_id="c1", name="Mike")
        api.get_collaborators.return_value = iter([[collab]])

        tasks = [
            _make_task(task_id="1", content="Completed", due=_make_due(date(2025, 1, 5)), is_completed=True),
            _make_task(task_id="2", content="No due", due=None),
            _make_task(task_id="3", content="Overdue", due=_make_due(date(2024, 12, 1))),
            _make_task(task_id="4", content="Today", due=_make_due(datetime(2025, 1, 8, 9, 0)), assignee_id="c1"),  # noqa: DTZ001
            _make_task(task_id="5", content="Tomorrow", due=_make_due(date(2025, 1, 9))),
            _make_task(task_id="6", content="Future", due=_make_due(date(2025, 2, 1))),
        ]
        api.get_tasks.return_value = iter([tasks])

        date_end = pendulum.datetime(2025, 1, 10, tz=TZ)
        result = get_tasks_todoist(API_KEY, PROJECT_ID, date_end)

        summaries = [r.summary for r in result]
        assert "Completed" not in summaries
        assert "No due" not in summaries
        assert "Future" not in summaries
        assert "Overdue" in summaries
        assert "Today [Mike]" in summaries
        assert "Tomorrow" in summaries
        assert len(result) == 3
