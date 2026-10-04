import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import DomainError
from app.core.security import DUMMY_HASH, decode_token, issue_token, verify_password
from app.modules.auth.models import AuthSession
from app.modules.auth.schemas import Login
from app.modules.users.models import User


def login(session: Session, data: Login, settings: Settings) -> tuple[User, str, str]:
    user = session.scalar(select(User).where(func.lower(User.username) == data.username.lower()))
    valid = verify_password(
        data.password.get_secret_value(), user.password_hash if user else DUMMY_HASH
    )
    if not valid or user is None or not user.is_active:
        raise DomainError(401, "Невірний логін або пароль.")
    now = datetime.now(UTC)
    session.execute(delete(AuthSession).where(AuthSession.expires_at < now))
    record = AuthSession(
        id=uuid4(), user_id=user.id, expires_at=now + timedelta(minutes=settings.session_minutes)
    )
    csrf = secrets.token_urlsafe(32)
    token = issue_token(user.id, record.id, csrf, settings)
    session.add(record)
    session.commit()
    return user, token, csrf


def authenticate(session: Session, token: str, settings: Settings) -> tuple[User, UUID, str]:
    claims = decode_token(token, settings)
    session_id = UUID(str(claims["jti"]))
    record = session.get(AuthSession, session_id)
    if record is None or record.expires_at <= datetime.now(UTC):
        raise DomainError(401, "Сесія завершилась. Увійдіть повторно.")
    if str(record.user_id) != claims["sub"]:
        raise DomainError(401, "Недійсна сесія.")
    user = session.get(User, record.user_id)
    if user is None or not user.is_active:
        raise DomainError(401, "Обліковий запис недоступний.")
    return user, session_id, str(claims["csrf"])


def logout(session: Session, session_id: UUID) -> None:
    session.execute(delete(AuthSession).where(AuthSession.id == session_id))
    session.commit()
