from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient

from app.modules.users.models import User

pytestmark = pytest.mark.integration


def create_project(
    client: TestClient,
    accounts: dict[str, User],
    headers: dict[str, str],
    include_employee: bool = True,
    name: str = "Test project",
) -> dict:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": name,
            "responsible_user_id": str(accounts["MANAGER"].id),
            "participant_ids": [str(accounts["EMPLOYEE"].id)] if include_employee else [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_task(
    client: TestClient,
    headers: dict[str, str],
    project: dict,
    assignee: User | None = None,
    **fields: object,
) -> dict:
    response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "title": "Test task",
            "project_id": project["id"],
            "assignee_id": str(assignee.id) if assignee else None,
            **fields,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_project_crud_and_members(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client, "MANAGER")
    project = create_project(auth_client, accounts, headers)
    assert {p["id"] for p in project["participants"]} == {
        str(accounts["MANAGER"].id),
        str(accounts["EMPLOYEE"].id),
    }
    assert project["responsible_name"] == accounts["MANAGER"].full_name
    response = auth_client.put(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={
            "name": "Renamed project",
            "status": "TESTING",
            "responsible_user_id": str(accounts["MANAGER"].id),
            "participant_ids": [str(accounts["ENGINEER"].id)],
            "description": "Updated",
        },
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["participants"]) == 2
    assert auth_client.get("/api/projects?q=Renamed&status=TESTING").json()["total"] == 1
    assert auth_client.delete(f"/api/projects/{project['id']}", headers=headers).status_code == 204
    assert auth_client.get(f"/api/projects/{project['id']}").status_code == 404


def test_employee_isolation_in_lists_details_and_options(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    public = create_project(auth_client, accounts, headers)
    private = create_project(auth_client, accounts, headers, include_employee=False, name="Private")
    own = create_task(auth_client, headers, public, accounts["EMPLOYEE"])
    other = create_task(auth_client, headers, public, accounts["MANAGER"])
    secret = create_task(auth_client, headers, private, accounts["MANAGER"])
    headers = sign_in(auth_client, "EMPLOYEE")
    assert auth_client.get("/api/projects").json()["total"] == 1
    assert auth_client.get("/api/projects/options").json() == [
        {"id": public["id"], "name": public["name"]}
    ]
    assert auth_client.get(f"/api/projects/{private['id']}").status_code == 404
    tasks = auth_client.get("/api/tasks?mine=false").json()
    assert tasks["total"] == 1 and tasks["items"][0]["id"] == own["id"]
    for task in (other, secret):
        assert auth_client.get(f"/api/tasks/{task['id']}").status_code == 404
        assert (
            auth_client.patch(
                f"/api/tasks/{task['id']}", headers=headers, json={"status": "DONE"}
            ).status_code
            == 404
        )
    assert auth_client.get(f"/api/tasks?project_id={private['id']}").json()["total"] == 0
    assert auth_client.get(f"/api/tasks/summary?project_id={private['id']}").status_code == 404


def test_employee_can_only_edit_own_status_and_result(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    task = create_task(auth_client, headers, project, accounts["EMPLOYEE"])
    headers = sign_in(auth_client, "EMPLOYEE")
    url = f"/api/tasks/{task['id']}"
    response = auth_client.patch(
        url, headers=headers, json={"status": "DONE", "result": "Finished work"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["completed_at"] is not None
    assert response.json()["result"] == "Finished work"
    assert (
        auth_client.patch(
            url, headers=headers, json={"assignee_id": str(accounts["ADMIN"].id)}
        ).status_code
        == 403
    )
    assert auth_client.patch(url, headers=headers, json={"priority": "CRITICAL"}).status_code == 403
    assert auth_client.delete(url, headers=headers).status_code == 403
    assert (
        auth_client.post(
            "/api/tasks", headers=headers, json={"title": "No", "project_id": project["id"]}
        ).status_code
        == 403
    )
    assert (
        auth_client.patch(url, headers=headers, json={"status": "IN_PROGRESS"}).json()[
            "completed_at"
        ]
        is None
    )


def test_assignment_and_removing_member_constraints(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    task = create_task(auth_client, headers, project)
    url = f"/api/tasks/{task['id']}"
    assert (
        auth_client.patch(
            url, headers=headers, json={"assignee_id": str(accounts["ENGINEER"].id)}
        ).status_code
        == 422
    )
    response = auth_client.patch(
        url, headers=headers, json={"assignee_id": str(accounts["EMPLOYEE"].id)}
    )
    assert response.status_code == 200
    assert response.json()["assignee_name"] == accounts["EMPLOYEE"].full_name
    patch = {
        "name": project["name"],
        "responsible_user_id": str(accounts["MANAGER"].id),
        "participant_ids": [],
    }
    assert (
        auth_client.put(f"/api/projects/{project['id']}", headers=headers, json=patch).status_code
        == 409
    )
    assert auth_client.patch(url, headers=headers, json={"assignee_id": None}).status_code == 200
    assert (
        auth_client.put(f"/api/projects/{project['id']}", headers=headers, json=patch).status_code
        == 200
    )


def test_engineer_tasks_but_no_project_writes(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    headers = sign_in(auth_client, "ENGINEER")
    assert auth_client.get(f"/api/projects/{project['id']}").status_code == 200
    assert (
        auth_client.post(
            "/api/projects",
            headers=headers,
            json={"name": "No", "responsible_user_id": str(accounts["ENGINEER"].id)},
        ).status_code
        == 403
    )
    task = create_task(auth_client, headers, project)
    assert task["created_by_id"] == str(accounts["ENGINEER"].id)
    assert auth_client.delete(f"/api/tasks/{task['id']}", headers=headers).status_code == 204


def test_task_filters_summary_pagination_and_sort(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    past = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    blocked = create_task(
        auth_client,
        headers,
        project,
        accounts["EMPLOYEE"],
        title="Blocked wiring",
        status="BLOCKED",
        priority="CRITICAL",
        deadline=past,
    )
    create_task(
        auth_client,
        headers,
        project,
        accounts["EMPLOYEE"],
        title="Done check",
        status="DONE",
        deadline=past,
    )
    create_task(auth_client, headers, project, accounts["MANAGER"], title="Normal task")
    result = auth_client.get(
        f"/api/tasks?project_id={project['id']}&status=BLOCKED&priority=CRITICAL&overdue=true&q=wiring"
    ).json()
    assert result["total"] == 1 and result["items"][0]["id"] == blocked["id"]
    assert (
        auth_client.get("/api/tasks?sort=priority&direction=desc&page_size=1").json()["items"][0][
            "id"
        ]
        == blocked["id"]
    )
    assert auth_client.get("/api/tasks?page=2&page_size=2").json()["total"] == 3
    assert len(auth_client.get("/api/tasks?page=2&page_size=2").json()["items"]) == 1
    sign_in(auth_client, "EMPLOYEE")
    summary = auth_client.get("/api/tasks/summary").json()
    assert summary == {
        "total": 2,
        "active": 1,
        "overdue": 1,
        "blocked": 1,
        "completed": 1,
        "completed_recently": 1,
    }


def test_project_deletion_preserves_task_references(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    task = create_task(auth_client, headers, project)
    assert auth_client.delete(f"/api/projects/{project['id']}", headers=headers).status_code == 409
    assert auth_client.get(f"/api/tasks/{task['id']}").status_code == 200
    assert auth_client.delete(f"/api/tasks/{task['id']}", headers=headers).status_code == 204
    assert auth_client.delete(f"/api/projects/{project['id']}", headers=headers).status_code == 204


def test_invalid_updates_and_cross_project_assignment(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    project = create_project(auth_client, accounts, headers)
    private = create_project(auth_client, accounts, headers, include_employee=False)
    task = create_task(auth_client, headers, project, accounts["EMPLOYEE"])
    url = f"/api/tasks/{task['id']}"
    for patch in [
        {"title": None},
        {"status": "UNKNOWN"},
        {},
        {"deadline": "2026-10-01T12:00:00"},
        {"created_by_id": str(uuid4())},
        {"assignee_id": str(uuid4())},
    ]:
        assert auth_client.patch(url, headers=headers, json=patch).status_code == 422
    assert (
        auth_client.patch(url, headers=headers, json={"project_id": private["id"]}).status_code
        == 422
    )
    assert auth_client.get("/api/tasks?sort=password_hash").status_code == 422
    assert auth_client.get("/api/projects?page_size=1000").status_code == 422
