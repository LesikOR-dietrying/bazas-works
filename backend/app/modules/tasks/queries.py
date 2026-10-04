from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, case, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.projects.access import visible_projects
from app.modules.projects.models import Project
from app.modules.tasks.models import Priority, Task, TaskStatus
from app.modules.tasks.schemas import TaskFilters
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability


def visible_tasks(user: User) -> Select[tuple[Task]]:
    statement = select(Task)
    if not has_capability(user, Capability.MANAGE_TASKS):
        statement = statement.where(
            Task.assignee_id == user.id,
            Task.project_id.in_(visible_projects(user).with_only_columns(Project.id)),
        )
    return statement


def get_task(session: Session, task_id: UUID, user: User, *, lock: bool = False) -> Task:
    statement = visible_tasks(user).where(Task.id == task_id)
    if lock:
        statement = statement.with_for_update(of=Task).execution_options(populate_existing=True)
    task = session.scalar(statement)
    if task is None:
        raise DomainError(404, "Задачу не знайдено або доступ відсутній.")
    return task


def list_tasks(session: Session, user: User, filters: TaskFilters) -> Page[Task]:
    statement = visible_tasks(user)
    if filters.q:
        statement = statement.where(Task.title.ilike(search_pattern(filters.q)))
    for field in ("assignee_id", "project_id", "branch_id", "status", "priority"):
        value = getattr(filters, field)
        if value is not None:
            statement = statement.where(getattr(Task, field) == value)
    if filters.mine:
        statement = statement.where(Task.assignee_id == user.id)
    if filters.overdue:
        statement = statement.where(
            Task.deadline < datetime.now(UTC), Task.status != TaskStatus.DONE
        )
    column = getattr(Task, filters.sort)
    if filters.sort == "priority":
        column = case(
            {priority.value: index for index, priority in enumerate(Priority)}, value=Task.priority
        )
    order = column.asc() if filters.direction == "asc" else column.desc()
    return paginate(session, statement.order_by(order.nulls_last(), Task.id), filters)
