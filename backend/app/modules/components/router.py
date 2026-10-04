from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.components import service
from app.modules.components.schemas import (
    ComponentFilters,
    ComponentOption,
    ComponentRead,
    ComponentWrite,
    UnitOfMeasureRead,
)

router = APIRouter(prefix="/components", tags=["components"])


@router.get("/uoms", response_model=list[UnitOfMeasureRead])
def list_units(session: Database, user: CurrentUser) -> object:
    return service.list_units(session, user)


@router.get("/options", response_model=list[ComponentOption])
def component_options(session: Database, user: CurrentUser) -> object:
    return service.component_options(session, user)


@router.get("", response_model=Page[ComponentRead])
def list_components(
    session: Database, user: CurrentUser, filters: Annotated[ComponentFilters, Query()]
) -> object:
    return service.list_components(session, user, filters)


@router.post("", response_model=ComponentRead, status_code=201)
def create_component(data: ComponentWrite, session: Database, user: CurrentUser) -> object:
    return service.create_component(session, user, data)


@router.get("/{component_id}", response_model=ComponentRead)
def read_component(component_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_component(session, component_id, user)


@router.put("/{component_id}", response_model=ComponentRead)
def update_component(
    component_id: UUID, data: ComponentWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_component(session, component_id, user, data)


@router.delete("/{component_id}", status_code=204)
def delete_component(component_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_component(session, component_id, user)
