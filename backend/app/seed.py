from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.security import hash_password
from app.modules.components.models import Component, ComponentCategory, UnitOfMeasure
from app.modules.files.models import Attachment  # noqa: F401
from app.modules.firmware.models import (  # noqa: F401
    FirmwareArtifact,
    FirmwareRelease,
    FirmwareRequirement,
)
from app.modules.products.models import (
    Product,
    ProductRevision,
    ProductVariant,
    RevisionStatus,
    TrackingMode,
)
from app.modules.projects.models import Project, ProjectMember, ProjectStatus
from app.modules.rnd.models import BranchConfiguration, RDBranch, RNDPromotionRequest  # noqa: F401
from app.modules.routes.models import ProductionRoute, RouteStage, RouteStageDependency
from app.modules.setups.models import ProjectSetup, Setup, SetupComponent, SetupStatus
from app.modules.tasks.models import Priority, Task, TaskStatus
from app.modules.technology.models import (  # noqa: F401
    ChecklistTemplateItem,
    TechnologyCard,
    TechnologyContentBlock,
    TechnologyOperation,
)
from app.modules.tests.models import Test, TestMeasurement, TestStatus, TestType
from app.modules.users.models import Role, RoleCode, RoleDefinition, User, UserRole

SEED_NAMESPACE = UUID("b13a8ca8-37a2-4cf2-b154-1a6f39a843e5")


def seed_id(name: str) -> UUID:
    return uuid5(SEED_NAMESPACE, name)


def _user(
    session: Session,
    key: str,
    username: str,
    name: str,
    email: str,
    role: Role,
    password: str,
) -> User:
    identifier = seed_id(f"user:{key}")
    existing = session.get(User, identifier)
    if existing is not None:
        if existing.username.lower() not in {key.lower(), username.lower()}:
            raise DomainError(409, "ID демонстраційного користувача вже зайнято.")
        return existing
    if session.scalar(select(User.id).where(func.lower(User.username) == username.lower())):
        raise DomainError(409, "Логін демонстраційного користувача вже використовується.")
    if session.scalar(select(User.id).where(func.lower(User.email) == email.lower())):
        raise DomainError(409, "Email демонстраційного користувача вже використовується.")
    user = User(
        id=identifier,
        username=username,
        full_name=name,
        email=email,
        role=role,
        is_active=True,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.flush()
    codes = {
        Role.ADMIN: (RoleCode.ADMINISTRATOR,),
        Role.MANAGER: (RoleCode.PRODUCTION_MANAGER,),
        Role.ENGINEER: (RoleCode.ENGINEER, RoleCode.RND_ENGINEER),
        Role.EMPLOYEE: (),
    }[role]
    definitions = session.scalars(
        select(RoleDefinition).where(RoleDefinition.code.in_(codes))
    ).all()
    user.role_assignments = [UserRole(role=definition) for definition in definitions]
    session.flush()
    return user


def _project(session: Session, key: str, name: str, responsible: User) -> Project:
    identifier = seed_id(f"project:{key}")
    project = session.get(Project, identifier)
    if project:
        return project
    project = Project(
        id=identifier,
        name=name,
        description="Демонстраційний проєкт BAZA для development-середовища.",
        status=ProjectStatus.IN_PROGRESS,
        responsible_user_id=responsible.id,
    )
    session.add(project)
    session.flush()
    return project


def _component(
    session: Session,
    key: str,
    category: ComponentCategory,
    manufacturer: str,
    model: str,
    name: str,
    specifications: dict[str, object],
) -> Component:
    identifier = seed_id(f"component:{key}")
    component = session.get(Component, identifier)
    if component:
        return component
    default_uom_id = session.scalar(select(UnitOfMeasure.id).where(UnitOfMeasure.code == "PCS"))
    if default_uom_id is None:
        raise DomainError(409, "Одиницю виміру PCS не налаштовано.")
    component = Component(
        id=identifier,
        category=category,
        manufacturer=manufacturer,
        model=model,
        name=name,
        description="Development seed data",
        specifications=specifications,
        default_uom_id=default_uom_id,
    )
    session.add(component)
    session.flush()
    return component


def _setup(session: Session, key: str, name: str, version: str, status: SetupStatus) -> Setup:
    identifier = seed_id(f"setup:{key}")
    existing = session.get(Setup, identifier)
    if existing is not None:
        if (existing.name, existing.version) != (name, version):
            raise DomainError(409, "ID демонстраційної конфігурації вже зайнято.")
        return existing
    if session.scalar(select(Setup.id).where(Setup.name == name, Setup.version == version)):
        raise DomainError(409, "Назва й версія демонстраційної конфігурації вже використовується.")
    setup = Setup(
        id=identifier,
        name=name,
        drone_class="15 inch",
        version=version,
        status=status,
        description="Development seed configuration",
        battery_description="12S 40Ah",
        battery_voltage=44.4,
        battery_capacity_ah=40,
        propeller_description="17x6",
        firmware_type="ArduPilot",
        firmware_version="4.5",
    )
    session.add(setup)
    session.flush()
    return setup


def _route_template(
    session: Session,
    key: str,
    code: str,
    name: str,
    category_id: UUID,
    creator_id: UUID,
    stages: tuple[tuple[str, str], ...],
) -> None:
    product_id = seed_id(f"route-product:{key}")
    product = session.get(Product, product_id)
    if product is None:
        if session.scalar(select(Product.id).where(Product.code == code)):
            raise DomainError(409, "Код демонстраційного шаблону маршруту вже використовується.")
        product = Product(
            id=product_id,
            code=code,
            name=name,
            category_id=category_id,
            description="Development route template",
            tracking_mode=TrackingMode.SERIAL,
        )
        session.add(product)
        session.flush()
    variant_id = seed_id(f"route-variant:{key}")
    variant = session.get(ProductVariant, variant_id)
    if variant is None:
        variant = session.scalar(
            select(ProductVariant).where(
                ProductVariant.product_id == product.id,
                ProductVariant.code == "STANDARD",
            )
        )
    if variant is None:
        variant = ProductVariant(
            id=variant_id,
            product_id=product.id,
            code="STANDARD",
            name="Стандартна",
            description="Базова комплектація",
        )
        session.add(variant)
        session.flush()
    revision_id = seed_id(f"route-revision:{key}")
    if session.get(ProductRevision, revision_id) is None:
        session.add(
            ProductRevision(
                id=revision_id,
                product_id=product.id,
                variant_id=variant.id,
                revision_code="TEMPLATE",
                status=RevisionStatus.DRAFT,
                created_by_id=creator_id,
            )
        )
        session.flush()
    route_id = seed_id(f"route:{key}")
    if session.get(ProductionRoute, route_id) is not None:
        return
    session.add(
        ProductionRoute(
            id=route_id,
            revision_id=revision_id,
            version=1,
            name=f"{name}: типовий маршрут",
            description="Editable development template",
        )
    )
    previous_id: UUID | None = None
    for sequence, (stage_code, stage_name) in enumerate(stages):
        stage_id = seed_id(f"route-stage:{key}:{stage_code}")
        session.add(
            RouteStage(
                id=stage_id,
                route_id=route_id,
                code=stage_code,
                name=stage_name,
                sequence=sequence,
            )
        )
        if previous_id is not None:
            session.add(
                RouteStageDependency(
                    id=seed_id(f"route-edge:{key}:{stage_code}"),
                    stage_id=stage_id,
                    predecessor_id=previous_id,
                )
            )
        previous_id = stage_id


def _seed_demo(session: Session, settings: Settings) -> dict[str, int]:
    if settings.app_env != "development":
        raise DomainError(403, "Demo seed дозволений лише у development-середовищі.")
    password = settings.seed_password.get_secret_value()
    if len(password) < 12:
        raise DomainError(422, "Встановіть SEED_PASSWORD щонайменше з 12 символів.")

    admin = _user(
        session,
        "admin",
        "demo-admin",
        "Demo Admin",
        "admin@baza.local",
        Role.ADMIN,
        password,
    )
    engineer = _user(
        session,
        "engineer",
        "demo-engineer",
        "Demo Engineer",
        "engineer@baza.local",
        Role.ENGINEER,
        password,
    )
    employee = _user(
        session,
        "employee",
        "demo-employee",
        "Demo Employee",
        "employee@baza.local",
        Role.EMPLOYEE,
        password,
    )
    drone15 = _project(session, "drone15", "Drone 15", admin)
    drone10 = _project(session, "drone10", "Drone 10", admin)
    retransmitter = _project(session, "retransmitter", "Retransmitter", admin)
    for project in (drone15, drone10, retransmitter):
        for member in (engineer, employee):
            identifier = seed_id(f"member:{project.id}:{member.id}")
            if session.get(ProjectMember, identifier) is None:
                session.add(ProjectMember(id=identifier, project_id=project.id, user_id=member.id))

    motor = _component(
        session,
        "motor6212",
        ComponentCategory.MOTOR,
        "BrotherHobby",
        "Avenger 6212 260KV",
        "BrotherHobby Avenger 6212 260KV",
        {
            "kv": 260,
            "voltage": "12S",
            "weight_g": 240,
            "max_current_a": 80,
            "max_power_w": 3500,
            "recommended_propellers": ["15.5x5.8", "17x6"],
        },
    )
    esc = _component(
        session,
        "esc120",
        ComponentCategory.ESC,
        "Example",
        "ESC 120A",
        "Example ESC 120A",
        {
            "continuous_current_a": 120,
            "burst_current_a": 150,
            "voltage": "6-12S",
            "firmware": "AM32",
        },
    )
    controller = _component(
        session,
        "fc-h743",
        ComponentCategory.FLIGHT_CONTROLLER,
        "Example",
        "H743",
        "H743 Flight Controller",
        {},
    )
    propeller = _component(
        session, "prop-17x6", ComponentCategory.PROPELLER, "Example", "17x6", "17x6 Propeller", {}
    )
    battery = _component(
        session,
        "battery-12s40",
        ComponentCategory.BATTERY,
        "Example",
        "12S 40Ah",
        "12S 40Ah Battery",
        {},
    )
    ready = _setup(session, "drone15-fiber-v3", "Drone 15 Fiber", "V3", SetupStatus.READY)
    development = _setup(session, "drone15-v4", "Drone 15", "V4", SetupStatus.DEVELOPMENT)
    for setup in (ready, development):
        quantities = ((motor, 4), (esc, 1), (controller, 1), (propeller, 4), (battery, 1))
        for component, quantity in quantities:
            identifier = seed_id(f"bom:{setup.id}:{component.id}")
            if session.get(SetupComponent, identifier) is None:
                session.add(
                    SetupComponent(
                        id=identifier,
                        setup_id=setup.id,
                        component_id=component.id,
                        quantity=quantity,
                        position="",
                    )
                )
    for setup in (ready, development):
        identifier = seed_id(f"project-setup:{drone15.id}:{setup.id}")
        if session.get(ProjectSetup, identifier) is None:
            session.add(ProjectSetup(id=identifier, project_id=drone15.id, setup_id=setup.id))

    now = datetime.now(UTC)
    for key, title, assignee, status, priority in (
        (
            "assemble-v4",
            "Зібрати прототип Drone 15 V4",
            employee,
            TaskStatus.IN_PROGRESS,
            Priority.HIGH,
        ),
        ("motor-bench", "Перевірити мотор 6212", engineer, TaskStatus.TESTING, Priority.NORMAL),
        ("telemetry", "Перевірити телеметрію", engineer, TaskStatus.BLOCKED, Priority.HIGH),
    ):
        identifier = seed_id(f"task:{key}")
        if session.get(Task, identifier) is None:
            session.add(
                Task(
                    id=identifier,
                    title=title,
                    project_id=drone15.id,
                    assignee_id=assignee.id,
                    created_by_id=admin.id,
                    status=status,
                    priority=priority,
                    deadline=now + timedelta(days=7),
                )
            )

    test_id = seed_id("test:motor6212-baseline")
    if session.get(Test, test_id) is None:
        session.add(
            Test(
                id=test_id,
                name="Motor 6212 baseline",
                test_type=TestType.MOTOR_BENCH,
                project_id=drone15.id,
                setup_id=ready.id,
                component_id=motor.id,
                performed_by_id=engineer.id,
                test_date=now,
                status=TestStatus.PASS,
                conditions={"voltage": "12S", "propeller": "17x6", "ambient_temperature_c": 22},
                result_summary={"max_thrust_kg": 12.4},
                conclusion="Базове випробування пройдено.",
            )
        )
        session.add_all(
            [
                TestMeasurement(
                    id=seed_id(f"measurement:baseline:{sequence}"),
                    test_id=test_id,
                    sequence=sequence,
                    throttle_percent=throttle,
                    voltage_v=44.4,
                    current_a=current,
                    power_w=power,
                    rpm=rpm,
                    thrust_kg=thrust,
                    efficiency_g_w=efficiency,
                )
                for sequence, throttle, current, power, rpm, thrust, efficiency in (
                    (0, 25, 12, 533, 2100, 2.8, 5.25),
                    (1, 50, 28, 1243, 3600, 6.4, 5.15),
                    (2, 75, 52, 2309, 4900, 9.7, 4.20),
                    (3, 100, 78, 3463, 5800, 12.4, 3.58),
                )
            ]
        )
    _route_template(
        session,
        "uav",
        "TPL-UAV",
        "БПЛА",
        UUID("20000000-0000-0000-0000-000000000001"),
        admin.id,
        (("ASSEMBLY", "Складання"), ("FIRMWARE", "Прошивка"), ("TEST", "Випробування")),
    )
    _route_template(
        session,
        "ground-station",
        "TPL-GCS",
        "Наземна станція",
        UUID("20000000-0000-0000-0000-000000000002"),
        admin.id,
        (("ASSEMBLY", "Складання"), ("CONFIG", "Конфігурація"), ("QA", "Контроль")),
    )
    _route_template(
        session,
        "antenna",
        "TPL-ANT",
        "Антена",
        UUID("20000000-0000-0000-0000-000000000003"),
        admin.id,
        (("ASSEMBLY", "Складання"), ("TUNE", "Налаштування"), ("RF_TEST", "RF тест")),
    )
    session.commit()
    return {"users": 3, "projects": 3, "components": 5, "setups": 2, "tasks": 3, "tests": 1}


def seed_demo(session: Session, settings: Settings) -> dict[str, int]:
    try:
        return _seed_demo(session, settings)
    except Exception:
        session.rollback()
        raise
