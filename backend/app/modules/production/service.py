import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.files.models import Attachment
from app.modules.orders.models import Order, OrderItem, OrderStatus, OrderVariant, VariantStatus
from app.modules.production.models import (
    ExecutionStatus,
    ProductionItem,
    StageChecklistResult,
    StageEvent,
    StageEventType,
    StageExecution,
)
from app.modules.production.schemas import (
    AssignmentWrite,
    CompleteWrite,
    ContentBlockRead,
    ExecutionDetailRead,
    ExecutionRead,
    LaunchRead,
    OrderProgressRead,
    ProductionItemRead,
    StageProgressRead,
    WorkItemRead,
)
from app.modules.products.models import Product, ProductRevision, TrackingMode
from app.modules.routes.models import (
    ProductionRoute,
    RouteStage,
    RouteStageDependency,
    RouteStageRole,
)
from app.modules.technology.models import (
    ChecklistTemplateItem,
    TechnologyContentBlock,
    TechnologyOperation,
)
from app.modules.users.models import User, UserRole
from app.modules.users.permissions import Capability, has_capability, require_capability


def _view(user: User) -> None:
    require_capability(user, Capability.VIEW_PRODUCTION, "Недостатньо прав для виробництва.")


def _manage(user: User) -> None:
    require_capability(user, Capability.MANAGE_ORDERS, "Недостатньо прав для запуску виробництва.")


def _execution_read(row: StageExecution) -> ExecutionRead:
    return ExecutionRead(
        id=row.id,
        production_item_id=row.production_item_id,
        stage_id=row.stage_id,
        stage_code=row.stage.code,
        stage_name=row.stage.name,
        attempt=row.attempt,
        planned_quantity=row.planned_quantity,
        completed_quantity=row.completed_quantity,
        failed_quantity=row.failed_quantity,
        status=row.status,
        assigned_user_id=row.assigned_user_id,
        started_by_id=row.started_by_id,
        started_at=row.started_at,
        completed_by_id=row.completed_by_id,
        completed_at=row.completed_at,
        result_note=row.result_note,
    )


def _item_read(session: Session, item: ProductionItem) -> ProductionItemRead:
    row = session.execute(
        select(OrderVariant.name, Product.name, ProductRevision.revision_code, Order.order_number)
        .join(OrderItem, OrderItem.id == OrderVariant.order_item_id)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .join(ProductRevision, ProductRevision.id == OrderItem.product_revision_id)
        .where(OrderVariant.id == item.variant_id)
    ).one()
    return ProductionItemRead(
        id=item.id,
        identifier=item.identifier,
        tracking_mode=item.tracking_mode,
        quantity=item.quantity,
        variant_id=item.variant_id,
        variant_name=row[0],
        product_name=row[1],
        revision_code=row[2],
        order_number=row[3],
        qr_value=f"/my-work/items/{item.id}",
    )


def _role_ids(session: Session, user: User) -> set[UUID]:
    return set(session.scalars(select(UserRole.role_id).where(UserRole.user_id == user.id)))


def _eligible(session: Session, execution: StageExecution, user: User) -> bool:
    if has_capability(user, Capability.MANAGE_ORDERS):
        return True
    if execution.assigned_user_id is not None and execution.assigned_user_id != user.id:
        return False
    return _role_eligible(session, execution.stage_id, user)


def _role_eligible(session: Session, stage_id: UUID, user: User) -> bool:
    if has_capability(user, Capability.MANAGE_ORDERS):
        return True
    required = set(
        session.scalars(select(RouteStageRole.role_id).where(RouteStageRole.stage_id == stage_id))
    )
    return not required or bool(required & _role_ids(session, user))


def _get_execution(
    session: Session, execution_id: UUID, user: User, *, lock: bool = False
) -> StageExecution:
    _view(user)
    statement = select(StageExecution).where(StageExecution.id == execution_id)
    if lock:
        statement = statement.with_for_update(of=StageExecution)
    row = session.scalar(statement)
    if row is None:
        raise DomainError(404, "Виробничу операцію не знайдено.")
    if not _eligible(session, row, user):
        raise DomainError(403, "Ця операція недоступна для ваших ролей.")
    return row


def _identifier(prefix: str, order_number: str, suffix: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9-]+", "-", order_number).strip("-")[:60]
    return f"{prefix[:40]}-{clean}-{suffix}"


def launch_order(session: Session, order_id: UUID, user: User) -> LaunchRead:
    _manage(user)
    order = session.scalar(select(Order).where(Order.id == order_id).with_for_update(of=Order))
    if order is None:
        raise DomainError(404, "Замовлення не знайдено.")
    existing = session.scalar(
        select(func.count())
        .select_from(ProductionItem)
        .join(OrderVariant, OrderVariant.id == ProductionItem.variant_id)
        .join(OrderItem, OrderItem.id == OrderVariant.order_item_id)
        .where(OrderItem.order_id == order_id)
    )
    if existing:
        return LaunchRead(order_id=order_id, created_items=0)
    if order.status != OrderStatus.MATERIALS:
        raise DomainError(409, "Запуск дозволений лише зі стану «Забезпечення матеріалами».")
    variants = list(
        session.scalars(
            select(OrderVariant)
            .join(OrderItem)
            .where(OrderItem.order_id == order_id, OrderVariant.status == VariantStatus.RELEASED)
            .order_by(OrderVariant.created_at, OrderVariant.id)
        )
    )
    prepared: list[tuple[OrderVariant, OrderItem, Product, ProductionRoute, list[RouteStage]]]
    prepared = []
    for variant in variants:
        order_item = session.get(OrderItem, variant.order_item_id)
        assert order_item is not None
        product = session.get(Product, order_item.product_id)
        assert product is not None
        route = session.scalar(
            select(ProductionRoute)
            .where(ProductionRoute.revision_id == order_item.product_revision_id)
            .order_by(ProductionRoute.version.desc())
            .limit(1)
        )
        if route is None:
            raise DomainError(409, f"Для {product.name} немає виробничого маршруту.")
        stages = list(
            session.scalars(
                select(RouteStage)
                .where(RouteStage.route_id == route.id)
                .order_by(RouteStage.sequence)
            )
        )
        if not stages:
            raise DomainError(409, f"Маршрут {route.name} не має етапів.")
        prepared.append((variant, order_item, product, route, stages))

    created = 0
    for variant_index, (variant, _order_item, product, route, stages) in enumerate(prepared, 1):
        roots = set(stage.id for stage in stages) - set(
            session.scalars(
                select(RouteStageDependency.stage_id).where(
                    RouteStageDependency.stage_id.in_([stage.id for stage in stages])
                )
            )
        )
        item_specs: list[tuple[str, int]]
        if product.tracking_mode == TrackingMode.SERIAL:
            item_specs = [
                (_identifier(product.code, order.order_number, f"{variant_index:02}-{index:05}"), 1)
                for index in range(1, variant.quantity + 1)
            ]
        else:
            marker = "BATCH" if product.tracking_mode == TrackingMode.BATCH else "QTY"
            item_specs = [
                (
                    _identifier(product.code, order.order_number, f"{marker}-{variant_index:03}"),
                    variant.quantity,
                )
            ]
        for identifier, quantity in item_specs:
            item = ProductionItem(
                variant_id=variant.id,
                route_id=route.id,
                tracking_mode=product.tracking_mode,
                identifier=identifier,
                quantity=quantity,
            )
            session.add(item)
            session.flush()
            for stage in stages:
                session.add(
                    StageExecution(
                        production_item_id=item.id,
                        stage_id=stage.id,
                        planned_quantity=quantity,
                        status=(
                            ExecutionStatus.READY if stage.id in roots else ExecutionStatus.WAITING
                        ),
                    )
                )
            created += 1
    if not created:
        raise DomainError(409, "У замовленні немає випущених варіантів.")
    order.status = OrderStatus.PRODUCTION
    session.commit()
    return LaunchRead(order_id=order_id, created_items=created)


def order_items(session: Session, order_id: UUID, user: User) -> list[ProductionItemRead]:
    _view(user)
    if not has_capability(user, Capability.MANAGE_ORDERS):
        raise DomainError(403, "Перелік виробів доступний керівнику виробництва.")
    rows = session.scalars(
        select(ProductionItem)
        .join(OrderVariant)
        .join(OrderItem)
        .where(OrderItem.order_id == order_id)
        .order_by(ProductionItem.identifier)
    ).all()
    return [_item_read(session, row) for row in rows]


def order_work(session: Session, order_id: UUID, user: User) -> list[WorkItemRead]:
    _view(user)
    if not has_capability(user, Capability.MANAGE_ORDERS):
        raise DomainError(403, "Операції замовлення доступні керівнику виробництва.")
    rows = session.scalars(
        select(StageExecution)
        .join(ProductionItem)
        .join(OrderVariant)
        .join(OrderItem)
        .join(RouteStage, RouteStage.id == StageExecution.stage_id)
        .where(
            OrderItem.order_id == order_id,
            StageExecution.status.in_([ExecutionStatus.READY, ExecutionStatus.IN_PROGRESS]),
        )
        .order_by(RouteStage.sequence, ProductionItem.identifier)
    ).all()
    return [
        WorkItemRead(item=_item_read(session, row.item), execution=_execution_read(row))
        for row in rows
    ]


def my_work(session: Session, user: User) -> list[WorkItemRead]:
    _view(user)
    candidates = session.scalars(
        select(StageExecution)
        .where(
            StageExecution.status.in_([ExecutionStatus.READY, ExecutionStatus.IN_PROGRESS]),
            or_(
                StageExecution.assigned_user_id.is_(None),
                StageExecution.assigned_user_id == user.id,
            ),
        )
        .order_by(StageExecution.updated_at, StageExecution.id)
    ).all()
    return [
        WorkItemRead(item=_item_read(session, row.item), execution=_execution_read(row))
        for row in candidates
        if _eligible(session, row, user)
    ]


def execution_detail(session: Session, execution_id: UUID, user: User) -> ExecutionDetailRead:
    row = _get_execution(session, execution_id, user)
    operation = (
        session.get(TechnologyOperation, row.stage.technology_operation_id)
        if row.stage.technology_operation_id
        else None
    )
    blocks = []
    checklist = []
    if operation:
        blocks = list(
            session.scalars(
                select(TechnologyContentBlock)
                .where(TechnologyContentBlock.operation_id == operation.id)
                .order_by(TechnologyContentBlock.sequence)
            )
        )
        block_ids = [block.id for block in blocks]
        if block_ids:
            checklist = list(
                session.scalars(
                    select(ChecklistTemplateItem)
                    .where(ChecklistTemplateItem.block_id.in_(block_ids))
                    .order_by(ChecklistTemplateItem.sequence)
                )
            )
    return ExecutionDetailRead(
        item=_item_read(session, row.item),
        execution=_execution_read(row),
        instructions=row.stage.instructions,
        operation_name=operation.name if operation else None,
        expected_result=operation.expected_result if operation else "",
        acceptance_criteria=operation.acceptance_criteria if operation else "",
        blocks=[ContentBlockRead.model_validate(block, from_attributes=True) for block in blocks],
        checklist=checklist,
    )


def item_detail(session: Session, item_id: UUID, user: User) -> ExecutionDetailRead:
    _view(user)
    item = session.get(ProductionItem, item_id)
    if item is None:
        raise DomainError(404, "Виріб не знайдено.")
    execution = session.scalar(
        select(StageExecution)
        .join(RouteStage)
        .where(
            StageExecution.production_item_id == item_id,
            StageExecution.status.in_([ExecutionStatus.READY, ExecutionStatus.IN_PROGRESS]),
        )
        .order_by(RouteStage.sequence, StageExecution.attempt.desc())
        .limit(1)
    )
    if execution is None:
        execution = session.scalar(
            select(StageExecution)
            .join(RouteStage)
            .where(StageExecution.production_item_id == item_id)
            .order_by(RouteStage.sequence.desc(), StageExecution.attempt.desc())
            .limit(1)
        )
    if execution is None:
        raise DomainError(404, "Для виробу немає операцій.")
    return execution_detail(session, execution.id, user)


def scan(session: Session, identifier: str, user: User) -> ProductionItemRead:
    _view(user)
    item = session.scalar(select(ProductionItem).where(ProductionItem.identifier == identifier))
    if item is None:
        raise DomainError(404, "Виріб або партію не знайдено.")
    item_detail(session, item.id, user)
    return _item_read(session, item)


def start(session: Session, execution_id: UUID, user: User) -> StageExecution:
    row = _get_execution(session, execution_id, user, lock=True)
    if row.status == ExecutionStatus.IN_PROGRESS and row.started_by_id == user.id:
        return row
    if row.status != ExecutionStatus.READY:
        raise DomainError(409, "Операція ще не готова до старту.")
    now = datetime.now(UTC)
    row.status = ExecutionStatus.IN_PROGRESS
    row.started_by_id = user.id
    row.started_at = now
    session.add(
        StageEvent(
            execution_id=row.id,
            event_type=StageEventType.START,
            quantity=row.planned_quantity - row.completed_quantity,
            actor_id=user.id,
        )
    )
    session.commit()
    session.refresh(row)
    return row


def _checklist_templates(session: Session, row: StageExecution) -> list[ChecklistTemplateItem]:
    operation_id = row.stage.technology_operation_id
    if operation_id is None:
        return []
    return list(
        session.scalars(
            select(ChecklistTemplateItem)
            .join(TechnologyContentBlock)
            .where(TechnologyContentBlock.operation_id == operation_id)
            .order_by(ChecklistTemplateItem.sequence)
        )
    )


def complete(
    session: Session, execution_id: UUID, user: User, data: CompleteWrite
) -> StageExecution:
    existing = session.scalar(
        select(StageEvent).where(StageEvent.idempotency_key == data.idempotency_key)
    )
    if existing is not None:
        if existing.execution_id != execution_id:
            raise DomainError(409, "Ключ повтору вже використано для іншої операції.")
        return _get_execution(session, execution_id, user)
    row = _get_execution(session, execution_id, user, lock=True)
    if row.status != ExecutionStatus.IN_PROGRESS:
        raise DomainError(409, "Спочатку запустіть операцію.")
    remaining = row.planned_quantity - row.completed_quantity - row.failed_quantity
    quantity = data.quantity or remaining
    if quantity > remaining:
        raise DomainError(422, "Кількість перевищує залишок операції.")
    if row.item.tracking_mode != TrackingMode.QUANTITY and quantity != remaining:
        raise DomainError(422, "Серійний виріб або партія завершуються повністю.")
    final = quantity == remaining
    if final:
        templates = _checklist_templates(session, row)
        submitted = {item.template_item_id: item for item in data.checklist}
        if set(submitted) != {item.id for item in templates}:
            raise DomainError(422, "Заповніть усі пункти чекліста.")
        for template in templates:
            answer = submitted[template.id]
            if template.required and not answer.checked:
                raise DomainError(422, f"Обов’язковий пункт не виконано: {template.text}")
            if template.note_required and not answer.note.strip():
                raise DomainError(422, f"Додайте примітку: {template.text}")
            if template.photo_required:
                attachment = (
                    session.get(Attachment, answer.photo_attachment_id)
                    if answer.photo_attachment_id
                    else None
                )
                if attachment is None or attachment.stage_execution_id != row.id:
                    raise DomainError(422, f"Додайте фото: {template.text}")
            session.add(
                StageChecklistResult(
                    execution_id=row.id,
                    template_item_id=template.id,
                    text_snapshot=template.text,
                    required_snapshot=template.required,
                    note_required_snapshot=template.note_required,
                    photo_required_snapshot=template.photo_required,
                    checked=answer.checked,
                    note=answer.note,
                    photo_attachment_id=answer.photo_attachment_id,
                    completed_by_id=user.id,
                )
            )
    row.completed_quantity += quantity
    row.result_note = data.result_note
    if final:
        row.status = ExecutionStatus.PASSED
        row.completed_by_id = user.id
        row.completed_at = datetime.now(UTC)
    session.add(
        StageEvent(
            execution_id=row.id,
            event_type=StageEventType.PASS,
            quantity=quantity,
            reason=data.result_note,
            actor_id=user.id,
            idempotency_key=data.idempotency_key,
        )
    )
    session.flush()
    if final:
        _unlock_successors(session, row)
        _update_order_ready(session, row.item.variant_id)
    session.commit()
    session.refresh(row)
    return row


def _unlock_successors(session: Session, completed: StageExecution) -> None:
    successor_ids = list(
        session.scalars(
            select(RouteStageDependency.stage_id).where(
                RouteStageDependency.predecessor_id == completed.stage_id
            )
        )
    )
    for stage_id in successor_ids:
        successor = session.scalar(
            select(StageExecution)
            .where(
                StageExecution.production_item_id == completed.production_item_id,
                StageExecution.stage_id == stage_id,
                StageExecution.attempt == 1,
            )
            .with_for_update(of=StageExecution)
        )
        if successor is None or successor.status != ExecutionStatus.WAITING:
            continue
        predecessors = list(
            session.scalars(
                select(RouteStageDependency.predecessor_id).where(
                    RouteStageDependency.stage_id == stage_id
                )
            )
        )
        statuses = list(
            session.scalars(
                select(StageExecution.status).where(
                    StageExecution.production_item_id == completed.production_item_id,
                    StageExecution.stage_id.in_(predecessors),
                    StageExecution.attempt == 1,
                )
            )
        )
        if len(statuses) == len(predecessors) and all(
            status == ExecutionStatus.PASSED for status in statuses
        ):
            successor.status = ExecutionStatus.READY


def _update_order_ready(session: Session, variant_id: UUID) -> None:
    order = session.scalar(
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(OrderVariant, OrderVariant.order_item_id == OrderItem.id)
        .where(OrderVariant.id == variant_id)
        .with_for_update(of=Order)
    )
    assert order is not None
    pending = session.scalar(
        select(func.count())
        .select_from(StageExecution)
        .join(ProductionItem)
        .join(OrderVariant)
        .join(OrderItem)
        .where(
            OrderItem.order_id == order.id,
            StageExecution.status != ExecutionStatus.PASSED,
        )
    )
    if not pending:
        order.status = OrderStatus.READY


def assign(
    session: Session, execution_id: UUID, user: User, data: AssignmentWrite
) -> StageExecution:
    _manage(user)
    row = session.scalar(
        select(StageExecution)
        .where(StageExecution.id == execution_id)
        .with_for_update(of=StageExecution)
    )
    if row is None:
        raise DomainError(404, "Виробничу операцію не знайдено.")
    if data.assigned_user_id is not None:
        assignee = session.get(User, data.assigned_user_id)
        if (
            assignee is None
            or not assignee.is_active
            or not _role_eligible(session, row.stage_id, assignee)
        ):
            raise DomainError(422, "Виконавець не має потрібної ролі.")
    row.assigned_user_id = data.assigned_user_id
    session.commit()
    session.refresh(row)
    return row


def order_progress(session: Session, order_id: UUID, user: User) -> OrderProgressRead:
    _view(user)
    if not has_capability(user, Capability.MANAGE_ORDERS):
        raise DomainError(403, "Прогрес замовлення доступний керівнику виробництва.")
    rows = session.execute(
        select(
            RouteStage.code,
            RouteStage.name,
            func.sum(StageExecution.completed_quantity),
            func.sum(StageExecution.planned_quantity),
        )
        .join(StageExecution, StageExecution.stage_id == RouteStage.id)
        .join(ProductionItem)
        .join(OrderVariant)
        .join(OrderItem)
        .where(OrderItem.order_id == order_id)
        .group_by(RouteStage.code, RouteStage.name, RouteStage.sequence)
        .order_by(RouteStage.sequence)
    ).all()
    stages = [
        StageProgressRead(stage_code=code, stage_name=name, completed=done or 0, total=total or 0)
        for code, name, done, total in rows
    ]
    total = sum(stage.total for stage in stages)
    completed = sum(stage.completed for stage in stages)
    return OrderProgressRead(
        order_id=order_id,
        completed=completed,
        total=total,
        percent=round(completed * 100 / total) if total else 0,
        stages=stages,
    )
