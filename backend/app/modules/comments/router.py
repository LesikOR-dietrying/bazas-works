from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.comments import service
from app.modules.comments.schemas import (
    CommentCreate,
    CommentFilters,
    CommentRead,
    CommentUpdate,
)

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=Page[CommentRead])
def list_comments(
    session: Database,
    user: CurrentUser,
    filters: Annotated[CommentFilters, Query()],
) -> object:
    return service.list_comments(session, user, filters)


@router.post("", response_model=CommentRead, status_code=201)
def create_comment(data: CommentCreate, session: Database, user: CurrentUser) -> object:
    return service.create_comment(session, user, data)


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: UUID, data: CommentUpdate, session: Database, user: CurrentUser
) -> object:
    return service.update_comment(session, comment_id, user, data)


@router.delete("/{comment_id}", status_code=204)
def delete_comment(comment_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_comment(session, comment_id, user)
