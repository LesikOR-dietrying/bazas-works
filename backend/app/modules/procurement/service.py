from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate
from app.modules.components.models import Component
from app.modules.orders.models import MaterialRequirement
from app.modules.procurement.models import (
    ProcurementAllocation,
    ProcurementRecord,
    ProcurementStatus,
    Supplier,
)
from app.modules.procurement.schemas import (
    AllocationWrite,
    ProcurementFilters,
    ProcurementWrite,
    SupplierWrite,
)
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def _view(user: User) -> None:
    require_capability(user, Capability.VIEW_PRODUCTION, "Недостатньо прав для procurement.")


def _manage(user: User) -> None:
    require_capability(user, Capability.MANAGE_PROCUREMENT, "Недостатньо прав для procurement.")


def suppliers(session: Session, user: User) -> list[Supplier]:
    _view(user)
    return list(session.scalars(select(Supplier).order_by(Supplier.name)))


def create_supplier(session: Session, user: User, data: SupplierWrite) -> Supplier:
    _manage(user)
    row = Supplier(**data.model_dump())
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Такий постачальник вже існує.") from None
    session.refresh(row)
    return row


def records(session: Session, user: User, filters: ProcurementFilters) -> Page[ProcurementRecord]:
    _view(user)
    statement = select(ProcurementRecord)
    if filters.component_id:
        statement = statement.where(ProcurementRecord.component_id == filters.component_id)
    if filters.status:
        statement = statement.where(ProcurementRecord.status == filters.status)
    return paginate(session, statement.order_by(ProcurementRecord.updated_at.desc()), filters)


def create_record(session: Session, user: User, data: ProcurementWrite) -> ProcurementRecord:
    _manage(user)
    if session.get(Component, data.component_id) is None:
        raise DomainError(422, "Компонент не знайдено.")
    if data.supplier_id and session.get(Supplier, data.supplier_id) is None:
        raise DomainError(422, "Постачальника не знайдено.")
    row = ProcurementRecord(created_by_id=user.id, **data.model_dump(mode="json"))
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


_STATUS_TRANSITIONS: dict[ProcurementStatus, frozenset[ProcurementStatus]] = {
    ProcurementStatus.REQUIRED: frozenset(
        {ProcurementStatus.RFQ, ProcurementStatus.ORDERED, ProcurementStatus.ISSUE}
    ),
    ProcurementStatus.RFQ: frozenset({ProcurementStatus.ORDERED, ProcurementStatus.ISSUE}),
    ProcurementStatus.ORDERED: frozenset(
        {ProcurementStatus.PAID, ProcurementStatus.IN_TRANSIT, ProcurementStatus.ISSUE}
    ),
    ProcurementStatus.PAID: frozenset({ProcurementStatus.IN_TRANSIT, ProcurementStatus.ISSUE}),
    ProcurementStatus.IN_TRANSIT: frozenset(
        {ProcurementStatus.CUSTOMS, ProcurementStatus.RECEIVED, ProcurementStatus.ISSUE}
    ),
    ProcurementStatus.CUSTOMS: frozenset({ProcurementStatus.RECEIVED, ProcurementStatus.ISSUE}),
    ProcurementStatus.RECEIVED: frozenset(),
    ProcurementStatus.ISSUE: frozenset(
        {
            ProcurementStatus.RFQ,
            ProcurementStatus.ORDERED,
            ProcurementStatus.PAID,
            ProcurementStatus.IN_TRANSIT,
            ProcurementStatus.CUSTOMS,
            ProcurementStatus.RECEIVED,
        }
    ),
}


def transition_status(
    session: Session, record_id: UUID, user: User, target: ProcurementStatus
) -> ProcurementRecord:
    _manage(user)
    record = session.scalar(
        select(ProcurementRecord)
        .where(ProcurementRecord.id == record_id)
        .with_for_update(of=ProcurementRecord)
    )
    if record is None:
        raise DomainError(404, "Закупівлю не знайдено.")
    current = ProcurementStatus(record.status)
    if target == current:
        return record
    if target not in _STATUS_TRANSITIONS[current]:
        raise DomainError(409, f"Перехід закупівлі {current.value} → {target.value} заборонено.")
    record.status = target
    session.commit()
    session.refresh(record)
    return record


def allocate(
    session: Session, record_id: UUID, user: User, data: AllocationWrite
) -> ProcurementAllocation:
    _manage(user)
    record = session.get(ProcurementRecord, record_id)
    requirement = session.get(MaterialRequirement, data.requirement_id)
    if record is None or requirement is None:
        raise DomainError(404, "Закупівлю або потребу не знайдено.")
    if record.component_id != requirement.component_id:
        raise DomainError(422, "Компонент закупівлі не відповідає потребі.")
    allocated = session.scalar(
        select(func.coalesce(func.sum(ProcurementAllocation.quantity), 0)).where(
            ProcurementAllocation.procurement_record_id == record_id
        )
    )
    if allocated + data.quantity > record.quantity:
        raise DomainError(409, "Розподіл перевищує кількість закупівлі.")
    row = ProcurementAllocation(procurement_record_id=record_id, **data.model_dump(mode="json"))
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
