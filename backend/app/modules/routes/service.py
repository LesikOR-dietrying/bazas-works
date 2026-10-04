from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.products.service import get_revision, require_draft
from app.modules.routes.models import (
    ProductionRoute,
    RouteStage,
    RouteStageDependency,
    RouteStageRole,
)
from app.modules.routes.schemas import RouteWrite, StageWrite
from app.modules.users.models import RoleDefinition, User
from app.modules.users.permissions import Capability, require_capability


def _edit(user: User) -> None:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для маршруту.")


def routes(session: Session, revision_id: UUID, user: User) -> list[ProductionRoute]:
    get_revision(session, revision_id, user)
    return list(
        session.scalars(
            select(ProductionRoute)
            .where(ProductionRoute.revision_id == revision_id)
            .order_by(ProductionRoute.version)
        )
    )


def create_route(
    session: Session, revision_id: UUID, user: User, data: RouteWrite
) -> ProductionRoute:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    row = ProductionRoute(revision_id=revision_id, **data.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def stages(session: Session, route_id: UUID, user: User) -> list[RouteStage]:
    route = session.get(ProductionRoute, route_id)
    if route is None:
        raise DomainError(404, "Маршрут не знайдено.")
    get_revision(session, route.revision_id, user)
    return list(
        session.scalars(
            select(RouteStage).where(RouteStage.route_id == route_id).order_by(RouteStage.sequence)
        )
    )


def add_stage(session: Session, route_id: UUID, user: User, data: StageWrite) -> RouteStage:
    _edit(user)
    route = session.get(ProductionRoute, route_id)
    if route is None:
        raise DomainError(404, "Маршрут не знайдено.")
    require_draft(get_revision(session, route.revision_id, user, lock=True))
    values = data.model_dump(exclude={"role_ids"}, mode="json")
    row = RouteStage(route_id=route_id, **values)
    session.add(row)
    session.flush()
    for role_id in data.role_ids:
        if session.get(RoleDefinition, role_id) is None:
            raise DomainError(422, "Професійну роль не знайдено.")
        session.add(RouteStageRole(stage_id=row.id, role_id=role_id))
    session.commit()
    session.refresh(row)
    return row


def add_dependency(
    session: Session, stage_id: UUID, predecessor_id: UUID, user: User
) -> RouteStageDependency:
    _edit(user)
    stage = session.get(RouteStage, stage_id)
    pred = session.get(RouteStage, predecessor_id)
    if stage is None or pred is None or stage.route_id != pred.route_id:
        raise DomainError(422, "Етапи мають належати одному маршруту.")
    route = session.get(ProductionRoute, stage.route_id)
    assert route is not None
    require_draft(get_revision(session, route.revision_id, user, lock=True))
    edges = list(
        session.execute(
            select(RouteStageDependency.predecessor_id, RouteStageDependency.stage_id)
            .join(RouteStage, RouteStage.id == RouteStageDependency.stage_id)
            .where(RouteStage.route_id == stage.route_id)
        ).all()
    )
    graph: dict[UUID, set[UUID]] = {}
    for source, target in [*edges, (predecessor_id, stage_id)]:
        graph.setdefault(source, set()).add(target)
    seen: set[UUID] = set()
    active: set[UUID] = set()

    def visit(node: UUID) -> bool:
        if node in active:
            return True
        if node in seen:
            return False
        seen.add(node)
        active.add(node)
        if any(visit(n) for n in graph.get(node, set())):
            return True
        active.remove(node)
        return False

    if any(visit(node) for node in list(graph)):
        raise DomainError(409, "Залежність створює цикл маршруту.")
    row = RouteStageDependency(stage_id=stage_id, predecessor_id=predecessor_id)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
