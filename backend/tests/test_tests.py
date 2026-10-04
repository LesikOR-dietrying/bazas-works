from datetime import UTC, datetime
from uuid import uuid4

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def create_component(client: TestClient, headers: dict[str, str], category: str, name: str) -> dict:
    response = client.post(
        "/api/components", headers=headers, json={"category": category, "name": name}
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_setup(client: TestClient, headers: dict[str, str], version: str) -> dict:
    response = client.post(
        "/api/setups",
        headers=headers,
        json={"name": "Test aircraft", "drone_class": "15 inch", "version": version},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_project(client: TestClient, headers: dict[str, str], manager: User) -> dict:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Test program", "responsible_user_id": str(manager.id)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_test(client: TestClient, headers: dict[str, str], **fields: object) -> dict:
    response = client.post(
        "/api/tests",
        headers=headers,
        json={"name": "Bench run", "test_type": "MOTOR_BENCH", **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_motor_bench_equipment_measurements_and_history(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client, "MANAGER")
    motor = create_component(auth_client, headers, "MOTOR", "Motor 13")
    esc = create_component(auth_client, headers, "ESC", "ESC 60")
    setup = create_setup(auth_client, headers, "V1")
    project = create_project(auth_client, headers, accounts["MANAGER"])
    assert (
        auth_client.post(
            f"/api/projects/{project['id']}/setups", headers=headers, json={"setup_id": setup["id"]}
        ).status_code
        == 201
    )
    firmware = auth_client.post(
        "/api/firmware",
        headers=headers,
        json={
            "setup_id": setup["id"],
            "version_name": "Rev A",
            "firmware_type": "ArduPilot",
            "firmware_version": "4.5",
        },
    )
    assert firmware.status_code == 201, firmware.text
    payload = {
        "project_id": project["id"],
        "setup_id": setup["id"],
        "component_id": motor["id"],
        "firmware_revision_id": firmware.json()["id"],
        "performed_by_id": str(accounts["ENGINEER"].id),
        "test_date": datetime.now(UTC).isoformat(),
        "status": "IN_PROGRESS",
        "conditions": {"ambient_c": 22},
    }
    test = create_test(auth_client, headers, **payload)
    test_id = test["id"]
    assert auth_client.get(f"/api/tests?setup_id={setup['id']}").json()["total"] == 1
    assert auth_client.get(f"/api/tests/{test_id}").json()["conditions"] == {"ambient_c": 22}
    equipment = auth_client.post(
        f"/api/tests/{test_id}/components",
        headers=headers,
        json={"component_id": esc["id"], "role": "ESC"},
    )
    assert equipment.status_code == 201, equipment.text
    assert equipment.json()["component"]["name"] == "ESC 60"
    assert len(auth_client.get(f"/api/tests/{test_id}/components").json()) == 1
    assert (
        auth_client.put(
            f"/api/components/{esc['id']}",
            headers=headers,
            json={"category": "BATTERY", "name": esc["name"]},
        ).status_code
        == 409
    )
    assert (
        auth_client.put(
            f"/api/components/{motor['id']}",
            headers=headers,
            json={"category": "OTHER", "name": motor["name"]},
        ).status_code
        == 409
    )
    assert (
        auth_client.post(
            f"/api/tests/{test_id}/components",
            headers=headers,
            json={"component_id": motor["id"], "role": "ESC"},
        ).status_code
        == 422
    )
    measurement = auth_client.post(
        f"/api/tests/{test_id}/measurements",
        headers=headers,
        json={
            "sequence": 0,
            "throttle_percent": 50,
            "voltage_v": 24.1,
            "thrust_kg": 1.2,
            "motor_temperature_c": -2,
        },
    )
    assert measurement.status_code == 201, measurement.text
    assert measurement.json()["current_a"] is None
    revised = auth_client.put(
        f"/api/tests/{test_id}/measurements/{measurement.json()['id']}",
        headers=headers,
        json={"sequence": 0, "throttle_percent": 50, "power_w": 200},
    )
    assert revised.status_code == 200 and revised.json()["power_w"] == "200.0000"
    assert len(auth_client.get(f"/api/tests/{test_id}/measurements").json()) == 1
    assert (
        auth_client.post(
            f"/api/tests/{test_id}/measurements", headers=headers, json={"sequence": 0}
        ).status_code
        == 409
    )
    for field, value in (("throttle_percent", 101), ("power_w", -1), ("voltage_v", "NaN")):
        assert (
            auth_client.post(
                f"/api/tests/{test_id}/measurements",
                headers=headers,
                json={"sequence": 1, field: value},
            ).status_code
            == 422
        )
    payload["status"] = "PASS"
    payload["result_summary"] = {"max_thrust_kg": 1.2}
    assert (
        auth_client.put(
            f"/api/tests/{test_id}",
            headers=headers,
            json={"name": "Bench run", "test_type": "MOTOR_BENCH", **payload},
        ).status_code
        == 200
    )
    assert auth_client.delete(f"/api/tests/{test_id}", headers=headers).status_code == 409
    payload["component_id"] = esc["id"]
    assert (
        auth_client.put(
            f"/api/tests/{test_id}",
            headers=headers,
            json={"name": "Bench run", "test_type": "MOTOR_BENCH", **payload},
        ).status_code
        == 409
    )
    assert auth_client.get(f"/api/tests/{test_id}").json()["result_summary"] == {
        "max_thrust_kg": 1.2
    }


def test_cross_links_and_bom_freeze(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    headers = sign_in(auth_client, "MANAGER")
    motor = create_component(auth_client, headers, "MOTOR", "Motor X")
    first = create_setup(auth_client, headers, "V1")
    second = create_setup(auth_client, headers, "V2")
    project = create_project(auth_client, headers, accounts["MANAGER"])
    assert (
        auth_client.post(
            f"/api/projects/{project['id']}/setups", headers=headers, json={"setup_id": first["id"]}
        ).status_code
        == 201
    )
    bom = auth_client.post(
        f"/api/setups/{first['id']}/components",
        headers=headers,
        json={"component_id": motor["id"], "quantity": 4},
    )
    assert bom.status_code == 201, bom.text
    firmware = auth_client.post(
        "/api/firmware",
        headers=headers,
        json={
            "setup_id": second["id"],
            "version_name": "Other",
            "firmware_type": "PX4",
            "firmware_version": "1",
        },
    ).json()
    assert (
        auth_client.post(
            "/api/tests",
            headers=headers,
            json={
                "name": "Wrong project link",
                "test_type": "FLIGHT",
                "project_id": project["id"],
                "setup_id": second["id"],
            },
        ).status_code
        == 422
    )
    assert (
        auth_client.post(
            "/api/tests",
            headers=headers,
            json={
                "name": "Wrong firmware",
                "test_type": "FLIGHT",
                "setup_id": first["id"],
                "firmware_revision_id": firmware["id"],
            },
        ).status_code
        == 422
    )
    flight = create_test(
        auth_client,
        headers,
        name="Flight run",
        test_type="FLIGHT",
        project_id=project["id"],
        setup_id=first["id"],
    )
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("UPDATE tests SET setup_id = :setup_id WHERE id = :id"),
            {"setup_id": second["id"], "id": flight["id"]},
        )
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text("UPDATE tests SET firmware_revision_id = :revision_id WHERE id = :id"),
            {"revision_id": firmware["id"], "id": flight["id"]},
        )
        db.flush()
    for method, path, body in (
        (
            "post",
            f"/api/setups/{first['id']}/components",
            {"component_id": motor["id"], "quantity": 1, "position": "extra"},
        ),
        (
            "put",
            f"/api/setups/{first['id']}/components/{bom.json()['id']}",
            {"component_id": motor["id"], "quantity": 5},
        ),
        ("delete", f"/api/setups/{first['id']}/components/{bom.json()['id']}", None),
    ):
        response = (
            auth_client.delete(path, headers=headers)
            if body is None
            else getattr(auth_client, method)(path, headers=headers, json=body)
        )
        assert response.status_code == 409
    assert (
        auth_client.put(
            f"/api/setups/{first['id']}",
            headers=headers,
            json={
                "name": first["name"],
                "drone_class": first["drone_class"],
                "version": first["version"],
                "weight_kg": 5,
            },
        ).status_code
        == 409
    )
    assert (
        auth_client.put(
            f"/api/setups/{first['id']}",
            headers=headers,
            json={
                "name": first["name"],
                "drone_class": first["drone_class"],
                "version": first["version"],
                "status": "TESTING",
                "notes": "In field",
            },
        ).status_code
        == 200
    )
    assert (
        auth_client.delete(
            f"/api/projects/{project['id']}/setups/{first['id']}", headers=headers
        ).status_code
        == 409
    )
    assert auth_client.delete(f"/api/tests/{flight['id']}", headers=headers).status_code == 204
    assert (
        auth_client.delete(
            f"/api/projects/{project['id']}/setups/{first['id']}", headers=headers
        ).status_code
        == 204
    )


def test_role_validation_and_database_constraints(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    headers = sign_in(auth_client, "ENGINEER")
    esc = create_component(auth_client, headers, "ESC", "ESC only")
    setup = create_setup(auth_client, headers, "V1")
    assert (
        auth_client.post(
            "/api/tests",
            headers=headers,
            json={"name": "Wrong motor", "test_type": "MOTOR_BENCH", "component_id": esc["id"]},
        ).status_code
        == 422
    )
    assert (
        auth_client.post(
            "/api/tests",
            headers=headers,
            json={
                "name": "No operator",
                "test_type": "FLIGHT",
                "setup_id": setup["id"],
                "status": "PASS",
            },
        ).status_code
        == 422
    )
    test = create_test(
        auth_client, headers, name="Flight", test_type="FLIGHT", setup_id=setup["id"]
    )
    assert auth_client.get(f"/api/tests/{test['id']}").status_code == 200
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(
            text(
                "INSERT INTO test_measurements (id,test_id,sequence,power_w) "
                "VALUES (:id,:test_id,:sequence,'NaN'::numeric)"
            ),
            {"id": uuid4(), "test_id": test["id"], "sequence": 4},
        )
        db.flush()
    sign_in(auth_client, "EMPLOYEE")
    for path in (
        "/api/tests",
        f"/api/tests/{test['id']}",
        f"/api/tests/{test['id']}/measurements",
        f"/api/tests/{test['id']}/components",
    ):
        assert auth_client.get(path).status_code == 403
    assert (
        auth_client.post(
            "/api/tests",
            headers={"X-CSRF-Token": auth_client.cookies["baza_csrf"]},
            json={"name": "Blocked", "test_type": "FLIGHT", "setup_id": setup["id"]},
        ).status_code
        == 403
    )
