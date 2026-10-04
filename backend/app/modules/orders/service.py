from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.models import Component
from app.modules.orders.models import (
    Customer,
    DeviationTest,
    MaterialRequirement,
    Order,
    OrderItem,
    OrderStatus,
    OrderVariant,
    VariantDeviation,
    VariantStatus,
)
from app.modules.orders.schemas import (
    CustomerWrite,
    DeviationWrite,
    ItemWrite,
    MaterialSummary,
    OrderFilters,
    OrderWrite,
    VariantWrite,
)
from app.modules.procurement.models import (
    ProcurementAllocation,
    ProcurementRecord,
    ProcurementStatus,
)
from app.modules.products.models import ProductRevision, ProductRevisionBomItem, RevisionStatus
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def _view(user: User) -> None:
    require_capability(user, Capability.VIEW_PRODUCTION, "Недостатньо прав для Production.")


def _manage(user: User) -> None:
    require_capability(user, Capability.MANAGE_ORDERS, "Недостатньо прав для замовлень.")


def _commit(session: Session, message: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, message) from None


def customers(session: Session, user: User) -> list[Customer]:
    _view(user)
    return list(session.scalars(select(Customer).order_by(Customer.name)))


def released_revisions(session: Session, user: User) -> list[ProductRevision]:
    _view(user)
    return list(
        session.scalars(
            select(ProductRevision)
            .where(ProductRevision.status == RevisionStatus.RELEASED)
            .order_by(ProductRevision.released_at.desc(), ProductRevision.id)
        )
    )


def create_customer(session: Session, user: User, data: CustomerWrite) -> Customer:
    _manage(user)
    row = Customer(**data.model_dump())
    session.add(row)
    _commit(session, "Такий замовник уже існує.")
    session.refresh(row)
    return row


def list_orders(session: Session, user: User, filters: OrderFilters) -> Page[Order]:
    _view(user)
    statement = select(Order)
    if filters.q:
        statement = statement.where(
            or_(
                Order.order_number.ilike(search_pattern(filters.q)),
                Order.recipient.ilike(search_pattern(filters.q)),
            )
        )
    if filters.status:
        statement = statement.where(Order.status == filters.status)
    if filters.customer_id:
        statement = statement.where(Order.customer_id == filters.customer_id)
    return paginate(session, statement.order_by(Order.created_at.desc()), filters)


def get_order(session: Session, order_id: UUID, user: User, *, lock: bool = False) -> Order:
    _view(user)
    statement = select(Order).where(Order.id == order_id)
    if lock:
        statement = statement.with_for_update(of=Order)
    row = session.scalar(statement)
    if row is None:
        raise DomainError(404, "Замовлення не знайдено.")
    return row


def create_order(session: Session, user: User, data: OrderWrite) -> Order:
    _manage(user)
    if session.get(Customer, data.customer_id) is None:
        raise DomainError(422, "Замовника не знайдено.")
    row = Order(**data.model_dump(), created_by_id=user.id)
    session.add(row)
    _commit(session, "Номер замовлення вже використовується.")
    session.refresh(row)
    return row


def items(session: Session, order_id: UUID, user: User) -> list[OrderItem]:
    get_order(session, order_id, user)
    return list(
        session.scalars(
            select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.created_at)
        )
    )


def add_item(session: Session, order_id: UUID, user: User, data: ItemWrite) -> OrderItem:
    _manage(user)
    order = get_order(session, order_id, user, lock=True)
    if order.status != OrderStatus.DRAFT:
        raise DomainError(409, "Рядки змінюються лише у draft замовленні.")
    revision = session.get(ProductRevision, data.product_revision_id)
    if revision is None or revision.status != RevisionStatus.RELEASED:
        raise DomainError(422, "Оберіть випущену ревізію продукту.")
    row = OrderItem(order_id=order_id, product_id=revision.product_id, **data.model_dump())
    session.add(row)
    session.flush()
    session.add(
        OrderVariant(
            order_item_id=row.id,
            name="Standard",
            quantity=row.quantity,
            is_standard=True,
            status=VariantStatus.DRAFT,
        )
    )
    _commit(session, "Такий рядок вже існує.")
    session.refresh(row)
    return row


def variants(session: Session, item_id: UUID, user: User) -> list[OrderVariant]:
    _view(user)
    return list(
        session.scalars(
            select(OrderVariant)
            .where(OrderVariant.order_item_id == item_id)
            .order_by(OrderVariant.created_at)
        )
    )


def split_variant(session: Session, item_id: UUID, user: User, data: VariantWrite) -> OrderVariant:
    _manage(user)
    item = session.get(OrderItem, item_id)
    if item is None:
        raise DomainError(404, "Рядок замовлення не знайдено.")
    get_order(session, item.order_id, user, lock=True)
    standard = session.scalar(
        select(OrderVariant)
        .where(OrderVariant.order_item_id == item_id, OrderVariant.is_standard)
        .with_for_update()
    )
    if (
        standard is None
        or standard.status != VariantStatus.DRAFT
        or data.quantity >= standard.quantity
    ):
        raise DomainError(409, "Недостатньо кількості у standard variant.")
    standard.quantity -= data.quantity
    row = OrderVariant(order_item_id=item_id, status=VariantStatus.DRAFT, **data.model_dump())
    session.add(row)
    _commit(session, "Назва варіанта вже використовується.")
    session.refresh(row)
    return row


def add_deviation(
    session: Session, variant_id: UUID, user: User, data: DeviationWrite
) -> VariantDeviation:
    _manage(user)
    variant = session.get(OrderVariant, variant_id)
    if variant is None or variant.status != VariantStatus.DRAFT:
        raise DomainError(409, "Заміна додається лише до draft variant.")
    item = session.get(OrderItem, variant.order_item_id)
    bom = session.get(ProductRevisionBomItem, data.original_bom_item_id)
    if item is None or bom is None or bom.revision_id != item.product_revision_id:
        raise DomainError(422, "BOM row не належить ревізії замовлення.")
    if session.get(Component, data.replacement_component_id) is None:
        raise DomainError(422, "Компонент заміни не знайдено.")
    values = data.model_dump(exclude={"test_ids"})
    row = VariantDeviation(variant_id=variant_id, requested_by_id=user.id, **values)
    variant.status = VariantStatus.PENDING_APPROVAL
    session.add(row)
    session.flush()
    for test_id in data.test_ids:
        session.add(DeviationTest(deviation_id=row.id, test_id=test_id))
    _commit(session, "Заміна для цього BOM row вже існує.")
    session.refresh(row)
    return row


def approve_deviation(
    session: Session, deviation_id: UUID, user: User, approved: bool
) -> VariantDeviation:
    require_capability(
        user, Capability.APPROVE_DEVIATIONS, "Недостатньо прав для погодження замін."
    )
    row = session.get(VariantDeviation, deviation_id)
    if row is None:
        raise DomainError(404, "Запит на заміну не знайдено.")
    variant = session.get(OrderVariant, row.variant_id)
    assert variant is not None
    if variant.status != VariantStatus.PENDING_APPROVAL:
        raise DomainError(409, "Запит на заміну вже розглянуто.")
    if approved:
        row.approved_by_id = user.id
        row.approved_at = datetime.now(UTC)
        variant.status = VariantStatus.APPROVED
    else:
        variant.status = VariantStatus.REJECTED
    session.commit()
    session.refresh(row)
    return row


def deviations(session: Session, variant_id: UUID, user: User) -> list[VariantDeviation]:
    _view(user)
    if session.get(OrderVariant, variant_id) is None:
        raise DomainError(404, "Варіант не знайдено.")
    return list(
        session.scalars(
            select(VariantDeviation)
            .where(VariantDeviation.variant_id == variant_id)
            .order_by(VariantDeviation.created_at)
        )
    )


def transition_order(session: Session, order_id: UUID, user: User, target: OrderStatus) -> Order:
    _manage(user)
    order = get_order(session, order_id, user, lock=True)
    allowed = {
        OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED: {OrderStatus.MATERIALS, OrderStatus.CANCELLED},
        OrderStatus.MATERIALS: {OrderStatus.CANCELLED},
    }
    if target not in allowed.get(OrderStatus(order.status), set()):
        raise DomainError(409, "Недопустимий перехід статусу замовлення.")
    if target == OrderStatus.CONFIRMED:
        item_rows = list(session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
        if not item_rows:
            raise DomainError(409, "Додайте хоча б один рядок замовлення.")
        item_ids = [item.id for item in item_rows]
        variant_rows = list(
            session.scalars(select(OrderVariant).where(OrderVariant.order_item_id.in_(item_ids)))
        )
        if not variant_rows or any(row.status != VariantStatus.RELEASED for row in variant_rows):
            raise DomainError(409, "Перед підтвердженням випустіть усі варіанти.")
    order.status = target
    session.commit()
    session.refresh(order)
    return order


def release_variants(session: Session, item_id: UUID, user: User) -> list[OrderVariant]:
    _manage(user)
    item = session.get(OrderItem, item_id)
    if item is None:
        raise DomainError(404, "Рядок замовлення не знайдено.")
    rows = variants(session, item_id, user)
    active = [r for r in rows if r.status != VariantStatus.REJECTED]
    if sum(r.quantity for r in active) != item.quantity:
        raise DomainError(409, "Сума активних варіантів має дорівнювати кількості рядка.")
    if any(r.status not in {VariantStatus.DRAFT, VariantStatus.APPROVED} for r in active):
        raise DomainError(409, "Усі заміни мають бути погоджені.")
    for variant in active:
        _generate_requirements(session, item, variant)
        variant.status = VariantStatus.RELEASED
    session.commit()
    return active


def _generate_requirements(session: Session, item: OrderItem, variant: OrderVariant) -> None:
    session.query(MaterialRequirement).filter(MaterialRequirement.variant_id == variant.id).delete()
    deviations = {
        d.original_bom_item_id: d
        for d in session.scalars(
            select(VariantDeviation).where(
                VariantDeviation.variant_id == variant.id, VariantDeviation.approved_at.is_not(None)
            )
        )
    }
    bom = session.scalars(
        select(ProductRevisionBomItem).where(
            ProductRevisionBomItem.revision_id == item.product_revision_id
        )
    ).all()
    for row in bom:
        deviation = deviations.get(row.id)
        quantity = (
            deviation.quantity_per_product if deviation else row.quantity
        ) * variant.quantity
        session.add(
            MaterialRequirement(
                variant_id=variant.id,
                original_bom_item_id=row.id,
                source_deviation_id=deviation.id if deviation else None,
                component_id=deviation.replacement_component_id if deviation else row.component_id,
                uom_id=row.uom_id,
                required_quantity=quantity,
            )
        )


def requirements(session: Session, order_id: UUID, user: User) -> list[MaterialRequirement]:
    get_order(session, order_id, user)
    return list(
        session.scalars(
            select(MaterialRequirement)
            .join(OrderVariant)
            .join(OrderItem)
            .where(OrderItem.order_id == order_id)
        )
    )


def material_summary(session: Session, order_id: UUID, user: User) -> list[MaterialSummary]:
    rows = requirements(session, order_id, user)
    result = []
    for component_id in sorted({r.component_id for r in rows}, key=str):
        required = sum(
            (r.required_quantity for r in rows if r.component_id == component_id), Decimal(0)
        )
        allocations = session.execute(
            select(ProcurementAllocation.quantity, ProcurementRecord.status)
            .join(ProcurementRecord)
            .join(MaterialRequirement)
            .join(OrderVariant)
            .join(OrderItem)
            .where(OrderItem.order_id == order_id, MaterialRequirement.component_id == component_id)
        ).all()
        ordered = sum(
            (q for q, s in allocations if s in {ProcurementStatus.ORDERED, ProcurementStatus.PAID}),
            Decimal(0),
        )
        transit = sum(
            (
                q
                for q, s in allocations
                if s in {ProcurementStatus.IN_TRANSIT, ProcurementStatus.CUSTOMS}
            ),
            Decimal(0),
        )
        result.append(
            MaterialSummary(
                component_id=component_id,
                required=required,
                ordered=ordered,
                in_transit=transit,
                missing=max(Decimal(0), required - ordered - transit),
            )
        )
    return result
