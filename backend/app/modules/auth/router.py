from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.core.security import CSRF_COOKIE, SESSION_COOKIE
from app.modules.auth import service
from app.modules.auth.dependencies import (
    Configuration,
    CurrentUser,
    Database,
    authenticated_session_id,
    require_origin,
)
from app.modules.auth.schemas import Login
from app.modules.auth.throttle import limit_login
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login", response_model=UserRead, dependencies=[Depends(require_origin), Depends(limit_login)]
)
def login(data: Login, response: Response, session: Database, settings: Configuration) -> object:
    user, token, csrf = service.login(session, data, settings)
    for key, value, http_only in [(SESSION_COOKIE, token, True), (CSRF_COOKIE, csrf, False)]:
        response.set_cookie(
            key,
            value,
            httponly=http_only,
            secure=settings.app_env == "production",
            samesite="lax",
            max_age=settings.session_minutes * 60,
            path="/",
        )
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser, response: Response) -> object:
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204)
def logout(
    session_id: Annotated[UUID, Depends(authenticated_session_id)],
    session: Database,
    response: Response,
    settings: Configuration,
) -> None:
    service.logout(session, session_id)
    for key in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            key,
            path="/",
            secure=settings.app_env == "production",
            httponly=key == SESSION_COOKIE,
            samesite="lax",
        )
