from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import TEST_PASSWORD, TEST_SECRET, sign_in
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import SESSION_COOKIE
from app.modules.users.models import User

pytestmark = pytest.mark.integration


def test_login_cookie_me_logout_and_token_revocation(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    assert auth_client.get("/api/auth/me").status_code == 401
    headers = sign_in(auth_client)
    token = auth_client.cookies[SESSION_COOKIE]
    response = auth_client.get("/api/auth/me")
    assert response.json()["role"] == "ADMIN"
    assert response.json()["username"] == "admin"
    assert response.json()["roles"] == ["ADMINISTRATOR"]
    assert "ADMIN_USERS" in response.json()["capabilities"]
    assert "password" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert auth_client.post("/api/auth/logout", headers=headers).status_code == 204
    auth_client.cookies.set(SESSION_COOKIE, token)
    assert auth_client.get("/api/auth/me").status_code == 401


def test_login_errors_origin_and_cookie_flags(
    auth_client: TestClient, accounts: dict[str, User]
) -> None:
    payload = {"username": "ADMIN", "password": "wrong"}
    assert auth_client.post("/api/auth/login", json=payload).status_code == 401
    assert (
        auth_client.post(
            "/api/auth/login", json=payload, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    payload["password"] = TEST_PASSWORD
    response = auth_client.post("/api/auth/login", json=payload)
    assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
    assert "SameSite=lax" in response.headers.get_list("set-cookie")[0]


@pytest.mark.parametrize("mode", ["expired", "tampered", "audience"])
def test_bad_tokens(auth_client: TestClient, accounts: dict[str, User], mode: str) -> None:
    sign_in(auth_client)
    token = auth_client.cookies[SESSION_COOKIE]
    claims = jwt.decode(
        token, TEST_SECRET, algorithms=["HS256"], audience="baza-web", issuer="baza"
    )
    if mode == "expired":
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
    if mode == "audience":
        claims["aud"] = "other-app"
    token = jwt.encode(claims, TEST_SECRET if mode != "tampered" else "x" * 48, algorithm="HS256")
    auth_client.cookies.clear()
    auth_client.cookies.set(SESSION_COOKIE, token)
    assert auth_client.get("/api/auth/me").status_code == 401


def test_csrf_and_role_access(auth_client: TestClient, accounts: dict[str, User]) -> None:
    headers = sign_in(auth_client, "EMPLOYEE")
    assert auth_client.get("/api/users").status_code == 403
    assert auth_client.post("/api/auth/logout").status_code == 403
    assert (
        auth_client.post("/api/auth/logout", headers={"x-csrf-token": b"\xff"}).status_code == 403
    )
    assert (
        auth_client.post(
            "/api/auth/logout", headers={**headers, "Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    options = auth_client.get("/api/users/options").json()
    assert [item["id"] for item in options] == [str(accounts["EMPLOYEE"].id)]
    assert "email" not in options[0]


def test_disabled_user_is_rejected_immediately(
    auth_client: TestClient, accounts: dict[str, User], db: Session
) -> None:
    sign_in(auth_client, "EMPLOYEE")
    accounts["EMPLOYEE"].is_active = False
    db.commit()
    assert auth_client.get("/api/auth/me").status_code == 401
    assert (
        auth_client.post(
            "/api/auth/login", json={"username": "employee", "password": TEST_PASSWORD}
        ).status_code
        == 401
    )


def test_login_throttle(auth_client: TestClient) -> None:
    for _ in range(10):
        assert (
            auth_client.post(
                "/api/auth/login", json={"username": "missing", "password": "bad"}
            ).status_code
            == 401
        )
    assert (
        auth_client.post(
            "/api/auth/login", json={"username": "missing", "password": "bad"}
        ).status_code
        == 429
    )
