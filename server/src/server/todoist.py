import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import SecretStr
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Due, Task

from server.activity import Activity

logger = logging.getLogger(__name__)

def get_tasks_todoist(api_key: SecretStr, project_id: str, date_end: datetime) -> list[Activity]:

    """
    Returns all tasks within a given Project before the specified end date (i.e. includes overdue tasks).
    """

    tz: timezone = date_end.tzinfo

    api = TodoistAPI(api_key.get_secret_value())

    logger.debug("Querying Todoist.")
    logger.debug("Getting collaborators...")
    try:
        # Get collaborators using the new paginated API
        collaborators_paginator = api.get_collaborators(project_id=project_id)
        # Get all collaborators from the paginator
        collaborators = []
        for collaborator_batch in collaborators_paginator:
            collaborators.extend(collaborator_batch)
    except Exception:
        logger.exception("Failed to get collaborators.")
        raise

    logger.debug("Getting tasks...")
    try:
        # Get tasks using the new paginated API
        tasks_paginator = api.get_tasks(project_id=project_id)
        # Get all tasks from the paginator
        tasks_unfiltered = []
        for task_batch in tasks_paginator:
            tasks_unfiltered.extend(task_batch)
        # Filter out completed tasks - the new API uses is_completed instead of completed_at
        tasks = [task for task in tasks_unfiltered if not task.is_completed]
    except Exception:
        logger.exception("Failed to get tasks.")
        raise

    def include_task(due: Optional[Due]) -> bool:
        return due is not None and due.date <= date_end.date()

    tasks_due: list[Task] = filter(lambda x: include_task(x.due), tasks)

    my_collaborators = {c.id: c.name for c in collaborators}

    my_tasks: list[Activity] = []

    logger.debug("Constructing activity list from tasks...")
    for task in tasks_due:
        # task_id = task.id
        # priority = task.priority
        assignee_str = "" if task.assignee_id is None else f" [{my_collaborators.get(task.assignee_id)}]"
        summary = task.content + assignee_str
        desc = task.description

        e = Activity(
            activity_type="task",
            summary=summary,
            date_start=task.due.date,
            time_start=None, # TODO: fix this hardcoding - this is a union type now https://doist.github.io/todoist-api-python/models/#todoist_api_python.models.Due
            # time_start=datetime.fromisoformat(task.due.datetime).time() if task.due.datetime is not None else None,
            description=desc
        )
        my_tasks.append(e)

    log_msg = f"Built a list of {len(my_tasks)} tasks."
    logger.debug(log_msg)

    return my_tasks
