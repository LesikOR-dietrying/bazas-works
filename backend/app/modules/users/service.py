from uuid import UUID

from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.core.security import hash_password
from app.modules.auth.models import AuthSession
from app.modules.users.models import Role, RoleCode, RoleDefinition, User, UserRole
from app.modules.users.permissions import Capability, has_capability
from app.modules.users.schemas import UserCreate, UserFilters, UserUpdate


def get_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise DomainError(404, "Користувача не знайдено.")
    return user


def list_roles(session: Session) -> list[RoleDefinition]:
    return list(
        session.scalars(
            select(RoleDefinition)
            .where(RoleDefinition.is_active)
            .order_by(RoleDefinition.name, RoleDefinition.id)
        ).all()
    )


def user_options(session: Session, actor: User) -> list[User]:
    statement = select(User).where(User.is_active)
    if not has_capability(actor, Capability.MANAGE_TASKS):
        statement = statement.where(User.id == actor.id)
    return list(session.scalars(statement.order_by(User.full_name, User.id)).all())


def _legacy_role(role_codes: set[RoleCode]) -> Role:
    if RoleCode.ADMINISTRATOR in role_codes:
        return Role.ADMIN
    if RoleCode.PRODUCTION_MANAGER in role_codes:
        return Role.MANAGER
    if role_codes & {RoleCode.ENGINEER, RoleCode.RND_ENGINEER}:
        return Role.ENGINEER
    return Role.EMPLOYEE


def _role_records(session: Session, role_codes: set[RoleCode]) -> dict[RoleCode, RoleDefinition]:
    records = session.scalars(
        select(RoleDefinition).where(
            RoleDefinition.code.in_([code.value for code in role_codes]), RoleDefinition.is_active
        )
    ).all()
    result = {RoleCode(record.code): record for record in records}
    if result.keys() != role_codes:
        raise DomainError(422, "Одна або кілька ролей недоступні.")
    return result


def _assign_roles(
    session: Session, user: User, role_codes: set[RoleCode], actor: User | None
) -> None:
    # A new/edited user may temporarily duplicate a case-insensitive unique key.
    # Resolve roles without flushing so commit_user can translate that conflict to 409.
    with session.no_autoflush:
        records = _role_records(session, role_codes)
    existing = {RoleCode(item.role.code): item for item in user.role_assignments}
    user.role_assignments = [
        existing.get(code)
        or UserRole(role=records[code], assigned_by_id=actor.id if actor else None)
        for code in sorted(role_codes, key=str)
    ]
    user.role = _legacy_role(role_codes)


def commit_user(session: Session, user: User) -> User:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Такий логін або email уже використовується.") from None
    session.refresh(user)
    return user


def create_user(session: Session, data: UserCreate, actor: User | None = None) -> User:
    role_codes = set(data.roles)
    user = User(
        full_name=data.full_name,
        username=data.username.lower(),
        email=str(data.email).lower() if data.email else None,
        role=_legacy_role(role_codes),
        password_hash=hash_password(data.password.get_secret_value()),
    )
    session.add(user)
    _assign_roles(session, user, role_codes, actor)
    return commit_user(session, user)


def list_users(session: Session, filters: UserFilters) -> Page[User]:
    statement = select(User)
    if filters.q:
        pattern = search_pattern(filters.q)
        statement = statement.where(
            or_(
                User.full_name.ilike(pattern),
                User.username.ilike(pattern),
                User.email.ilike(pattern),
            )
        )
    if filters.role:
        statement = statement.where(
            User.id.in_(
                select(UserRole.user_id)
                .join(RoleDefinition)
                .where(RoleDefinition.code == filters.role.value)
            )
        )
    if filters.is_active is not None:
        statement = statement.where(User.is_active == filters.is_active)
    order = User.full_name.asc() if filters.direction == "asc" else User.full_name.desc()
    return paginate(session, statement.order_by(order, User.id), filters)


def update_user(
    session: Session, user_id: UUID, data: UserUpdate, actor: User | None = None
) -> User:
    session.execute(text("SELECT pg_advisory_xact_lock(2948102)"))
    user = get_user(session, user_id)
    role_codes = set(data.roles)
    active_admins = session.scalars(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(RoleDefinition, RoleDefinition.id == UserRole.role_id)
        .where(RoleDefinition.code == RoleCode.ADMINISTRATOR.value, User.is_active)
        .order_by(User.id)
        .with_for_update(of=User)
        .execution_options(populate_existing=True)
    ).all()
    if (
        user in active_admins
        and len(active_admins) == 1
        and (RoleCode.ADMINISTRATOR not in role_codes or not data.is_active)
    ):
        raise DomainError(409, "Не можна вимкнути або забрати роль останнього адміністратора.")
    old_roles = set(user.roles)
    if old_roles != role_codes or user.is_active != data.is_active:
        session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    user.full_name = data.full_name
    user.username = data.username.lower()
    user.email = str(data.email).lower() if data.email else None
    user.is_active = data.is_active
    _assign_roles(session, user, role_codes, actor)
    return commit_user(session, user)


def reset_password(session: Session, user_id: UUID, password: str) -> None:
    user = get_user(session, user_id)
    user.password_hash = hash_password(password)
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    session.commit()


def bootstrap_admin(session: Session, data: UserCreate) -> User:
    session.execute(text("SELECT pg_advisory_xact_lock(2948101)"))
    if session.scalar(select(func.count()).select_from(User)):
        raise DomainError(409, "Користувачі вже існують. Створіть адміністратора через Users.")
    return create_user(session, data.model_copy(update={"roles": [RoleCode.ADMINISTRATOR]}))
