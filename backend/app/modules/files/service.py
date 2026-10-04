import logging
from collections.abc import Iterator
from contextlib import closing
from pathlib import PurePath
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page
from app.modules.files.access import OWNER_FIELDS, authorize_owner, may_manage_owned_record
from app.modules.files.models import Attachment
from app.modules.files.schemas import AttachmentFilters, OwnerReference
from app.modules.files.storage import Storage
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def owner_values(source: object) -> dict[str, UUID | None]:
    return {field: getattr(source, field) for field in OWNER_FIELDS}


def _safe_filename(filename: str | None) -> str:
    candidate = (filename or "file").replace("\\", "/").split("/")[-1].strip()
    candidate = PurePath(candidate).name[:500]
    return candidate or "file"


def list_files(session: Session, user: User, filters: AttachmentFilters) -> Page[Attachment]:
    owners = owner_values(filters)
    authorize_owner(session, user, owners)
    field, value = next((field, value) for field, value in owners.items() if value is not None)
    statement = (
        select(Attachment)
        .where(getattr(Attachment, field) == value)
        .order_by(Attachment.created_at.desc(), Attachment.id)
    )
    total = session.scalar(
        select(func.count()).select_from(Attachment).where(getattr(Attachment, field) == value)
    )
    items = session.scalars(
        statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
    ).all()
    return Page(items=list(items), total=total or 0, page=filters.page, page_size=filters.page_size)


def create_file(
    session: Session,
    user: User,
    owner: OwnerReference,
    filename: str | None,
    mime_type: str | None,
    stream: BinaryIO,
    storage: Storage,
    max_bytes: int,
) -> Attachment:
    owners = owner_values(owner)
    authorize_owner(session, user, owners)
    stored = storage.put(stream, max_bytes)
    attachment = Attachment(
        original_filename=_safe_filename(filename),
        stored_filename=stored.key,
        mime_type=(mime_type or "application/octet-stream")[:255],
        size=stored.size,
        storage_path=stored.key,
        uploaded_by_id=user.id,
        **owners,
    )
    try:
        session.add(attachment)
        session.commit()
    except Exception:
        session.rollback()
        try:
            storage.delete(stored.key)
        except Exception:
            logger.exception("Failed to remove storage object after attachment transaction failure")
        raise
    session.refresh(attachment)
    return attachment


def get_file(session: Session, attachment_id: UUID, user: User) -> Attachment:
    attachment = session.get(Attachment, attachment_id)
    if attachment is None:
        raise DomainError(404, "Файл не знайдено.")
    authorize_owner(session, user, owner_values(attachment))
    return attachment


def stream_file(stream: BinaryIO) -> Iterator[bytes]:
    with closing(stream):
        while chunk := stream.read(1024 * 1024):
            yield chunk


def delete_file(session: Session, attachment_id: UUID, user: User, storage: Storage) -> None:
    attachment = get_file(session, attachment_id, user)
    if not may_manage_owned_record(user, attachment.uploaded_by_id):
        raise DomainError(403, "Видалити файл може автор, менеджер або адміністратор.")
    storage_path = attachment.storage_path
    try:
        session.delete(attachment)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Файл використовується іншими записами.") from None
    storage.delete(storage_path)
