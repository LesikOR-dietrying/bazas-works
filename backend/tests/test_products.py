import pytest
from conftest import sign_in
from fastapi.testclient import TestClient

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def test_product_revision_lifecycle_and_released_immutability(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    assert accounts
    headers = sign_in(auth_client, "MANAGER")
    categories = auth_client.get("/api/products/categories").json()
    product_response = auth_client.post(
        "/api/products",
        headers=headers,
        json={
            "code": "UAV-INTEGRATION",
            "name": "Integration UAV",
            "category_id": categories[0]["id"],
            "description": "Phase 3 verification",
            "lifecycle": "DEVELOPMENT",
            "tracking_mode": "SERIAL",
        },
    )
    assert product_response.status_code == 201, product_response.text
    product = product_response.json()
    revision_response = auth_client.post(
        f"/api/products/{product['id']}/revisions",
        headers=headers,
        json={
            "revision_code": "R1",
            "technical_characteristics": {"range_km": 20},
            "standard_cost": "1200.00",
            "currency": "UAH",
            "revision_instructions": "Initial release",
        },
    )
    assert revision_response.status_code == 201, revision_response.text
    revision = revision_response.json()
    assert revision["status"] == "DRAFT"
    for status in ("IN_REVIEW", "RELEASED"):
        transitioned = auth_client.post(
            f"/api/products/revisions/{revision['id']}/status",
            headers=headers,
            json={"status": status},
        )
        assert transitioned.status_code == 200, transitioned.text
    immutable = auth_client.put(
        f"/api/products/revisions/{revision['id']}",
        headers=headers,
        json={
            "revision_code": "R1",
            "technical_characteristics": {},
            "standard_cost": None,
            "currency": "UAH",
            "revision_instructions": "Changed",
        },
    )
    assert immutable.status_code == 409
    refreshed = auth_client.get(f"/api/products/{product['id']}").json()
    assert refreshed["current_revision_id"] == revision["id"]
    assert refreshed["lifecycle"] == "PRODUCTION"
    cloned = auth_client.post(
        f"/api/products/revisions/{revision['id']}/clone",
        headers=headers,
        json={"revision_code": "R2"},
    )
    assert cloned.status_code == 201, cloned.text
    assert cloned.json()["status"] == "DRAFT"
