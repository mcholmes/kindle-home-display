import logging
from typing import Optional, cast

import pendulum
from pydantic import SecretStr
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Due

from server.activity import Activity

logger = logging.getLogger(__name__)

def get_tasks_todoist(api_key: SecretStr, project_id: int, date_end: pendulum.DateTime) -> list[Activity]:

    """
    Returns all tasks within a given Project before the specified end date (i.e. includes overdue tasks).
    """

    tz = date_end.timezone

    api = TodoistAPI(api_key.get_secret_value())

    logger.debug("Querying Todoist.")
    logger.debug("Getting collaborators...")
    try:
        collaborators = api.get_collaborators(project_id=project_id)
    except Exception:
        logger.exception("Failed to get collaborators.")
        raise

    logger.debug("Getting tasks...")
    try:
        tasks = api.get_tasks(project_id=project_id, is_completed=False)
    except Exception:
        logger.exception("Failed to get tasks.")
        raise

    def include_task(due: Optional[Due]) -> bool:
        if due is None:
            return False
        parsed = cast(pendulum.DateTime, pendulum.parse(due.date, tz=tz))
        return parsed <= date_end

    tasks_due = filter(lambda x: include_task(x.due), tasks)

    my_collaborators = {c.id: c.name for c in collaborators}

    my_tasks: list[Activity] = []

    logger.debug("Constructing activity list from tasks...")
    for task in tasks_due:
        assignee_str = "" if task.assignee_id is None else f" [{my_collaborators.get(task.assignee_id)}]"
        summary = task.content + assignee_str
        desc = task.description

        date_start = cast(pendulum.DateTime, pendulum.parse(task.due.date))
        time_start = (
            cast(pendulum.DateTime, pendulum.parse(task.due.datetime)).time()
            if task.due.datetime is not None
            else None
        )

        e = Activity(
            activity_type="task",
            summary=summary,
            date_start=date_start.date(),
            time_start=time_start,
            description=desc
        )
        my_tasks.append(e)

    log_msg = f"Built a list of {len(my_tasks)} tasks."
    logger.debug(log_msg)

    return my_tasks
