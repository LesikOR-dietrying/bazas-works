from uuid import UUID

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.technology import service
from app.modules.technology.schemas import (
    BlockRead,
    BlockWrite,
    CardRead,
    CardWrite,
    ChecklistRead,
    ChecklistWrite,
    OperationRead,
    OperationWrite,
    WorkerPreview,
)

router = APIRouter(prefix="/technology", tags=["technology"])


@router.get("/revisions/{revision_id}", response_model=CardRead)
def card(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_card(session, revision_id, user)


@router.post("/revisions/{revision_id}", response_model=CardRead, status_code=201)
def create_card(revision_id: UUID, data: CardWrite, session: Database, user: CurrentUser) -> object:
    return service.create_card(session, revision_id, user, data)


@router.get("/revisions/{revision_id}/operations", response_model=list[OperationRead])
def operations(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.operations(session, revision_id, user)


@router.post("/revisions/{revision_id}/operations", response_model=OperationRead, status_code=201)
def operation(
    revision_id: UUID, data: OperationWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_operation(session, revision_id, user, data)


@router.put("/operations/{operation_id}", response_model=OperationRead)
def update_operation(
    operation_id: UUID, data: OperationWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_operation(session, operation_id, user, data)


@router.delete("/operations/{operation_id}", status_code=204)
def delete_operation(operation_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_operation(session, operation_id, user)


@router.post("/operations/{operation_id}/blocks", response_model=BlockRead, status_code=201)
def block(operation_id: UUID, data: BlockWrite, session: Database, user: CurrentUser) -> object:
    return service.add_block(session, operation_id, user, data)


@router.put("/blocks/{block_id}", response_model=BlockRead)
def update_block(block_id: UUID, data: BlockWrite, session: Database, user: CurrentUser) -> object:
    return service.update_block(session, block_id, user, data)


@router.delete("/blocks/{block_id}", status_code=204)
def delete_block(block_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_block(session, block_id, user)


@router.post("/blocks/{block_id}/checklist", response_model=ChecklistRead, status_code=201)
def checklist(block_id: UUID, data: ChecklistWrite, session: Database, user: CurrentUser) -> object:
    return service.add_checklist(session, block_id, user, data)


@router.put("/checklist/{item_id}", response_model=ChecklistRead)
def update_checklist(
    item_id: UUID, data: ChecklistWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_checklist(session, item_id, user, data)


@router.delete("/checklist/{item_id}", status_code=204)
def delete_checklist(item_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_checklist(session, item_id, user)


@router.get("/revisions/{revision_id}/preview", response_model=WorkerPreview)
def preview(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.preview(session, revision_id, user)
