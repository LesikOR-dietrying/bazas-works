from datetime import date, timedelta
from decimal import Decimal

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.orders.models import MaterialRequirement
from app.modules.products.models import ProductRevisionBomItem
from app.modules.users.models import User

pytestmark = pytest.mark.integration


def _component(client: TestClient, headers: dict[str, str], name: str) -> dict[str, object]:
    uom = client.get("/api/components/uoms").json()[0]
    response = client.post(
        "/api/components",
        headers=headers,
        json={
            "category": "OTHER",
            "name": name,
            "default_uom_id": uom["id"],
            "manufacturer": "BAZA",
            "model": name,
            "description": "",
            "specifications": {},
            "notes": "",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_order_variants_deviation_requirements_and_procurement(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    assert accounts
    headers = sign_in(auth_client, "MANAGER")
    original = _component(auth_client, headers, "Phase 4 original")
    replacement = _component(auth_client, headers, "Phase 4 replacement")
    categories = auth_client.get("/api/products/categories").json()
    product_response = auth_client.post(
        "/api/products",
        headers=headers,
        json={
            "code": "PHASE4-UAV",
            "name": "Phase 4 UAV",
            "category_id": categories[0]["id"],
            "description": "Order integration",
            "lifecycle": "DEVELOPMENT",
            "tracking_mode": "SERIAL",
        },
    )
    product = product_response.json()
    revision_response = auth_client.post(
        f"/api/products/{product['id']}/revisions",
        headers=headers,
        json={"revision_code": "R1", "currency": "UAH"},
    )
    revision = revision_response.json()
    bom_response = auth_client.post(
        f"/api/products/revisions/{revision['id']}/bom",
        headers=headers,
        json={"component_id": original["id"], "quantity": "2", "position": "M1"},
    )
    assert bom_response.status_code == 201, bom_response.text
    bom = bom_response.json()
    for status in ("IN_REVIEW", "RELEASED"):
        response = auth_client.post(
            f"/api/products/revisions/{revision['id']}/status",
            headers=headers,
            json={"status": status},
        )
        assert response.status_code == 200, response.text

    customer_response = auth_client.post(
        "/api/orders/customers", headers=headers, json={"name": "Phase 4 customer"}
    )
    customer = customer_response.json()
    today = date.today()
    order_response = auth_client.post(
        "/api/orders",
        headers=headers,
        json={
            "order_number": "ORD-PHASE4-001",
            "customer_id": customer["id"],
            "recipient": "Integration recipient",
            "destination": "Kyiv",
            "order_date": today.isoformat(),
            "deadline": (today + timedelta(days=30)).isoformat(),
        },
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    item_response = auth_client.post(
        f"/api/orders/{order['id']}/items",
        headers=headers,
        json={"product_revision_id": revision["id"], "quantity": 100},
    )
    assert item_response.status_code == 201, item_response.text
    item = item_response.json()

    split_response = auth_client.post(
        f"/api/orders/items/{item['id']}/variants",
        headers=headers,
        json={"name": "Alternative motors", "quantity": 10},
    )
    assert split_response.status_code == 201, split_response.text
    alternative_variant = split_response.json()
    variants = auth_client.get(f"/api/orders/items/{item['id']}/variants").json()
    assert sorted(row["quantity"] for row in variants) == [10, 90]

    deviation_response = auth_client.post(
        f"/api/orders/variants/{alternative_variant['id']}/deviations",
        headers=headers,
        json={
            "original_bom_item_id": bom["id"],
            "replacement_component_id": replacement["id"],
            "quantity_per_product": "3",
            "reason": "Validated replacement",
        },
    )
    assert deviation_response.status_code == 201, deviation_response.text
    deviation = deviation_response.json()
    approval = auth_client.post(
        f"/api/orders/deviations/{deviation['id']}/approve", headers=headers
    )
    assert approval.status_code == 200, approval.text
    released = auth_client.post(f"/api/orders/items/{item['id']}/release-variants", headers=headers)
    assert released.status_code == 200, released.text
    assert all(row["status"] == "RELEASED" for row in released.json())

    requirements_response = auth_client.get(f"/api/orders/{order['id']}/requirements")
    assert requirements_response.status_code == 200, requirements_response.text
    requirements = requirements_response.json()
    by_component = {row["component_id"]: Decimal(row["required_quantity"]) for row in requirements}
    assert by_component[original["id"]] == Decimal("180")
    assert by_component[replacement["id"]] == Decimal("30")
    base_bom = db.scalar(
        select(ProductRevisionBomItem).where(ProductRevisionBomItem.id == bom["id"])
    )
    assert base_bom is not None
    assert str(base_bom.component_id) == original["id"]
    assert base_bom.quantity == Decimal("2")

    confirm = auth_client.post(
        f"/api/orders/{order['id']}/status", headers=headers, json={"status": "CONFIRMED"}
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "CONFIRMED"

    replacement_requirement = db.scalar(
        select(MaterialRequirement).where(MaterialRequirement.component_id == replacement["id"])
    )
    supplier_response = auth_client.post(
        "/api/procurement/suppliers", headers=headers, json={"name": "Phase 4 supplier"}
    )
    supplier = supplier_response.json()
    procurement_response = auth_client.post(
        "/api/procurement",
        headers=headers,
        json={
            "component_id": replacement["id"],
            "supplier_id": supplier["id"],
            "quantity": "30",
            "currency": "UAH",
            "status": "ORDERED",
        },
    )
    assert procurement_response.status_code == 201, procurement_response.text
    procurement = procurement_response.json()
    paid = auth_client.post(
        f"/api/procurement/{procurement['id']}/status",
        headers=headers,
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "PAID"
    transit = auth_client.post(
        f"/api/procurement/{procurement['id']}/status",
        headers=headers,
        json={"status": "IN_TRANSIT"},
    )
    assert transit.status_code == 200, transit.text
    assert transit.json()["status"] == "IN_TRANSIT"
    invalid_status = auth_client.post(
        f"/api/procurement/{procurement['id']}/status",
        headers=headers,
        json={"status": "REQUIRED"},
    )
    assert invalid_status.status_code == 409
    allocation = auth_client.post(
        f"/api/procurement/{procurement['id']}/allocations",
        headers=headers,
        json={"requirement_id": str(replacement_requirement.id), "quantity": "30"},
    )
    assert allocation.status_code == 201, allocation.text
    materials = auth_client.get(f"/api/orders/{order['id']}/materials").json()
    replacement_summary = next(row for row in materials if row["component_id"] == replacement["id"])
    assert Decimal(replacement_summary["ordered"]) == Decimal("0")
    assert Decimal(replacement_summary["in_transit"]) == Decimal("30")
    assert Decimal(replacement_summary["missing"]) == Decimal("0")


def test_employee_cannot_view_orders(auth_client: TestClient, accounts: dict[str, User]) -> None:
    assert accounts
    sign_in(auth_client, "EMPLOYEE")
    response = auth_client.get("/api/orders")
    assert response.status_code == 403
