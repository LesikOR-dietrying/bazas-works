from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.projects import service
from app.modules.projects.access import get_project
from app.modules.projects.schemas import ProjectFilters, ProjectOption, ProjectRead, ProjectWrite

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/options", response_model=list[ProjectOption])
def project_options(session: Database, user: CurrentUser) -> object:
    return service.project_options(session, user)


@router.get("", response_model=Page[ProjectRead])
def list_projects(
    session: Database, user: CurrentUser, filters: Annotated[ProjectFilters, Query()]
) -> object:
    return service.list_projects(session, user, filters)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(data: ProjectWrite, session: Database, user: CurrentUser) -> object:
    return service.create_project(session, user, data)


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: UUID, session: Database, user: CurrentUser) -> object:
    return get_project(session, project_id, user)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID, data: ProjectWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_project(session, project_id, user, data)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_project(session, project_id, user)
