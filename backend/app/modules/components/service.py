from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.models import Component, UnitOfMeasure
from app.modules.components.schemas import ComponentFilters, ComponentWrite
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def require_engineer(user: User) -> None:
    require_capability(
        user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для інженерних записів."
    )


def get_component(
    session: Session, component_id: UUID, user: User, *, lock: bool = False
) -> Component:
    require_engineer(user)
    statement = select(Component).where(Component.id == component_id)
    if lock:
        statement = statement.with_for_update(of=Component).execution_options(
            populate_existing=True
        )
    component = session.scalar(statement)
    if component is None:
        raise DomainError(404, "Компонент не знайдено.")
    return component


def list_components(session: Session, user: User, filters: ComponentFilters) -> Page[Component]:
    require_engineer(user)
    statement = select(Component)
    if filters.q:
        pattern = search_pattern(filters.q)
        statement = statement.where(
            or_(
                Component.name.ilike(pattern),
                Component.manufacturer.ilike(pattern),
                Component.model.ilike(pattern),
            )
        )
    if filters.category:
        statement = statement.where(Component.category == filters.category)
    column = getattr(Component, filters.sort)
    order = column.asc() if filters.direction == "asc" else column.desc()
    return paginate(session, statement.order_by(order, Component.id), filters)


def component_options(session: Session, user: User) -> list[Component]:
    require_engineer(user)
    return list(session.scalars(select(Component).order_by(Component.name, Component.id)).all())


def list_units(session: Session, user: User) -> list[UnitOfMeasure]:
    require_engineer(user)
    return list(session.scalars(select(UnitOfMeasure).order_by(UnitOfMeasure.code)).all())


def _component_values(session: Session, data: ComponentWrite) -> dict[str, object]:
    values = data.model_dump(mode="json")
    if values["default_uom_id"] is None:
        values["default_uom_id"] = session.scalar(
            select(UnitOfMeasure.id).where(UnitOfMeasure.code == "PCS")
        )
    if (
        values["default_uom_id"] is None
        or session.get(UnitOfMeasure, values["default_uom_id"]) is None
    ):
        raise DomainError(422, "Оберіть чинну одиницю виміру.")
    return values


def create_component(session: Session, user: User, data: ComponentWrite) -> Component:
    require_engineer(user)
    component = Component(**_component_values(session, data))
    session.add(component)
    session.commit()
    session.refresh(component)
    return component


def update_component(
    session: Session, component_id: UUID, user: User, data: ComponentWrite
) -> Component:
    component = get_component(session, component_id, user, lock=True)
    if data.category != component.category:
        from app.modules.setups.models import SetupComponent
        from app.modules.tests.models import Test, TestComponent

        if any(
            session.scalar(select(model.id).where(model.component_id == component_id).limit(1))
            for model in (SetupComponent, Test, TestComponent)
        ):
            raise DomainError(409, "Категорію використаного компонента змінювати не можна.")
    for field, value in _component_values(session, data).items():
        setattr(component, field, value)
    session.commit()
    session.refresh(component)
    return component


def delete_component(session: Session, component_id: UUID, user: User) -> None:
    component = get_component(session, component_id, user, lock=True)
    try:
        session.delete(component)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Компонент використовується в конфігурації або історії.") from None
