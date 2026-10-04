from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.projects.access import get_project
from app.modules.projects.models import Project
from app.modules.rnd.models import RDBranch
from app.modules.tasks.models import Task, TaskStatus
from app.modules.tasks.queries import get_task, visible_tasks
from app.modules.tasks.schemas import TaskCreate, TaskSummary, TaskUpdate
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability, require_capability


def require_editor(user: User) -> None:
    require_capability(
        user, Capability.MANAGE_TASKS, "Можна змінювати лише статус і результат власних задач."
    )


def validate_assignee(
    session: Session, project: Project, assignee_id: UUID | None, previous: UUID | None = None
) -> None:
    if assignee_id is None:
        return
    user = session.get(User, assignee_id)
    if user is None or (not user.is_active and user.id != previous):
        raise DomainError(422, "Оберіть активного виконавця.")
    members = {member.user_id for member in project.memberships} | {project.responsible_user_id}
    if assignee_id not in members:
        raise DomainError(422, "Спочатку додайте виконавця до учасників проєкту.")


def validate_branch(session: Session, project_id: UUID, branch_id: UUID | None) -> None:
    if branch_id is None:
        return
    branch = session.get(RDBranch, branch_id)
    if branch is None or branch.project_id != project_id:
        raise DomainError(422, "Гілка задачі має належати вибраному проєкту.")


def create_task(session: Session, user: User, data: TaskCreate) -> Task:
    require_editor(user)
    project = get_project(session, data.project_id, user, lock=True)
    validate_assignee(session, project, data.assignee_id)
    validate_branch(session, project.id, data.branch_id)
    task = Task(
        **data.model_dump(),
        created_by_id=user.id,
        completed_at=datetime.now(UTC) if data.status == TaskStatus.DONE else None,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(session: Session, task_id: UUID, user: User, data: TaskUpdate) -> Task:
    if not has_capability(user, Capability.MANAGE_TASKS) and data.model_fields_set - {
        "status",
        "result",
    }:
        raise DomainError(403, "Можна змінювати лише статус і результат власної задачі.")
    # Lock the project before the task: membership edits and assignments share this lock order.
    existing = get_task(session, task_id, user)
    original_project_id = existing.project_id
    target_project_id = (
        data.project_id if "project_id" in data.model_fields_set else existing.project_id
    )
    projects = {
        project_id: get_project(session, project_id, user, lock=True)
        for project_id in sorted({existing.project_id, target_project_id}, key=str)
    }
    task = get_task(session, task_id, user, lock=True)
    if task.project_id != original_project_id:
        raise DomainError(409, "Задачу змінено іншим користувачем. Оновіть сторінку.")
    values = data.model_dump(exclude_unset=True)
    assignee_id = values.get("assignee_id", task.assignee_id)
    branch_id = values.get("branch_id", task.branch_id)
    validate_assignee(session, projects[target_project_id], assignee_id, task.assignee_id)
    validate_branch(session, target_project_id, branch_id)
    if "status" in values and values["status"] != task.status:
        task.completed_at = datetime.now(UTC) if values["status"] == TaskStatus.DONE else None
    for field, value in values.items():
        setattr(task, field, value)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: UUID, user: User) -> None:
    require_editor(user)
    task = get_task(session, task_id, user, lock=True)
    session.delete(task)
    session.commit()


def task_summary(
    session: Session, user: User, project_id: UUID | None = None, mine: bool = True
) -> TaskSummary:
    if project_id:
        get_project(session, project_id, user)
    visible = visible_tasks(user)
    if project_id:
        visible = visible.where(Task.project_id == project_id)
    if mine:
        visible = visible.where(Task.assignee_id == user.id)
    records = visible.with_only_columns(Task.status, Task.deadline, Task.completed_at).subquery()
    now = datetime.now(UTC)
    row = session.execute(
        select(
            func.count(),
            func.count().filter(records.c.status != TaskStatus.DONE),
            func.count().filter(records.c.status != TaskStatus.DONE, records.c.deadline < now),
            func.count().filter(records.c.status == TaskStatus.BLOCKED),
            func.count().filter(records.c.status == TaskStatus.DONE),
            func.count().filter(records.c.completed_at >= now - timedelta(days=7)),
        ).select_from(records)
    ).one()
    return TaskSummary(**dict(zip(TaskSummary.model_fields, row, strict=True)))
