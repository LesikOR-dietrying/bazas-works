from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import AdminUser, CurrentUser, Database
from app.modules.users import service
from app.modules.users.schemas import (
    PasswordReset,
    RoleRead,
    UserCreate,
    UserFilters,
    UserOption,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/roles", response_model=list[RoleRead])
def roles(session: Database, user: AdminUser) -> object:
    return service.list_roles(session)


@router.get("/options", response_model=list[UserOption])
def options(session: Database, user: CurrentUser) -> object:
    return service.user_options(session, user)


@router.get("", response_model=Page[UserRead])
def list_users(
    session: Database, user: AdminUser, filters: Annotated[UserFilters, Query()]
) -> object:
    return service.list_users(session, filters)


@router.post("", response_model=UserRead, status_code=201)
def create_user(data: UserCreate, session: Database, user: AdminUser) -> object:
    return service.create_user(session, data, user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, data: UserUpdate, session: Database, user: AdminUser) -> object:
    return service.update_user(session, user_id, data, user)


@router.post("/{user_id}/password", status_code=204)
def reset_password(user_id: UUID, data: PasswordReset, session: Database, user: AdminUser) -> None:
    service.reset_password(session, user_id, data.password.get_secret_value())
