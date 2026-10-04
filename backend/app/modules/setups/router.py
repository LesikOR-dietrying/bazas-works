from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.setups import service
from app.modules.setups.schemas import (
    SetupClone,
    SetupComponentRead,
    SetupComponentWrite,
    SetupFilters,
    SetupOption,
    SetupRead,
    SetupWrite,
)

router = APIRouter(prefix="/setups", tags=["setups"])
project_router = APIRouter(prefix="/projects/{project_id}/setups", tags=["setups"])


class ProjectSetupWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    setup_id: UUID


@router.get("/options", response_model=list[SetupOption])
def setup_options(session: Database, user: CurrentUser) -> object:
    return service.setup_options(session, user)


@router.get("", response_model=Page[SetupRead])
def list_setups(
    session: Database, user: CurrentUser, filters: Annotated[SetupFilters, Query()]
) -> object:
    return service.list_setups(session, user, filters)


@router.post("", response_model=SetupRead, status_code=201)
def create_setup(data: SetupWrite, session: Database, user: CurrentUser) -> object:
    return service.create_setup(session, user, data)


@router.get("/{setup_id}", response_model=SetupRead)
def read_setup(setup_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_setup(session, setup_id, user)


@router.put("/{setup_id}", response_model=SetupRead)
def update_setup(setup_id: UUID, data: SetupWrite, session: Database, user: CurrentUser) -> object:
    return service.update_setup(session, setup_id, user, data)


@router.delete("/{setup_id}", status_code=204)
def delete_setup(setup_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_setup(session, setup_id, user)


@router.post("/{setup_id}/clone", response_model=SetupRead, status_code=201)
def clone_setup(setup_id: UUID, data: SetupClone, session: Database, user: CurrentUser) -> object:
    return service.clone_setup(session, setup_id, user, data)


@router.get("/{setup_id}/components", response_model=list[SetupComponentRead])
def list_bom(setup_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_bom(session, setup_id, user)


@router.post("/{setup_id}/components", response_model=SetupComponentRead, status_code=201)
def add_bom_item(
    setup_id: UUID, data: SetupComponentWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_bom_item(session, setup_id, user, data)


@router.put("/{setup_id}/components/{item_id}", response_model=SetupComponentRead)
def update_bom_item(
    setup_id: UUID, item_id: UUID, data: SetupComponentWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_bom_item(session, setup_id, item_id, user, data)


@router.delete("/{setup_id}/components/{item_id}", status_code=204)
def delete_bom_item(setup_id: UUID, item_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_bom_item(session, setup_id, item_id, user)


@project_router.get("", response_model=list[SetupOption])
def project_setups(project_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.project_setups(session, project_id, user)


@project_router.post("", response_model=SetupOption, status_code=201)
def link_project_setup(
    project_id: UUID, data: ProjectSetupWrite, session: Database, user: CurrentUser
) -> object:
    return service.link_project_setup(session, project_id, data.setup_id, user)


@project_router.delete("/{setup_id}", status_code=204)
def unlink_project_setup(
    project_id: UUID, setup_id: UUID, session: Database, user: CurrentUser
) -> None:
    service.unlink_project_setup(session, project_id, setup_id, user)
