from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.service import get_component, require_engineer
from app.modules.projects.access import get_project, require_project_manager
from app.modules.setups.models import ProjectSetup, Setup, SetupComponent, SetupStatus
from app.modules.setups.schemas import SetupClone, SetupComponentWrite, SetupFilters, SetupWrite
from app.modules.users.models import User


def get_setup(session: Session, setup_id: UUID, user: User, *, lock: bool = False) -> Setup:
    require_engineer(user)
    statement = select(Setup).where(Setup.id == setup_id)
    if lock:
        statement = statement.with_for_update(of=Setup).execution_options(populate_existing=True)
    setup = session.scalar(statement)
    if setup is None:
        raise DomainError(404, "Конфігурацію не знайдено.")
    return setup


def list_setups(session: Session, user: User, filters: SetupFilters) -> Page[Setup]:
    require_engineer(user)
    statement = select(Setup)
    if filters.q:
        statement = statement.where(Setup.name.ilike(search_pattern(filters.q)))
    if filters.status:
        statement = statement.where(Setup.status == filters.status)
    if filters.project_id:
        get_project(session, filters.project_id, user)
        statement = statement.where(
            Setup.id.in_(
                select(ProjectSetup.setup_id).where(ProjectSetup.project_id == filters.project_id)
            )
        )
    if filters.component_id:
        statement = statement.where(
            Setup.id.in_(
                select(SetupComponent.setup_id).where(
                    SetupComponent.component_id == filters.component_id
                )
            )
        )
    column = getattr(Setup, filters.sort)
    order = column.asc() if filters.direction == "asc" else column.desc()
    return paginate(session, statement.order_by(order, Setup.id), filters)


def setup_options(session: Session, user: User) -> list[Setup]:
    require_engineer(user)
    return list(session.scalars(select(Setup).order_by(Setup.name, Setup.version, Setup.id)).all())


def _save(session: Session, setup: Setup) -> Setup:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Конфігурація з такою назвою та версією вже існує.") from None
    session.refresh(setup)
    return setup


def create_setup(session: Session, user: User, data: SetupWrite) -> Setup:
    require_engineer(user)
    setup = Setup(**data.model_dump())
    session.add(setup)
    return _save(session, setup)


def update_setup(session: Session, setup_id: UUID, user: User, data: SetupWrite) -> Setup:
    setup = get_setup(session, setup_id, user, lock=True)
    values = data.model_dump()
    from app.modules.tests.models import Test

    if any(
        value != getattr(setup, field)
        for field, value in values.items()
        if field not in {"status", "description", "notes"}
    ) and session.scalar(select(Test.id).where(Test.setup_id == setup_id).limit(1)):
        raise DomainError(
            409,
            "Після першого випробування характеристики конфігурації незмінні. "
            "Створіть нову версію.",
        )
    for field, value in values.items():
        setattr(setup, field, value)
    return _save(session, setup)


def clone_setup(session: Session, setup_id: UUID, user: User, data: SetupClone) -> Setup:
    source = get_setup(session, setup_id, user, lock=True)
    values = {
        column.name: getattr(source, column.name)
        for column in Setup.__table__.columns
        if column.name not in {"id", "created_at", "updated_at"}
    }
    values["version"] = data.version
    values["status"] = SetupStatus.DEVELOPMENT
    clone = Setup(**values)
    clone.components = [
        SetupComponent(
            component_id=item.component_id,
            quantity=item.quantity,
            position=item.position,
            notes=item.notes,
        )
        for item in source.components
    ]
    session.add(clone)
    return _save(session, clone)


def delete_setup(session: Session, setup_id: UUID, user: User) -> None:
    setup = get_setup(session, setup_id, user, lock=True)
    try:
        session.delete(setup)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(
            409, "Конфігурація пов’язана з проєктом, прошивкою або історією."
        ) from None


def list_bom(session: Session, setup_id: UUID, user: User) -> list[SetupComponent]:
    get_setup(session, setup_id, user)
    return list(
        session.scalars(
            select(SetupComponent)
            .where(SetupComponent.setup_id == setup_id)
            .order_by(SetupComponent.position, SetupComponent.id)
        ).all()
    )


def _ensure_bom_mutable(session: Session, setup_id: UUID) -> None:
    from app.modules.tests.models import Test

    if session.scalar(select(Test.id).where(Test.setup_id == setup_id).limit(1)):
        raise DomainError(409, "BOM конфігурації з випробуваннями незмінний. Створіть нову версію.")


def _get_bom_item(session: Session, setup_id: UUID, item_id: UUID, user: User) -> SetupComponent:
    get_setup(session, setup_id, user, lock=True)
    _ensure_bom_mutable(session, setup_id)
    item = session.scalar(
        select(SetupComponent)
        .where(SetupComponent.id == item_id, SetupComponent.setup_id == setup_id)
        .with_for_update(of=SetupComponent)
    )
    if item is None:
        raise DomainError(404, "Компонент конфігурації не знайдено.")
    return item


def _commit_bom(session: Session, item: SetupComponent) -> SetupComponent:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Цей компонент уже займає зазначену позицію.") from None
    session.refresh(item)
    return item


def add_bom_item(
    session: Session, setup_id: UUID, user: User, data: SetupComponentWrite
) -> SetupComponent:
    get_setup(session, setup_id, user, lock=True)
    _ensure_bom_mutable(session, setup_id)
    get_component(session, data.component_id, user)
    item = SetupComponent(setup_id=setup_id, **data.model_dump())
    session.add(item)
    return _commit_bom(session, item)


def update_bom_item(
    session: Session, setup_id: UUID, item_id: UUID, user: User, data: SetupComponentWrite
) -> SetupComponent:
    item = _get_bom_item(session, setup_id, item_id, user)
    get_component(session, data.component_id, user)
    for field, value in data.model_dump().items():
        setattr(item, field, value)
    return _commit_bom(session, item)


def delete_bom_item(session: Session, setup_id: UUID, item_id: UUID, user: User) -> None:
    item = _get_bom_item(session, setup_id, item_id, user)
    session.delete(item)
    session.commit()


def project_setups(session: Session, project_id: UUID, user: User) -> list[Setup]:
    require_engineer(user)
    get_project(session, project_id, user)
    return list(
        session.scalars(
            select(Setup)
            .join(ProjectSetup)
            .where(ProjectSetup.project_id == project_id)
            .order_by(Setup.name, Setup.version, Setup.id)
        ).all()
    )


def link_project_setup(session: Session, project_id: UUID, setup_id: UUID, user: User) -> Setup:
    require_project_manager(user)
    get_project(session, project_id, user, lock=True)
    setup = get_setup(session, setup_id, user)
    session.add(ProjectSetup(project_id=project_id, setup_id=setup_id))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Конфігурацію вже прив’язано до проєкту.") from None
    return setup


def unlink_project_setup(session: Session, project_id: UUID, setup_id: UUID, user: User) -> None:
    require_project_manager(user)
    get_project(session, project_id, user, lock=True)
    link = session.scalar(
        select(ProjectSetup)
        .where(ProjectSetup.project_id == project_id, ProjectSetup.setup_id == setup_id)
        .with_for_update(of=ProjectSetup)
    )
    if link is None:
        raise DomainError(404, "Прив’язку не знайдено.")
    try:
        session.delete(link)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Конфігурація використовується у випробуваннях проєкту.") from None
