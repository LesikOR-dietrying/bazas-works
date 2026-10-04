from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.tasks import queries, service
from app.modules.tasks.schemas import TaskCreate, TaskFilters, TaskRead, TaskSummary, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=Page[TaskRead])
def list_tasks(
    session: Database, user: CurrentUser, filters: Annotated[TaskFilters, Query()]
) -> object:
    return queries.list_tasks(session, user, filters)


@router.get("/summary", response_model=TaskSummary)
def summary(
    session: Database, user: CurrentUser, project_id: UUID | None = None, mine: bool = True
) -> TaskSummary:
    return service.task_summary(session, user, project_id, mine)


@router.post("", response_model=TaskRead, status_code=201)
def create_task(data: TaskCreate, session: Database, user: CurrentUser) -> object:
    return service.create_task(session, user, data)


@router.get("/{task_id}", response_model=TaskRead)
def read_task(task_id: UUID, session: Database, user: CurrentUser) -> object:
    return queries.get_task(session, task_id, user)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, data: TaskUpdate, session: Database, user: CurrentUser) -> object:
    return service.update_task(session, task_id, user, data)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_task(session, task_id, user)
