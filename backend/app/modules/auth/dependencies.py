import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import get_session
from app.core.errors import DomainError
from app.core.security import CSRF_COOKIE, SESSION_COOKIE
from app.modules.auth import service
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability

Database = Annotated[Session, Depends(get_session)]


def configuration(request: Request) -> Settings:
    return request.app.state.settings


Configuration = Annotated[Settings, Depends(configuration)]


def require_origin(request: Request, settings: Configuration) -> None:
    if request.headers.get("origin", "").rstrip("/") not in settings.trusted_origins:
        raise DomainError(403, "Запит з недозволеного джерела.")


def current_user(request: Request, session: Database, settings: Configuration) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise DomainError(401, "Увійдіть у свій обліковий запис.")
    user, session_id, csrf = service.authenticate(session, token, settings)
    request.state.session_id = session_id
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_origin(request, settings)
        header = request.headers.get("x-csrf-token", "")
        cookie = request.cookies.get(CSRF_COOKIE, "")
        if not secrets.compare_digest(header.encode(), csrf.encode()) or not secrets.compare_digest(
            cookie.encode(), csrf.encode()
        ):
            raise DomainError(403, "Не вдалося підтвердити запит. Оновіть сторінку.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def admin_user(user: CurrentUser) -> User:
    require_capability(user, Capability.ADMIN_USERS, "Доступно лише адміністратору.")
    return user


AdminUser = Annotated[User, Depends(admin_user)]


def authenticated_session_id(request: Request, user: CurrentUser) -> UUID:
    return request.state.session_id
