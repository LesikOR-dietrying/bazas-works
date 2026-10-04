from uuid import uuid4

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def project(
    client: TestClient, accounts: dict[str, User], headers: dict[str, str], name: str
) -> dict:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={"name": name, "responsible_user_id": str(accounts["MANAGER"].id)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def component(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/components",
        headers=headers,
        json={
            "category": "MOTOR",
            "name": "Motor A",
            "manufacturer": "Lab",
            "model": "M1",
            "specifications": {"kv_rpm_v": 1200, "mass_g": 84},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def setup(client: TestClient, headers: dict[str, str], version: str = "V1") -> dict:
    response = client.post(
        "/api/setups",
        headers=headers,
        json={"name": "Drone 15", "drone_class": "15 inch", "version": version},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_bom_reuse_clone_and_project_links(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client, "MANAGER")
    motor = component(auth_client, headers)
    first = setup(auth_client, headers)
    second = setup(auth_client, headers, "V2")
    item = auth_client.post(
        f"/api/setups/{first['id']}/components",
        headers=headers,
        json={"component_id": motor["id"], "quantity": 4, "position": "arm"},
    )
    assert item.status_code == 201, item.text
    assert item.json()["component"]["id"] == motor["id"]
    assert (
        auth_client.post(
            f"/api/setups/{second['id']}/components",
            headers=headers,
            json={"component_id": motor["id"], "quantity": 6, "position": "arm"},
        ).status_code
        == 201
    )
    assert (
        auth_client.post(
            f"/api/setups/{first['id']}/components",
            headers=headers,
            json={"component_id": motor["id"], "quantity": 1, "position": "arm"},
        ).status_code
        == 409
    )
    assert (
        auth_client.post(
            f"/api/setups/{first['id']}/components",
            headers=headers,
            json={"component_id": motor["id"], "quantity": 0},
        ).status_code
        == 422
    )
    cloned = auth_client.post(
        f"/api/setups/{first['id']}/clone", headers=headers, json={"version": "V3"}
    )
    assert cloned.status_code == 201, cloned.text
    copied = auth_client.get(f"/api/setups/{cloned.json()['id']}/components").json()
    assert len(copied) == 1 and copied[0]["component_id"] == motor["id"]
    assert copied[0]["id"] != item.json()["id"]
    assert auth_client.delete(f"/api/components/{motor['id']}", headers=headers).status_code == 409
    changed = {**motor, "category": "ESC"}
    for field in ("id", "created_at", "updated_at"):
        changed.pop(field)
    assert (
        auth_client.put(f"/api/components/{motor['id']}", headers=headers, json=changed).status_code
        == 409
    )
    assert (
        auth_client.put(
            f"/api/setups/{second['id']}/components/{item.json()['id']}",
            headers=headers,
            json={"component_id": motor["id"], "quantity": 2},
        ).status_code
        == 404
    )
    assert auth_client.get("/api/components?q=Motor&category=MOTOR").json()["total"] == 1
    assert auth_client.get("/api/setups?status=DEVELOPMENT").json()["total"] == 3
    used_in = auth_client.get(f"/api/setups?component_id={motor['id']}&sort=version").json()
    assert used_in["total"] == 3
    assert {item["version"] for item in used_in["items"]} == {"V1", "V2", "V3"}
    assert (
        auth_client.post(
            "/api/setups",
            headers=headers,
            json={
                "name": "Invalid current",
                "drone_class": "15 inch",
                "version": "V1",
                "average_current_a": 20,
                "max_current_a": 10,
            },
        ).status_code
        == 422
    )
    one = project(auth_client, accounts, headers, "One")
    two = project(auth_client, accounts, headers, "Two")
    for current in (one, two):
        response = auth_client.post(
            f"/api/projects/{current['id']}/setups",
            headers=headers,
            json={"setup_id": first["id"]},
        )
        assert response.status_code == 201, response.text
        assert (
            auth_client.get(f"/api/projects/{current['id']}/setups").json()[0]["id"] == first["id"]
        )
    assert (
        auth_client.post(
            f"/api/projects/{one['id']}/setups", headers=headers, json={"setup_id": first["id"]}
        ).status_code
        == 409
    )
    assert auth_client.get(f"/api/setups?project_id={two['id']}").json()["total"] == 1
    sign_in(auth_client, "ENGINEER")
    assert (
        auth_client.post(
            f"/api/projects/{one['id']}/setups",
            headers={"X-CSRF-Token": auth_client.cookies["baza_csrf"]},
            json={"setup_id": second["id"]},
        ).status_code
        == 403
    )


def test_firmware_ownership_append_only_and_role_isolation(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client, "ENGINEER")
    source = setup(auth_client, headers)
    other = setup(auth_client, headers, "V2")
    write = {
        "setup_id": source["id"],
        "version_name": "Rev A",
        "firmware_type": "ArduPilot",
        "firmware_version": "4.5",
        "config_text": "TEST=1",
    }
    response = auth_client.post("/api/firmware", headers=headers, json=write)
    assert response.status_code == 201, response.text
    revision = response.json()
    assert revision["created_by_id"] == str(accounts["ENGINEER"].id)
    assert (
        auth_client.post(
            "/api/firmware",
            headers=headers,
            json={**write, "version_name": "Spoof", "created_by_id": str(accounts["ADMIN"].id)},
        ).status_code
        == 422
    )
    assert auth_client.get(f"/api/firmware?setup_id={source['id']}").json()["total"] == 1
    assert auth_client.get(f"/api/firmware?setup_id={other['id']}").json()["total"] == 0
    assert auth_client.post("/api/firmware", headers=headers, json=write).status_code == 409
    assert (
        auth_client.put(f"/api/firmware/{revision['id']}", headers=headers, json=write).status_code
        == 405
    )
    assert auth_client.delete(f"/api/setups/{source['id']}", headers=headers).status_code == 409
    assert auth_client.get(f"/api/firmware/{uuid4()}").status_code == 404
    sign_in(auth_client, "EMPLOYEE")
    for path in (
        "/api/components",
        "/api/components/options",
        "/api/setups",
        "/api/setups/options",
        "/api/firmware",
        f"/api/firmware/{revision['id']}",
    ):
        assert auth_client.get(path).status_code == 403
    employee_headers = {"X-CSRF-Token": auth_client.cookies["baza_csrf"]}
    assert (
        auth_client.post(
            "/api/components",
            headers=employee_headers,
            json={"category": "OTHER", "name": "Forbidden"},
        ).status_code
        == 403
    )


def test_known_component_specs_are_validated(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client, "ENGINEER")
    base = {"category": "MOTOR", "name": "Spec motor"}
    for specs in (
        {"kv": -1},
        {"max_power_w": "NaN"},
        {"weight_g": True},
        {"recommended_propellers": ["13 inch", 5]},
        {"voltage": ""},
    ):
        assert (
            auth_client.post(
                "/api/components", headers=headers, json={**base, "specifications": specs}
            ).status_code
            == 422
        )
    assert (
        auth_client.post(
            "/api/components",
            headers=headers,
            json={
                **base,
                "specifications": {
                    "kv": 1200,
                    "recommended_propellers": ["13 inch"],
                    "custom": {"test": True},
                },
            },
        ).status_code
        == 201
    )
