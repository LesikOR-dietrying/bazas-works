import pytest
from conftest import sign_in
from fastapi.testclient import TestClient

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def _draft(auth_client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    category = auth_client.get("/api/products/categories").json()[0]
    product = auth_client.post(
        "/api/products",
        headers=headers,
        json={
            "code": "DEFINITION-TEST",
            "name": "Виріб з інструкціями",
            "category_id": category["id"],
            "description": "",
            "lifecycle": "DEVELOPMENT",
            "tracking_mode": "SERIAL",
        },
    ).json()
    variant = auth_client.get(f"/api/products/{product['id']}/variants").json()[0]
    response = auth_client.post(
        f"/api/products/{product['id']}/revisions?variant_id={variant['id']}",
        headers=headers,
        json={
            "revision_code": "V1",
            "technical_characteristics": {},
            "standard_cost": None,
            "currency": "UAH",
            "revision_instructions": "",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_technology_firmware_and_route_definition_api(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    assert accounts
    headers = sign_in(auth_client, "MANAGER")
    revision = _draft(auth_client, headers)

    card = auth_client.post(
        f"/api/technology/revisions/{revision['id']}",
        headers=headers,
        json={"title": "Монтаж", "description": "Робоча інструкція"},
    )
    assert card.status_code == 201, card.text
    operation = auth_client.post(
        f"/api/technology/revisions/{revision['id']}/operations",
        headers=headers,
        json={
            "name": "Розпайка",
            "sequence": 0,
            "expected_result": "Контакт надійний",
            "acceptance_criteria": "КЗ немає",
        },
    ).json()
    updated = auth_client.put(
        f"/api/technology/operations/{operation['id']}",
        headers=headers,
        json={**operation, "name": "Розпайка плати"},
    )
    assert updated.status_code == 200, updated.text
    block = auth_client.post(
        f"/api/technology/operations/{operation['id']}/blocks",
        headers=headers,
        json={
            "block_type": "CHECKLIST",
            "sequence": 0,
            "payload": {"text": "Контроль"},
            "attachment_id": None,
            "annotation_source": {},
            "annotation_version": 1,
        },
    ).json()
    item = auth_client.post(
        f"/api/technology/blocks/{block['id']}/checklist",
        headers=headers,
        json={
            "text": "Перевірити полярність",
            "sequence": 0,
            "required": True,
            "note_required": False,
            "photo_required": False,
        },
    ).json()
    changed = auth_client.put(
        f"/api/technology/checklist/{item['id']}",
        headers=headers,
        json={**item, "text": "Перевірити полярність живлення"},
    )
    assert changed.status_code == 200, changed.text
    preview = auth_client.get(f"/api/technology/revisions/{revision['id']}/preview")
    assert preview.json()["operations"][0]["checklist_items"][0]["text"].endswith("живлення")

    artifact = auth_client.post(
        "/api/firmware/artifacts",
        headers=headers,
        json={"name": "Flight controller", "description": "Основна прошивка"},
    ).json()
    release = auth_client.post(
        f"/api/firmware/artifacts/{artifact['id']}/releases",
        headers=headers,
        json={
            "version": "1.2.3",
            "firmware_type": "FC",
            "upstream_version": "1.2",
            "description": "Стабільний реліз",
            "config_text": "mode=prod",
            "checksum": "abc123",
            "binary_attachment_id": None,
            "config_attachment_id": None,
        },
    ).json()
    requirement = auth_client.post(
        f"/api/firmware/requirements/{revision['id']}",
        headers=headers,
        json={
            "release_id": release["id"],
            "purpose": "Контролер",
            "notes": "",
            "configuration": {},
        },
    )
    assert requirement.status_code == 201, requirement.text
    requirements = auth_client.get(f"/api/firmware/requirements/{revision['id']}").json()
    assert requirements[0]["artifact_name"] == "Flight controller"
    assert requirements[0]["release_version"] == "1.2.3"

    route = auth_client.post(
        f"/api/production-routes/revisions/{revision['id']}",
        headers=headers,
        json={"name": "Основний", "version": 1, "description": ""},
    ).json()
    role = auth_client.get("/api/production-routes/roles").json()[0]
    stage = auth_client.post(
        f"/api/production-routes/{route['id']}/stages",
        headers=headers,
        json={
            "code": "SOLDER",
            "name": "Паяння",
            "sequence": 0,
            "technology_operation_id": operation["id"],
            "supports_pass_fail": True,
            "measurement_required": False,
            "attachment_required": False,
            "instructions": "За картою",
            "role_ids": [role["id"]],
        },
    )
    assert stage.status_code == 201, stage.text
    stages = auth_client.get(f"/api/production-routes/{route['id']}/stages").json()
    assert stages[0]["roles"][0]["name"] == role["name"]
    assert stages[0]["predecessor_ids"] == []


def test_technology_definition_is_immutable_after_review(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    assert accounts
    headers = sign_in(auth_client, "MANAGER")
    revision = _draft(auth_client, headers)
    auth_client.post(
        f"/api/technology/revisions/{revision['id']}",
        headers=headers,
        json={"title": "Карта", "description": ""},
    )
    operation = auth_client.post(
        f"/api/technology/revisions/{revision['id']}/operations",
        headers=headers,
        json={"name": "Крок", "sequence": 0, "expected_result": "", "acceptance_criteria": ""},
    ).json()
    transition = auth_client.post(
        f"/api/products/revisions/{revision['id']}/status",
        headers=headers,
        json={"status": "IN_REVIEW"},
    )
    assert transition.status_code == 409
    assert "маршрут" in transition.json()["detail"]
    route = auth_client.post(
        f"/api/production-routes/revisions/{revision['id']}",
        headers=headers,
        json={"name": "Основний", "version": 1, "description": ""},
    ).json()
    role = auth_client.get("/api/production-routes/roles").json()[0]
    stage = auth_client.post(
        f"/api/production-routes/{route['id']}/stages",
        headers=headers,
        json={
            "code": "STEP",
            "name": "Крок",
            "sequence": 0,
            "technology_operation_id": operation["id"],
            "supports_pass_fail": True,
            "measurement_required": False,
            "attachment_required": False,
            "instructions": "",
            "role_ids": [role["id"]],
        },
    )
    assert stage.status_code == 201, stage.text
    transition = auth_client.post(
        f"/api/products/revisions/{revision['id']}/status",
        headers=headers,
        json={"status": "IN_REVIEW"},
    )
    assert transition.status_code == 200
    update = auth_client.put(
        f"/api/technology/operations/{operation['id']}",
        headers=headers,
        json={"name": "Змінений", "sequence": 0, "expected_result": "", "acceptance_criteria": ""},
    )
    assert update.status_code == 409
