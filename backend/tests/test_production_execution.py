from datetime import date
from uuid import uuid4

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.files.models import Attachment
from app.modules.orders.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    OrderVariant,
    VariantStatus,
)
from app.modules.production.models import ExecutionStatus, StageEvent, StageEventType
from app.modules.products.models import (
    Product,
    ProductCategory,
    ProductLifecycle,
    ProductRevision,
    ProductVariant,
    RevisionStatus,
    TrackingMode,
)
from app.modules.routes.models import (
    ProductionRoute,
    RouteStage,
    RouteStageDependency,
    RouteStageRole,
)
from app.modules.technology.models import (
    ChecklistTemplateItem,
    ContentBlockType,
    TechnologyCard,
    TechnologyContentBlock,
    TechnologyOperation,
)
from app.modules.users.models import Role, RoleCode, RoleDefinition, User, UserRole

pytestmark = pytest.mark.integration


def _production_order(
    db: Session, manager: User, tracking_mode: TrackingMode, quantity: int, suffix: str
) -> tuple[Order, ChecklistTemplateItem]:
    category = db.scalar(select(ProductCategory).limit(1))
    assert category is not None
    product = Product(
        code=f"EXEC-{suffix}",
        name=f"Execution {suffix}",
        category_id=category.id,
        lifecycle=ProductLifecycle.PRODUCTION,
        tracking_mode=tracking_mode,
    )
    db.add(product)
    db.flush()
    variant = ProductVariant(product_id=product.id, code="STANDARD", name="Стандартна")
    db.add(variant)
    db.flush()
    revision = ProductRevision(
        product_id=product.id,
        variant_id=variant.id,
        revision_code="R1",
        status=RevisionStatus.RELEASED,
        created_by_id=manager.id,
        released_by_id=manager.id,
        released_at=func.now(),
    )
    db.add(revision)
    db.flush()
    product.current_revision_id = revision.id
    variant.current_revision_id = revision.id
    card = TechnologyCard(revision_id=revision.id, title="Assembly")
    db.add(card)
    db.flush()
    operation = TechnologyOperation(card_id=card.id, name="Assemble", sequence=1)
    db.add(operation)
    db.flush()
    block = TechnologyContentBlock(
        operation_id=operation.id,
        block_type=ContentBlockType.CHECKLIST,
        sequence=1,
    )
    db.add(block)
    db.flush()
    checklist = ChecklistTemplateItem(
        block_id=block.id,
        text="Fasteners checked",
        sequence=1,
        required=True,
        note_required=True,
        photo_required=True,
    )
    db.add(checklist)
    route = ProductionRoute(revision_id=revision.id, version=1, name="Main")
    db.add(route)
    db.flush()
    first = RouteStage(
        route_id=route.id,
        code="ASSEMBLY",
        name="Assembly",
        sequence=1,
        technology_operation_id=operation.id,
    )
    second = RouteStage(route_id=route.id, code="READY", name="Ready", sequence=2)
    db.add_all([first, second])
    db.flush()
    db.add(RouteStageDependency(stage_id=second.id, predecessor_id=first.id))
    assembler = db.scalar(select(RoleDefinition).where(RoleDefinition.code == RoleCode.ASSEMBLER))
    assert assembler is not None
    db.add_all(
        [
            RouteStageRole(stage_id=first.id, role_id=assembler.id),
            RouteStageRole(stage_id=second.id, role_id=assembler.id),
        ]
    )
    customer = Customer(name=f"Customer {suffix}")
    db.add(customer)
    db.flush()
    order = Order(
        order_number=f"ORDER-{suffix}",
        customer_id=customer.id,
        order_date=date.today(),
        status=OrderStatus.MATERIALS,
        created_by_id=manager.id,
    )
    db.add(order)
    db.flush()
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_revision_id=revision.id,
        quantity=quantity,
    )
    db.add(order_item)
    db.flush()
    db.add(
        OrderVariant(
            order_item_id=order_item.id,
            name="Standard",
            quantity=quantity,
            is_standard=True,
            status=VariantStatus.RELEASED,
        )
    )
    db.commit()
    return order, checklist


def _make_employee_assembler(db: Session, employee: User) -> None:
    role = db.scalar(select(RoleDefinition).where(RoleDefinition.code == RoleCode.ASSEMBLER))
    assert role is not None
    db.add(UserRole(user_id=employee.id, role_id=role.id))
    db.commit()


def test_serial_stage_workflow_unlocks_dependencies_and_is_idempotent(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    manager = accounts[Role.MANAGER]
    employee = accounts[Role.EMPLOYEE]
    _make_employee_assembler(db, employee)
    order, checklist = _production_order(db, manager, TrackingMode.SERIAL, 2, "SERIAL")

    manager_headers = sign_in(auth_client, "MANAGER")
    launched = auth_client.post(
        f"/api/production/orders/{order.id}/launch", headers=manager_headers
    )
    assert launched.status_code == 200, launched.text
    assert launched.json()["created_items"] == 2
    items = auth_client.get(f"/api/production/orders/{order.id}/items").json()
    assert len(items) == 2
    assert all(item["tracking_mode"] == "SERIAL" and item["quantity"] == 1 for item in items)
    queue = auth_client.get("/api/production/queue?q=ORDER-SERIAL&page=1&page_size=1").json()
    assert queue["total"] == 1
    assert queue["page"] == 1
    assert queue["page_size"] == 1
    assert queue["items"][0]["order_id"] == str(order.id)
    assert queue["items"][0]["planned_quantity"] == 4
    assert queue["items"][0]["completed_quantity"] == 0
    assert queue["items"][0]["active_operations"] == 2
    assert queue["items"][0]["blocked_operations"] == 2
    assert queue["items"][0]["current_item_id"] in {item["id"] for item in items}

    employee_headers = sign_in(auth_client, "EMPLOYEE")
    work = auth_client.get("/api/production/my-work").json()
    assert len(work) == 2
    execution_id = work[0]["execution"]["id"]
    detail = auth_client.get(f"/api/production/executions/{execution_id}").json()
    assert detail["checklist"][0]["text"] == "Fasteners checked"
    started = auth_client.post(
        f"/api/production/executions/{execution_id}/start", headers=employee_headers
    )
    assert started.status_code == 200, started.text
    key = str(uuid4())
    incomplete = auth_client.post(
        f"/api/production/executions/{execution_id}/complete",
        headers=employee_headers,
        json={
            "idempotency_key": key,
            "checklist": [{"template_item_id": str(checklist.id), "checked": True}],
        },
    )
    assert incomplete.status_code == 422
    attachment = Attachment(
        original_filename="proof.jpg",
        stored_filename="proof.jpg",
        mime_type="image/jpeg",
        size=1,
        storage_path=f"phase5/{uuid4()}",
        uploaded_by_id=employee.id,
        stage_execution_id=execution_id,
    )
    db.add(attachment)
    db.commit()
    payload = {
        "idempotency_key": key,
        "result_note": "Done",
        "checklist": [
            {
                "template_item_id": str(checklist.id),
                "checked": True,
                "note": "Verified",
                "photo_attachment_id": str(attachment.id),
            }
        ],
    }
    completed = auth_client.post(
        f"/api/production/executions/{execution_id}/complete",
        headers=employee_headers,
        json=payload,
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == ExecutionStatus.PASSED
    duplicate = auth_client.post(
        f"/api/production/executions/{execution_id}/complete",
        headers=employee_headers,
        json=payload,
    )
    assert duplicate.status_code == 200
    event_count = db.scalar(
        select(func.count())
        .select_from(StageEvent)
        .where(
            StageEvent.execution_id == execution_id,
            StageEvent.event_type == StageEventType.PASS,
        )
    )
    assert event_count == 1
    next_work = auth_client.get("/api/production/my-work").json()
    assert any(
        row["item"]["id"] == work[0]["item"]["id"] and row["execution"]["stage_code"] == "READY"
        for row in next_work
    )
    sign_in(auth_client, "MANAGER")
    progress = auth_client.get(f"/api/production/orders/{order.id}/progress").json()
    assert progress["percent"] == 25


@pytest.mark.parametrize(
    ("mode", "quantity", "expected_items"),
    [(TrackingMode.BATCH, 50, 1), (TrackingMode.QUANTITY, 100, 1)],
)
def test_group_tracking_creates_one_production_item(
    auth_client: TestClient,
    accounts: dict[str, User],
    db: Session,
    mode: TrackingMode,
    quantity: int,
    expected_items: int,
) -> None:
    manager = accounts[Role.MANAGER]
    order, _ = _production_order(db, manager, mode, quantity, mode.value)
    headers = sign_in(auth_client, "MANAGER")
    response = auth_client.post(f"/api/production/orders/{order.id}/launch", headers=headers)
    assert response.status_code == 200, response.text
    items = auth_client.get(f"/api/production/orders/{order.id}/items").json()
    assert len(items) == expected_items
    assert items[0]["quantity"] == quantity
    if mode == TrackingMode.QUANTITY:
        work = auth_client.get("/api/production/my-work").json()
        execution = next(row["execution"] for row in work if row["item"]["id"] == items[0]["id"])
        auth_client.post(f"/api/production/executions/{execution['id']}/start", headers=headers)
        partial = auth_client.post(
            f"/api/production/executions/{execution['id']}/complete",
            headers=headers,
            json={"quantity": 40, "idempotency_key": str(uuid4()), "checklist": []},
        )
        assert partial.status_code == 200, partial.text
        assert partial.json()["status"] == ExecutionStatus.IN_PROGRESS
        assert partial.json()["completed_quantity"] == 40
