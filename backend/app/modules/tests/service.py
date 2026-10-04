from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.models import ComponentCategory
from app.modules.components.service import get_component, require_engineer
from app.modules.firmware.service import get_firmware
from app.modules.projects.access import get_project
from app.modules.rnd.models import RDBranch
from app.modules.setups.models import ProjectSetup
from app.modules.setups.service import get_setup
from app.modules.tests.models import (
    Test,
    TestComponent,
    TestComponentRole,
    TestMeasurement,
    TestStatus,
    TestType,
)
from app.modules.tests.schemas import (
    TestComponentWrite,
    TestFilters,
    TestMeasurementWrite,
    TestWrite,
)
from app.modules.users.models import User


def get_test(session: Session, test_id: UUID, user: User, *, lock: bool = False) -> Test:
    require_engineer(user)
    statement = select(Test).where(Test.id == test_id)
    if lock:
        statement = statement.with_for_update(of=Test).execution_options(populate_existing=True)
    test = session.scalar(statement)
    if test is None:
        raise DomainError(404, "Випробування не знайдено.")
    return test


def list_tests(session: Session, user: User, filters: TestFilters) -> Page[Test]:
    require_engineer(user)
    statement = select(Test)
    if filters.q:
        statement = statement.where(Test.name.ilike(search_pattern(filters.q)))
    for field in ("project_id", "branch_id", "setup_id", "component_id", "test_type", "status"):
        value = getattr(filters, field)
        if value is not None:
            statement = statement.where(getattr(Test, field) == value)
    column = getattr(Test, filters.sort)
    order = column.asc() if filters.direction == "asc" else column.desc()
    return paginate(session, statement.order_by(order, Test.id), filters)


def _lock_references(
    session: Session,
    user: User,
    project_ids: set[UUID],
    setup_ids: set[UUID],
    component_ids: set[UUID],
) -> None:
    for project_id in sorted(project_ids, key=str):
        get_project(session, project_id, user, lock=True)
    for setup_id in sorted(setup_ids, key=str):
        get_setup(session, setup_id, user, lock=True)
    for component_id in sorted(component_ids, key=str):
        get_component(session, component_id, user, lock=True)


def _validate_references(session: Session, user: User, data: TestWrite) -> None:
    if data.branch_id:
        branch = session.get(RDBranch, data.branch_id)
        if branch is None or branch.project_id != data.project_id:
            raise DomainError(422, "Гілка випробування має належати вибраному проєкту.")
    if data.project_id and data.setup_id:
        link = session.scalar(
            select(ProjectSetup.id).where(
                ProjectSetup.project_id == data.project_id,
                ProjectSetup.setup_id == data.setup_id,
            )
        )
        if link is None:
            raise DomainError(422, "Спочатку прив’яжіть конфігурацію до проєкту.")
    if data.firmware_revision_id:
        revision = get_firmware(session, data.firmware_revision_id, user)
        if revision.setup_id != data.setup_id:
            raise DomainError(422, "Ревізія прошивки належить іншій конфігурації.")
    if data.component_id:
        component = get_component(session, data.component_id, user)
        expected = {
            TestType.MOTOR_BENCH: ComponentCategory.MOTOR,
            TestType.ESC_BENCH: ComponentCategory.ESC,
        }.get(data.test_type)
        if expected and component.category != expected:
            raise DomainError(
                422, "Категорія головного компонента не відповідає типу випробування."
            )
    if data.performed_by_id:
        operator = session.get(User, data.performed_by_id)
        if operator is None or not operator.is_active:
            raise DomainError(422, "Оберіть активного виконавця випробування.")


def _commit_test(session: Session, test: Test) -> Test:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Зв’язки випробування змінилися. Оновіть сторінку.") from None
    session.refresh(test)
    return test


def create_test(session: Session, user: User, data: TestWrite) -> Test:
    require_engineer(user)
    _lock_references(
        session,
        user,
        {data.project_id} if data.project_id else set(),
        {data.setup_id} if data.setup_id else set(),
        {data.component_id} if data.component_id else set(),
    )
    _validate_references(session, user, data)
    test = Test(**data.model_dump())
    session.add(test)
    return _commit_test(session, test)


def update_test(session: Session, test_id: UUID, user: User, data: TestWrite) -> Test:
    current = get_test(session, test_id, user)
    prior = {
        field: getattr(current, field)
        for field in (
            "project_id",
            "branch_id",
            "setup_id",
            "component_id",
            "firmware_revision_id",
            "test_type",
            "status",
        )
    }
    _lock_references(
        session,
        user,
        {item for item in (current.project_id, data.project_id) if item},
        {item for item in (current.setup_id, data.setup_id) if item},
        {item for item in (current.component_id, data.component_id) if item},
    )
    test = get_test(session, test_id, user, lock=True)
    if any(getattr(test, field) != value for field, value in prior.items()):
        raise DomainError(409, "Випробування змінено іншим користувачем. Оновіть сторінку.")
    if test.status != TestStatus.PLANNED:
        for field in (
            "project_id",
            "branch_id",
            "setup_id",
            "component_id",
            "firmware_revision_id",
            "test_type",
        ):
            if getattr(data, field) != getattr(test, field):
                raise DomainError(409, "Предмет виконаного випробування незмінний.")
        if data.status == TestStatus.PLANNED:
            raise DomainError(409, "Виконане випробування не можна повернути в чернетку.")
    _validate_references(session, user, data)
    for field, value in data.model_dump().items():
        setattr(test, field, value)
    return _commit_test(session, test)


def delete_test(session: Session, test_id: UUID, user: User) -> None:
    current = get_test(session, test_id, user)
    _lock_references(
        session,
        user,
        {current.project_id} if current.project_id else set(),
        {current.setup_id} if current.setup_id else set(),
        {current.component_id} if current.component_id else set(),
    )
    test = get_test(session, test_id, user, lock=True)
    if test.status != TestStatus.PLANNED:
        raise DomainError(409, "Видаляти можна лише заплановані випробування.")
    try:
        session.delete(test)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Випробування має пов’язану історію.") from None


def list_equipment(session: Session, test_id: UUID, user: User) -> list[TestComponent]:
    get_test(session, test_id, user)
    return list(
        session.scalars(
            select(TestComponent)
            .where(TestComponent.test_id == test_id)
            .order_by(TestComponent.role, TestComponent.id)
        ).all()
    )


def add_equipment(
    session: Session, test_id: UUID, user: User, data: TestComponentWrite
) -> TestComponent:
    get_test(session, test_id, user)
    component = get_component(session, data.component_id, user, lock=True)
    get_test(session, test_id, user, lock=True)
    if data.role != TestComponentRole.OTHER and component.category != data.role:
        raise DomainError(422, "Категорія компонента не відповідає його ролі у випробуванні.")
    item = TestComponent(test_id=test_id, **data.model_dump())
    session.add(item)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Компонент уже додано з цією роллю.") from None
    session.refresh(item)
    return item


def delete_equipment(session: Session, test_id: UUID, item_id: UUID, user: User) -> None:
    get_test(session, test_id, user)
    item = session.scalar(
        select(TestComponent).where(TestComponent.id == item_id, TestComponent.test_id == test_id)
    )
    if item is None:
        raise DomainError(404, "Обладнання випробування не знайдено.")
    get_component(session, item.component_id, user, lock=True)
    get_test(session, test_id, user, lock=True)
    item = session.scalar(
        select(TestComponent)
        .where(TestComponent.id == item_id, TestComponent.test_id == test_id)
        .with_for_update(of=TestComponent)
    )
    if item is None:
        raise DomainError(404, "Обладнання випробування не знайдено.")
    session.delete(item)
    session.commit()


def list_measurements(session: Session, test_id: UUID, user: User) -> list[TestMeasurement]:
    get_test(session, test_id, user)
    return list(
        session.scalars(
            select(TestMeasurement)
            .where(TestMeasurement.test_id == test_id)
            .order_by(TestMeasurement.sequence, TestMeasurement.id)
        ).all()
    )


def _commit_measurement(session: Session, measurement: TestMeasurement) -> TestMeasurement:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(
            409, "Номер вимірювання вже використаний або значення недопустиме."
        ) from None
    session.refresh(measurement)
    return measurement


def add_measurement(
    session: Session, test_id: UUID, user: User, data: TestMeasurementWrite
) -> TestMeasurement:
    get_test(session, test_id, user, lock=True)
    measurement = TestMeasurement(test_id=test_id, **data.model_dump())
    session.add(measurement)
    return _commit_measurement(session, measurement)


def update_measurement(
    session: Session, test_id: UUID, measurement_id: UUID, user: User, data: TestMeasurementWrite
) -> TestMeasurement:
    get_test(session, test_id, user, lock=True)
    measurement = session.scalar(
        select(TestMeasurement)
        .where(TestMeasurement.id == measurement_id, TestMeasurement.test_id == test_id)
        .with_for_update(of=TestMeasurement)
    )
    if measurement is None:
        raise DomainError(404, "Вимірювання не знайдено.")
    for field, value in data.model_dump().items():
        setattr(measurement, field, value)
    return _commit_measurement(session, measurement)


def delete_measurement(session: Session, test_id: UUID, measurement_id: UUID, user: User) -> None:
    get_test(session, test_id, user, lock=True)
    measurement = session.scalar(
        select(TestMeasurement)
        .where(TestMeasurement.id == measurement_id, TestMeasurement.test_id == test_id)
        .with_for_update(of=TestMeasurement)
    )
    if measurement is None:
        raise DomainError(404, "Вимірювання не знайдено.")
    session.delete(measurement)
    session.commit()
