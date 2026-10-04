import pytest
from conftest import sign_in
from fastapi.testclient import TestClient

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def _create_setup(client: TestClient, headers: dict[str, str], version: str, mass: int) -> dict:
    response = client.post(
        "/api/setups",
        headers=headers,
        json={
            "name": "Універсальна платформа",
            "drone_class": "generic",
            "version": version,
            "attributes": {"mass_g": mass, "product_kind": "ground_station"},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_rnd_branch_comparison_scope_and_promotion(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client, "MANAGER")
    manager_id = str(accounts["MANAGER"].id)
    project_response = auth_client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Наземна станція",
            "goal": "Перевірити нову антену",
            "start_date": "2026-10-01",
            "deadline": "2026-11-01",
            "responsible_user_id": manager_id,
            "participant_ids": [str(accounts["ENGINEER"].id)],
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    assert project["goal"] == "Перевірити нову антену"

    baseline = _create_setup(auth_client, headers, "A", 1000)
    candidate = _create_setup(auth_client, headers, "B", 900)
    for setup in (baseline, candidate):
        linked = auth_client.post(
            f"/api/projects/{project['id']}/setups",
            headers=headers,
            json={"setup_id": setup["id"]},
        )
        assert linked.status_code == 201, linked.text

    main_response = auth_client.post(
        f"/api/projects/{project['id']}/branches",
        headers=headers,
        json={
            "name": "main",
            "responsible_user_id": manager_id,
            "purpose": "Базова лінія дослідження",
        },
    )
    assert main_response.status_code == 201, main_response.text
    main = main_response.json()
    child_response = auth_client.post(
        f"/api/projects/{project['id']}/branches",
        headers=headers,
        json={
            "name": "antenna-b",
            "parent_id": main["id"],
            "responsible_user_id": manager_id,
            "change_summary": "Легша антена",
        },
    )
    assert child_response.status_code == 201, child_response.text
    branch = child_response.json()
    assert branch["parent_name"] == "main"

    for setup, role in ((baseline, "BASELINE"), (candidate, "CANDIDATE")):
        response = auth_client.post(
            f"/api/rnd/branches/{branch['id']}/configurations",
            headers=headers,
            json={"setup_id": setup["id"], "role": role},
        )
        assert response.status_code == 201, response.text

    comparison = auth_client.get(
        f"/api/rnd/branches/{branch['id']}/comparison",
        params={"candidate_setup_id": candidate["id"]},
    )
    assert comparison.status_code == 200, comparison.text
    assert any(change["field"] == "mass_g" for change in comparison.json()["attribute_changes"])

    task = auth_client.post(
        "/api/tasks",
        headers=headers,
        json={"title": "Перевірити антену", "project_id": project["id"], "branch_id": branch["id"]},
    )
    assert task.status_code == 201, task.text
    test = auth_client.post(
        "/api/tests",
        headers=headers,
        json={
            "name": "Перевірка дальності",
            "test_type": "OTHER",
            "project_id": project["id"],
            "branch_id": branch["id"],
        },
    )
    assert test.status_code == 201, test.text
    assert auth_client.get(f"/api/tasks?branch_id={branch['id']}").json()["total"] == 1
    assert auth_client.get(f"/api/tests?branch_id={branch['id']}").json()["total"] == 1

    promotion = auth_client.post(
        f"/api/rnd/branches/{branch['id']}/promotion-requests",
        headers=headers,
        json={"candidate_setup_id": candidate["id"], "reason": "Випробування завершено"},
    )
    assert promotion.status_code == 201, promotion.text
    assert auth_client.get(f"/api/rnd/branches/{branch['id']}").json()["status"] == "IN_REVIEW"
    reviewed = auth_client.post(
        f"/api/rnd/promotion-requests/{promotion.json()['id']}/review",
        headers=headers,
        json={"status": "APPROVED", "review_notes": "Погоджено для Phase 3"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "APPROVED"
    assert auth_client.get(f"/api/rnd/branches/{branch['id']}").json()["status"] == "APPROVED"


def test_branch_must_match_task_project(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client, "MANAGER")
    manager_id = str(accounts["MANAGER"].id)
    projects = []
    for name in ("One", "Two"):
        response = auth_client.post(
            "/api/projects",
            headers=headers,
            json={"name": name, "responsible_user_id": manager_id},
        )
        assert response.status_code == 201, response.text
        projects.append(response.json())
    branch = auth_client.post(
        f"/api/projects/{projects[0]['id']}/branches",
        headers=headers,
        json={"name": "main", "responsible_user_id": manager_id},
    ).json()
    response = auth_client.post(
        "/api/tasks",
        headers=headers,
        json={"title": "Wrong scope", "project_id": projects[1]["id"], "branch_id": branch["id"]},
    )
    assert response.status_code == 422
