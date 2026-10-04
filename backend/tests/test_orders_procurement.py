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
    ground_component = _component(auth_client, headers, "Phase 4 ground component")
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
        json={"component_id": original["id"], "quantity": "4", "position": "M1"},
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

    preview = auth_client.get(
        "/api/orders/requirements/preview",
        params={"product_revision_id": revision["id"], "quantity": 100},
    )
    assert preview.status_code == 200, preview.text
    assert Decimal(preview.json()[0]["total_quantity"]) == Decimal("400")

    ground_product_response = auth_client.post(
        "/api/products",
        headers=headers,
        json={
            "code": "PHASE4-GROUND",
            "name": "Phase 4 Ground Station",
            "category_id": categories[0]["id"],
            "description": "Second order line",
            "lifecycle": "DEVELOPMENT",
            "tracking_mode": "SERIAL",
        },
    )
    ground_product = ground_product_response.json()
    ground_revision = auth_client.post(
        f"/api/products/{ground_product['id']}/revisions",
        headers=headers,
        json={"revision_code": "R1", "currency": "UAH"},
    ).json()
    ground_bom = auth_client.post(
        f"/api/products/revisions/{ground_revision['id']}/bom",
        headers=headers,
        json={
            "component_id": ground_component["id"],
            "quantity": "2",
            "position": "GS1",
        },
    )
    assert ground_bom.status_code == 201, ground_bom.text
    for status in ("IN_REVIEW", "RELEASED"):
        response = auth_client.post(
            f"/api/products/revisions/{ground_revision['id']}/status",
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
    stale_version = auth_client.get(f"/api/orders/{order['id']}").json()["draft_version"]

    ground_item_response = auth_client.post(
        f"/api/orders/{order['id']}/items",
        headers=headers,
        json={"product_revision_id": ground_revision["id"], "quantity": 1},
    )
    assert ground_item_response.status_code == 201, ground_item_response.text
    ground_item = ground_item_response.json()
    ground_release = auth_client.post(
        f"/api/orders/items/{ground_item['id']}/release-variants", headers=headers
    )
    assert ground_release.status_code == 200, ground_release.text

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
            "quantity_per_product": "4",
            "reason": "Validated replacement",
        },
    )
    assert deviation_response.status_code == 201, deviation_response.text
    deviation = deviation_response.json()
    pending_release = auth_client.post(
        f"/api/orders/items/{item['id']}/release-variants", headers=headers
    )
    assert pending_release.status_code == 409
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
    assert by_component[original["id"]] == Decimal("360")
    assert by_component[replacement["id"]] == Decimal("40")
    assert by_component[ground_component["id"]] == Decimal("2")
    base_bom = db.scalar(
        select(ProductRevisionBomItem).where(ProductRevisionBomItem.id == bom["id"])
    )
    assert base_bom is not None
    assert str(base_bom.component_id) == original["id"]
    assert base_bom.quantity == Decimal("4")

    cloned = auth_client.post(
        f"/api/products/revisions/{revision['id']}/clone",
        headers=headers,
        json={"revision_code": "R2"},
    )
    assert cloned.status_code == 201, cloned.text
    cloned_revision = cloned.json()
    cloned_bom = auth_client.get(f"/api/products/revisions/{cloned_revision['id']}/bom").json()[0]
    updated_bom = auth_client.put(
        f"/api/products/revisions/{cloned_revision['id']}/bom/{cloned_bom['id']}",
        headers=headers,
        json={
            "component_id": original["id"],
            "quantity": "5",
            "uom_id": cloned_bom["uom_id"],
            "position": cloned_bom["position"],
            "sequence": cloned_bom["sequence"],
            "required": cloned_bom["required"],
            "notes": cloned_bom["notes"],
        },
    )
    assert updated_bom.status_code == 200, updated_bom.text
    for status in ("IN_REVIEW", "RELEASED"):
        response = auth_client.post(
            f"/api/products/revisions/{cloned_revision['id']}/status",
            headers=headers,
            json={"status": status},
        )
        assert response.status_code == 200, response.text
    unchanged = auth_client.get(f"/api/orders/{order['id']}/requirements").json()
    unchanged_by_component = {
        row["component_id"]: Decimal(row["required_quantity"]) for row in unchanged
    }
    assert unchanged_by_component[original["id"]] == Decimal("360")
    assert unchanged_by_component[replacement["id"]] == Decimal("40")

    stale_confirm = auth_client.post(
        f"/api/orders/{order['id']}/status",
        headers=headers,
        json={"status": "CONFIRMED", "expected_draft_version": stale_version},
    )
    assert stale_confirm.status_code == 409
    current_version = auth_client.get(f"/api/orders/{order['id']}").json()["draft_version"]
    confirm = auth_client.post(
        f"/api/orders/{order['id']}/status",
        headers=headers,
        json={"status": "CONFIRMED", "expected_draft_version": current_version},
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
            "quantity": "40",
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
        json={"requirement_id": str(replacement_requirement.id), "quantity": "40"},
    )
    assert allocation.status_code == 201, allocation.text
    materials = auth_client.get(f"/api/orders/{order['id']}/materials").json()
    replacement_summary = next(row for row in materials if row["component_id"] == replacement["id"])
    assert Decimal(replacement_summary["ordered"]) == Decimal("0")
    assert Decimal(replacement_summary["in_transit"]) == Decimal("40")
    assert Decimal(replacement_summary["missing"]) == Decimal("0")


def test_employee_cannot_view_orders(auth_client: TestClient, accounts: dict[str, User]) -> None:
    assert accounts
    sign_in(auth_client, "EMPLOYEE")
    response = auth_client.get("/api/orders")
    assert response.status_code == 403
