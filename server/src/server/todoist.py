from datetime import datetime, timezone
from typing import Optional

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Due

from server.activity import Activity


def get_tasks_todoist(api_key: str, project_id: int, date_end: datetime) -> list[Activity]:

    tz: timezone = date_end.tzinfo

    api = TodoistAPI(api_key)

    collaborators = api.get_collaborators(project_id=project_id)
    tasks = api.get_tasks(project_id=project_id, is_completed=False)

    def include_task(due: Optional[Due]) -> bool:
        return due is not None and datetime.fromisoformat(due.date).replace(tzinfo=tz) <= date_end

    tasks_due = filter(lambda x: include_task(x.due), tasks)

    my_collaborators = {c.id: c.name for c in collaborators}

    my_tasks: list[Activity] = []

    for task in tasks_due:
        # task_id = task.id
        # priority = task.priority
        assignee_str = "" if task.assignee_id is None else f" [{my_collaborators.get(task.assignee_id)}]"
        summary = task.content + assignee_str
        desc = task.description
        due = task.due.date if task.due.datetime is None else task.due.datetime

        e = Activity(
            activity_type="task",
            summary=summary,
            date_start=datetime.fromisoformat(due),
            description=desc
        )
        my_tasks.append(e)

    return my_tasks
