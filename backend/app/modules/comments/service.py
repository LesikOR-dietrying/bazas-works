from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate, CommentFilters, CommentUpdate
from app.modules.files.access import authorize_owner, may_manage_owned_record
from app.modules.users.models import User

COMMENT_OWNER_FIELDS = ("project_id", "task_id", "setup_id", "test_id", "branch_id")


def owner_values(source: object) -> dict[str, UUID | None]:
    return {field: getattr(source, field) for field in COMMENT_OWNER_FIELDS}


def list_comments(session: Session, user: User, filters: CommentFilters) -> Page[Comment]:
    owners = owner_values(filters)
    authorize_owner(session, user, owners)
    field, value = next((field, value) for field, value in owners.items() if value is not None)
    predicate = getattr(Comment, field) == value
    total = session.scalar(select(func.count()).select_from(Comment).where(predicate)) or 0
    items = session.scalars(
        select(Comment)
        .where(predicate)
        .order_by(Comment.created_at, Comment.id)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).all()
    return Page(items=list(items), total=total, page=filters.page, page_size=filters.page_size)


def create_comment(session: Session, user: User, data: CommentCreate) -> Comment:
    owners = owner_values(data)
    authorize_owner(session, user, owners)
    comment = Comment(author_id=user.id, text=data.text.strip(), **owners)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def get_comment(session: Session, comment_id: UUID, user: User) -> Comment:
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise DomainError(404, "Коментар не знайдено.")
    authorize_owner(session, user, owner_values(comment))
    return comment


def update_comment(session: Session, comment_id: UUID, user: User, data: CommentUpdate) -> Comment:
    comment = get_comment(session, comment_id, user)
    if not may_manage_owned_record(user, comment.author_id):
        raise DomainError(403, "Редагувати коментар може автор, менеджер або адміністратор.")
    comment.text = data.text.strip()
    session.commit()
    session.refresh(comment)
    return comment


def delete_comment(session: Session, comment_id: UUID, user: User) -> None:
    comment = get_comment(session, comment_id, user)
    if not may_manage_owned_record(user, comment.author_id):
        raise DomainError(403, "Видалити коментар може автор, менеджер або адміністратор.")
    session.delete(comment)
    session.commit()
