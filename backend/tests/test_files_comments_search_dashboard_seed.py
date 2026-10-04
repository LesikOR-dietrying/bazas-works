from io import BytesIO
from pathlib import Path
from uuid import UUID

import pytest
from conftest import sign_in
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import DomainError
from app.modules.files.models import Attachment
from app.modules.files.schemas import OwnerReference
from app.modules.files.service import create_file
from app.modules.files.storage import LocalStorage
from app.modules.projects.models import Project
from app.modules.setups.models import Setup
from app.modules.users.models import Role, User
from app.seed import seed_demo

pytestmark = pytest.mark.integration


def create_project_and_task(
    client: TestClient,
    accounts: dict[str, User],
    headers: dict[str, str],
    name: str,
    assignee: str,
) -> tuple[dict, dict]:
    project_response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": name,
            "responsible_user_id": str(accounts["MANAGER"].id),
            "participant_ids": [str(accounts[assignee].id)],
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    task_response = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "title": f"{name} task",
            "project_id": project["id"],
            "assignee_id": str(accounts[assignee].id),
            "status": "BLOCKED",
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project, task_response.json()


def test_authorized_upload_download_comments_and_isolation(
    auth_client: TestClient,
    accounts: dict[str, User],
    tmp_path: Path,
) -> None:
    auth_client.app.state.settings.storage_directory = tmp_path
    auth_client.app.state.settings.max_upload_bytes = 1024
    manager_headers = sign_in(auth_client, "MANAGER")
    project, task = create_project_and_task(
        auth_client, accounts, manager_headers, "Visible", "EMPLOYEE"
    )
    _, hidden_task = create_project_and_task(
        auth_client, accounts, manager_headers, "Hidden", "ENGINEER"
    )
    upload = auth_client.post(
        "/api/files",
        headers=manager_headers,
        data={"task_id": task["id"]},
        files={"upload": ("../bench.txt", b"bench result", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    attachment = upload.json()
    assert attachment["original_filename"] == "bench.txt"
    assert "storage_path" not in attachment and "stored_filename" not in attachment
    listing = auth_client.get(f"/api/files?task_id={task['id']}").json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == attachment["id"]
    assert auth_client.get(f"/api/files?task_id={task['id']}&page=2&page_size=1").json() == {
        "items": [],
        "total": 1,
        "page": 2,
        "page_size": 1,
    }
    download = auth_client.get(f"/api/files/{attachment['id']}/download")
    assert download.status_code == 200 and download.content == b"bench result"
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-content-type-options"] == "nosniff"

    hidden_upload = auth_client.post(
        "/api/files",
        headers=manager_headers,
        data={"task_id": hidden_task["id"]},
        files={"upload": ("hidden.txt", b"hidden", "text/plain")},
    )
    assert hidden_upload.status_code == 201
    employee_headers = sign_in(auth_client, "EMPLOYEE")
    assert auth_client.get(f"/api/files/{attachment['id']}/download").status_code == 200
    assert auth_client.get(f"/api/files/{hidden_upload.json()['id']}/download").status_code == 404
    comment = auth_client.post(
        "/api/comments",
        headers=employee_headers,
        json={"task_id": task["id"], "text": "  Перевірено працівником.  "},
    )
    assert comment.status_code == 201, comment.text
    assert comment.json()["author_id"] == str(accounts["EMPLOYEE"].id)
    updated = auth_client.patch(
        f"/api/comments/{comment.json()['id']}",
        headers=employee_headers,
        json={"text": "Результат підтверджено."},
    )
    assert updated.status_code == 200 and updated.json()["text"] == "Результат підтверджено."
    assert auth_client.get(f"/api/comments?task_id={task['id']}").json()["total"] == 1
    assert (
        auth_client.post(
            "/api/comments", headers=employee_headers, json={"task_id": task["id"], "text": "   "}
        ).status_code
        == 422
    )
    assert (
        auth_client.patch(
            f"/api/comments/{comment.json()['id']}", headers=employee_headers, json={"text": "  "}
        ).status_code
        == 422
    )
    assert auth_client.get(f"/api/comments?project_id={project['id']}").status_code == 200

    before = len(list(tmp_path.iterdir()))
    auth_client.app.state.settings.max_upload_bytes = 3
    too_large = auth_client.post(
        "/api/files",
        headers=employee_headers,
        data={"task_id": task["id"]},
        files={"upload": ("large.bin", b"1234", "application/octet-stream")},
    )
    assert too_large.status_code == 413
    assert len(list(tmp_path.iterdir())) == before


def test_storage_containment_database_xor_search_dashboard_and_seed(
    auth_client: TestClient,
    accounts: dict[str, User],
    db: Session,
    tmp_path: Path,
) -> None:
    storage = LocalStorage(tmp_path)
    with pytest.raises(DomainError):
        storage.open("../secret")
    with pytest.raises(DomainError):
        storage.put(BytesIO(b"1234"), 3)

    manager_headers = sign_in(auth_client, "MANAGER")
    project, task = create_project_and_task(
        auth_client, accounts, manager_headers, "Searchable airframe", "EMPLOYEE"
    )
    component = auth_client.post(
        "/api/components",
        headers=manager_headers,
        json={"category": "MOTOR", "name": "Private 6212", "specifications": {"kv": 260}},
    )
    assert component.status_code == 201
    assert auth_client.get("/api/search?q=6212").json()["total"] == 1
    assert auth_client.get("/api/search?q=Searchable").json()["total"] >= 2
    sign_in(auth_client, "EMPLOYEE")
    assert auth_client.get("/api/search?q=6212").json()["total"] == 0
    visible = auth_client.get("/api/search?q=Searchable").json()
    assert {item["type"] for item in visible["items"]} == {"PROJECT", "TASK"}
    dashboard = auth_client.get("/api/dashboard").json()
    assert dashboard["engineering"] is None
    assert any(item["id"] == task["id"] for item in dashboard["blocked_tasks"])

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(
                text(
                    "INSERT INTO attachments "
                    "(id, original_filename, stored_filename, mime_type, size, storage_path, "
                    "uploaded_by_id) VALUES "
                    "(gen_random_uuid(), 'x', 'x', 'text/plain', 1, 'xor-none', :user_id)"
                ),
                {"user_id": accounts["MANAGER"].id},
            )

    test_settings = Settings(
        _env_file=None,
        app_env="test",
        seed_password=SecretStr("development-password"),
    )
    with pytest.raises(DomainError):
        seed_demo(db, test_settings)
    development = Settings(
        _env_file=None,
        app_env="development",
        seed_password=SecretStr("development-password"),
    )
    seed_demo(db, development)
    seed_demo(db, development)
    assert (
        db.scalar(select(func.count()).select_from(Project).where(Project.name == "Drone 15")) == 1
    )
    assert db.scalar(select(func.count()).select_from(Attachment)) == 0


def test_seed_rejects_real_records_with_demo_identity(db: Session) -> None:
    development = Settings(
        _env_file=None,
        app_env="development",
        seed_password=SecretStr("development-password"),
    )
    real_user = User(
        username="conflicting-admin",
        full_name="Real account",
        email="admin@baza.local",
        password_hash="test-only-hash",
        role=Role.ADMIN,
        is_active=True,
    )
    db.add(real_user)
    db.commit()
    with pytest.raises(DomainError) as error:
        seed_demo(db, development)
    assert error.value.status == 409
    assert db.scalar(select(func.count()).select_from(Project)) == 0

    db.delete(real_user)
    db.commit()
    real_setup = Setup(name="Drone 15 Fiber", version="V3", drone_class="Existing")
    db.add(real_setup)
    db.commit()
    with pytest.raises(DomainError) as error:
        seed_demo(db, development)
    assert error.value.status == 409
    assert db.scalar(select(func.count()).select_from(Project)) == 0


def test_upload_removes_blob_when_database_commit_fails(
    auth_client: TestClient,
    accounts: dict[str, User],
    db: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = sign_in(auth_client, "MANAGER")
    project, _ = create_project_and_task(auth_client, accounts, headers, "Cleanup", "ENGINEER")

    def fail_commit() -> None:
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        create_file(
            db,
            accounts["MANAGER"],
            OwnerReference(project_id=UUID(project["id"])),
            "report.bin",
            "application/octet-stream",
            BytesIO(b"payload"),
            LocalStorage(tmp_path),
            1024,
        )
    assert list(tmp_path.iterdir()) == []
