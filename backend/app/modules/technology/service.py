from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.products.service import get_revision, require_draft
from app.modules.technology.models import (
    ChecklistTemplateItem,
    ContentBlockType,
    TechnologyCard,
    TechnologyContentBlock,
    TechnologyOperation,
)
from app.modules.technology.schemas import (
    BlockWrite,
    CardWrite,
    ChecklistWrite,
    OperationPreview,
    OperationWrite,
    WorkerPreview,
)
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def _edit(user: User) -> None:
    require_capability(
        user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для технологічної карти."
    )


def get_card(session: Session, revision_id: UUID, user: User) -> TechnologyCard:
    get_revision(session, revision_id, user)
    card = session.scalar(select(TechnologyCard).where(TechnologyCard.revision_id == revision_id))
    if card is None:
        raise DomainError(404, "Технологічну карту не знайдено.")
    return card


def create_card(session: Session, revision_id: UUID, user: User, data: CardWrite) -> TechnologyCard:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    card = TechnologyCard(revision_id=revision_id, **data.model_dump())
    session.add(card)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Технологічна карта вже існує.") from None
    session.refresh(card)
    return card


def operations(session: Session, revision_id: UUID, user: User) -> list[TechnologyOperation]:
    card = get_card(session, revision_id, user)
    return list(
        session.scalars(
            select(TechnologyOperation)
            .where(TechnologyOperation.card_id == card.id)
            .order_by(TechnologyOperation.sequence)
        )
    )


def add_operation(
    session: Session, revision_id: UUID, user: User, data: OperationWrite
) -> TechnologyOperation:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    card = get_card(session, revision_id, user)
    row = TechnologyOperation(card_id=card.id, **data.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def update_operation(
    session: Session, operation_id: UUID, user: User, data: OperationWrite
) -> TechnologyOperation:
    _edit(user)
    row, revision_id = _operation_revision(session, operation_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    _commit(session, "Операція з таким порядком уже існує.")
    session.refresh(row)
    return row


def delete_operation(session: Session, operation_id: UUID, user: User) -> None:
    _edit(user)
    row, revision_id = _operation_revision(session, operation_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    session.delete(row)
    session.commit()


def add_block(
    session: Session, operation_id: UUID, user: User, data: BlockWrite
) -> TechnologyContentBlock:
    _edit(user)
    operation = session.get(TechnologyOperation, operation_id)
    if operation is None:
        raise DomainError(404, "Операцію не знайдено.")
    card = session.get(TechnologyCard, operation.card_id)
    assert card is not None
    require_draft(get_revision(session, card.revision_id, user, lock=True))
    _validate_block(data)
    row = TechnologyContentBlock(operation_id=operation_id, **data.model_dump(mode="json"))
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def update_block(
    session: Session, block_id: UUID, user: User, data: BlockWrite
) -> TechnologyContentBlock:
    _edit(user)
    row, revision_id = _block_revision(session, block_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    _validate_block(data)
    for key, value in data.model_dump(mode="json").items():
        setattr(row, key, value)
    _commit(session, "Блок з таким порядком уже існує.")
    session.refresh(row)
    return row


def delete_block(session: Session, block_id: UUID, user: User) -> None:
    _edit(user)
    row, revision_id = _block_revision(session, block_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    session.delete(row)
    session.commit()


def add_checklist(
    session: Session, block_id: UUID, user: User, data: ChecklistWrite
) -> ChecklistTemplateItem:
    _edit(user)
    block = session.get(TechnologyContentBlock, block_id)
    if block is None or block.block_type != ContentBlockType.CHECKLIST:
        raise DomainError(422, "Пункт можна додати лише до блоку чекліста.")
    operation = session.get(TechnologyOperation, block.operation_id)
    assert operation is not None
    card = session.get(TechnologyCard, operation.card_id)
    assert card is not None
    require_draft(get_revision(session, card.revision_id, user, lock=True))
    row = ChecklistTemplateItem(block_id=block_id, **data.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def update_checklist(
    session: Session, item_id: UUID, user: User, data: ChecklistWrite
) -> ChecklistTemplateItem:
    _edit(user)
    row = session.get(ChecklistTemplateItem, item_id)
    if row is None:
        raise DomainError(404, "Пункт чекліста не знайдено.")
    _, revision_id = _block_revision(session, row.block_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    _commit(session, "Пункт з таким порядком уже існує.")
    session.refresh(row)
    return row


def delete_checklist(session: Session, item_id: UUID, user: User) -> None:
    _edit(user)
    row = session.get(ChecklistTemplateItem, item_id)
    if row is None:
        raise DomainError(404, "Пункт чекліста не знайдено.")
    _, revision_id = _block_revision(session, row.block_id)
    require_draft(get_revision(session, revision_id, user, lock=True))
    session.delete(row)
    session.commit()


def _commit(session: Session, message: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, message) from None


def _operation_revision(session: Session, operation_id: UUID) -> tuple[TechnologyOperation, UUID]:
    operation = session.get(TechnologyOperation, operation_id)
    if operation is None:
        raise DomainError(404, "Операцію не знайдено.")
    card = session.get(TechnologyCard, operation.card_id)
    assert card is not None
    return operation, card.revision_id


def _block_revision(session: Session, block_id: UUID) -> tuple[TechnologyContentBlock, UUID]:
    block = session.get(TechnologyContentBlock, block_id)
    if block is None:
        raise DomainError(404, "Блок не знайдено.")
    _, revision_id = _operation_revision(session, block.operation_id)
    return block, revision_id


def _validate_block(data: BlockWrite) -> None:
    if (
        data.block_type
        in {
            ContentBlockType.IMAGE,
            ContentBlockType.FILE,
            ContentBlockType.VIDEO,
            ContentBlockType.ANNOTATED_IMAGE,
        }
        and data.attachment_id is None
    ):
        raise DomainError(422, "Для цього блоку потрібен файл.")


def preview(session: Session, revision_id: UUID, user: User) -> WorkerPreview:
    card = get_card(session, revision_id, user)
    result = []
    for operation in operations(session, revision_id, user):
        blocks = list(
            session.scalars(
                select(TechnologyContentBlock)
                .where(TechnologyContentBlock.operation_id == operation.id)
                .order_by(TechnologyContentBlock.sequence)
            )
        )
        ids = [block.id for block in blocks]
        items = (
            []
            if not ids
            else list(
                session.scalars(
                    select(ChecklistTemplateItem)
                    .where(ChecklistTemplateItem.block_id.in_(ids))
                    .order_by(ChecklistTemplateItem.sequence)
                )
            )
        )
        base = {
            "id": operation.id,
            "card_id": operation.card_id,
            "name": operation.name,
            "sequence": operation.sequence,
            "expected_result": operation.expected_result,
            "acceptance_criteria": operation.acceptance_criteria,
            "created_at": operation.created_at,
            "updated_at": operation.updated_at,
            "blocks": blocks,
            "checklist_items": items,
        }
        result.append(OperationPreview.model_validate(base))
    return WorkerPreview(card=card, operations=result)
