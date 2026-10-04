from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.procurement import service
from app.modules.procurement.schemas import (
    AllocationRead,
    AllocationWrite,
    ProcurementFilters,
    ProcurementRead,
    ProcurementStatusWrite,
    ProcurementWrite,
    SupplierRead,
    SupplierWrite,
)

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.get("/suppliers", response_model=list[SupplierRead])
def suppliers(session: Database, user: CurrentUser) -> object:
    return service.suppliers(session, user)


@router.post("/suppliers", response_model=SupplierRead, status_code=201)
def supplier(data: SupplierWrite, session: Database, user: CurrentUser) -> object:
    return service.create_supplier(session, user, data)


@router.get("", response_model=Page[ProcurementRead])
def records(
    session: Database, user: CurrentUser, filters: Annotated[ProcurementFilters, Query()]
) -> object:
    return service.records(session, user, filters)


@router.post("", response_model=ProcurementRead, status_code=201)
def create(data: ProcurementWrite, session: Database, user: CurrentUser) -> object:
    return service.create_record(session, user, data)


@router.post("/{record_id}/status", response_model=ProcurementRead)
def update_status(
    record_id: UUID, data: ProcurementStatusWrite, session: Database, user: CurrentUser
) -> object:
    return service.transition_status(session, record_id, user, data.status)


@router.post("/{record_id}/allocations", response_model=AllocationRead, status_code=201)
def allocation(
    record_id: UUID, data: AllocationWrite, session: Database, user: CurrentUser
) -> object:
    return service.allocate(session, record_id, user, data)
