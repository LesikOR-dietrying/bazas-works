from uuid import UUID

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.production import service
from app.modules.production.schemas import (
    AssignmentWrite,
    CompleteWrite,
    ExecutionDetailRead,
    ExecutionRead,
    LaunchRead,
    OrderProgressRead,
    ProductionItemRead,
    WorkItemRead,
)

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/orders/{order_id}/launch", response_model=LaunchRead)
def launch(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.launch_order(session, order_id, user)


@router.get("/orders/{order_id}/items", response_model=list[ProductionItemRead])
def items(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.order_items(session, order_id, user)


@router.get("/orders/{order_id}/progress", response_model=OrderProgressRead)
def progress(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.order_progress(session, order_id, user)


@router.get("/orders/{order_id}/work", response_model=list[WorkItemRead])
def order_work(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.order_work(session, order_id, user)


@router.get("/my-work", response_model=list[WorkItemRead])
def my_work(session: Database, user: CurrentUser) -> object:
    return service.my_work(session, user)


@router.get("/scan/{identifier}", response_model=ProductionItemRead)
def scan(identifier: str, session: Database, user: CurrentUser) -> object:
    return service.scan(session, identifier, user)


@router.get("/items/{item_id}", response_model=ExecutionDetailRead)
def item(item_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.item_detail(session, item_id, user)


@router.get("/executions/{execution_id}", response_model=ExecutionDetailRead)
def execution(execution_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.execution_detail(session, execution_id, user)


@router.post("/executions/{execution_id}/start", response_model=ExecutionRead)
def start(execution_id: UUID, session: Database, user: CurrentUser) -> object:
    return service._execution_read(service.start(session, execution_id, user))


@router.post("/executions/{execution_id}/complete", response_model=ExecutionRead)
def complete(
    execution_id: UUID, data: CompleteWrite, session: Database, user: CurrentUser
) -> object:
    return service._execution_read(service.complete(session, execution_id, user, data))


@router.patch("/executions/{execution_id}/assignment", response_model=ExecutionRead)
def assign(
    execution_id: UUID, data: AssignmentWrite, session: Database, user: CurrentUser
) -> object:
    return service._execution_read(service.assign(session, execution_id, user, data))
