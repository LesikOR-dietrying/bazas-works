import pytest
from conftest import sign_in
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.users.models import User

pytestmark = pytest.mark.integration


def test_create_and_update_user(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    headers = sign_in(auth_client)
    payload = {
        "full_name": "New Engineer",
        "username": "engineer2",
        "email": "engineer2@example.com",
        "password": "safe-test-password-22",
        "roles": ["ENGINEER", "RND_ENGINEER"],
    }
    response = auth_client.post("/api/users", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["roles"] == ["ENGINEER", "RND_ENGINEER"]
    assert "MANAGE_ENGINEERING" in response.json()["capabilities"]
    assert "password" not in response.text
    from uuid import UUID

    record = db.get(User, UUID(response.json()["id"]))
    assert record is not None and record.password_hash != payload["password"]
    assert verify_password(payload["password"], record.password_hash)
    payload["username"] = "ENGINEER2"
    assert auth_client.post("/api/users", headers=headers, json=payload).status_code == 409
    patch = {
        "full_name": "Updated Engineer",
        "username": "engineer-updated",
        "email": None,
        "roles": [],
        "is_active": False,
    }
    assert (
        auth_client.patch(f"/api/users/{record.id}", headers=headers, json=patch).status_code == 200
    )
    result = auth_client.get("/api/users?q=Updated&is_active=false").json()
    assert result["total"] == 1
    assert result["items"][0]["full_name"] == "Updated Engineer"


def test_preserves_last_admin(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client)
    admin = accounts["ADMIN"]
    response = auth_client.patch(
        f"/api/users/{admin.id}",
        headers=headers,
        json={
            "full_name": admin.full_name,
            "username": admin.username,
            "email": admin.email,
            "roles": [],
            "is_active": True,
        },
    )
    assert response.status_code == 409


def test_password_reset_revokes_session(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client)
    assert (
        auth_client.post(
            f"/api/users/{accounts['ADMIN'].id}/password",
            headers=headers,
            json={"password": "replacement-password-123"},
        ).status_code
        == 204
    )
    assert auth_client.get("/api/auth/me").status_code == 401


def test_employee_cannot_create_users(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client, "EMPLOYEE")
    assert (
        auth_client.post(
            "/api/users",
            headers=headers,
            json={
                "full_name": "Forbidden",
                "username": "forbidden",
                "password": "test-only-long-password",
            },
        ).status_code
        == 403
    )


def test_professional_role_does_not_bypass_backend_policy(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    headers = sign_in(auth_client)
    response = auth_client.post(
        "/api/users",
        headers=headers,
        json={
            "full_name": "Assembly Worker",
            "username": "assembler",
            "password": "test-only-long-password",
            "roles": ["ASSEMBLER", "QUALITY_CONTROLLER"],
        },
    )
    assert response.status_code == 201
    auth_client.cookies.clear()
    login = auth_client.post(
        "/api/auth/login",
        json={"username": "ASSEMBLER", "password": "test-only-long-password"},
    )
    assert login.status_code == 200
    assert login.json()["roles"] == ["ASSEMBLER", "QUALITY_CONTROLLER"]
    assert auth_client.get("/api/components").status_code == 403
    assert auth_client.get("/api/users").status_code == 403
