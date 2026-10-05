from uuid import UUID

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.routes import service
from app.modules.routes.schemas import (
    DependencyRead,
    DependencyWrite,
    RouteRead,
    RouteRoleRead,
    RouteWrite,
    StageRead,
    StageWrite,
)

router = APIRouter(prefix="/production-routes", tags=["production-routes"])


@router.get("/roles", response_model=list[RouteRoleRead])
def roles(session: Database, user: CurrentUser) -> object:
    return service.available_roles(session, user)


@router.get("/revisions/{revision_id}", response_model=list[RouteRead])
def routes(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.routes(session, revision_id, user)


@router.post("/revisions/{revision_id}", response_model=RouteRead, status_code=201)
def create(revision_id: UUID, data: RouteWrite, session: Database, user: CurrentUser) -> object:
    return service.create_route(session, revision_id, user, data)


@router.get("/{route_id}/stages", response_model=list[StageRead])
def stages(route_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.stages(session, route_id, user)


@router.post("/{route_id}/stages", response_model=StageRead, status_code=201)
def stage(route_id: UUID, data: StageWrite, session: Database, user: CurrentUser) -> object:
    return service.add_stage(session, route_id, user, data)


@router.post("/stages/{stage_id}/dependencies", response_model=DependencyRead, status_code=201)
def dependency(
    stage_id: UUID, data: DependencyWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_dependency(session, stage_id, data.predecessor_id, user)
