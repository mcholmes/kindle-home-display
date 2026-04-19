from datetime import date, datetime
from itertools import chain

import pendulum
from loguru import logger
from pydantic import SecretStr
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Due

from server.activity import Activity

def get_tasks_todoist(api_key: SecretStr, project_id: str, date_end: pendulum.DateTime) -> list[Activity]:

    """
    Returns all tasks within a given Project before the specified end date (i.e. includes overdue tasks).
    """

    tz = date_end.timezone

    api = TodoistAPI(api_key.get_secret_value())

    logger.debug("Querying Todoist.")
    logger.debug("Getting collaborators...")
    try:
        collaborators = list(chain.from_iterable(api.get_collaborators(project_id=str(project_id))))
    except Exception:
        logger.exception("Failed to get collaborators.")
        raise

    logger.debug("Getting tasks...")
    try:
        all_tasks = list(chain.from_iterable(api.get_tasks(project_id=str(project_id))))
    except Exception:
        logger.exception("Failed to get tasks.")
        raise

    # v4 API no longer supports is_completed param -- filter client-side
    tasks = [t for t in all_tasks if not t.is_completed]

    def include_task(due: Due | None) -> bool:
        if due is None:
            return False
        # v4 API: due.date is datetime.date (date-only) or datetime.datetime (with time)
        if isinstance(due.date, datetime):
            return pendulum.instance(due.date, tz=tz) <= date_end
        return pendulum.instance(datetime.combine(due.date, datetime.min.time()), tz=tz) <= date_end

    tasks_due = [t for t in tasks if include_task(t.due)]

    my_collaborators = {c.id: c.name for c in collaborators}

    my_tasks: list[Activity] = []

    logger.debug("Constructing activity list from tasks...")
    for task in tasks_due:
        if task.due is None:
            continue
        assignee_str = "" if task.assignee_id is None else f" [{my_collaborators.get(task.assignee_id)}]"
        summary = task.content + assignee_str
        desc = task.description

        # v4 API: due.date is datetime.datetime (with time) or datetime.date (date-only)
        due_value = task.due.date
        if isinstance(due_value, datetime):
            date_start = due_value.date()
            time_start = due_value.time()
        else:
            date_start = due_value
            time_start = None

        e = Activity(
            activity_type="task",
            summary=summary,
            date_start=date_start,
            time_start=time_start,
            description=desc
        )
        my_tasks.append(e)

    log_msg = f"Built a list of {len(my_tasks)} tasks."
    logger.debug(log_msg)

    return my_tasks
