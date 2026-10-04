import os
import secrets
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import create_database_engine, get_session
from app.core.security import hash_password
from app.main import create_app
from app.modules.users.models import Role, RoleCode, RoleDefinition, User, UserRole

TEST_SECRET = secrets.token_urlsafe(48)
TEST_PASSWORD = "test-only-password-123"


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        app_env="test",
        jwt_secret=SecretStr(TEST_SECRET),
        database_url=SecretStr("postgresql+psycopg://test:test@127.0.0.1:1/test"),
        cors_origins=["http://localhost:5173"],
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Use scripts/test_backend.py for isolated PostgreSQL tests")
    settings = Settings(
        _env_file=None,
        database_url=SecretStr(url),
        jwt_secret=SecretStr(TEST_SECRET),
        app_env="test",
    )
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    try:
        command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    finally:
        if old_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old_url
        get_settings.cache_clear()
    engine = create_database_engine(settings)
    yield engine
    engine.dispose()


@pytest.fixture
def db(pg_engine: Engine) -> Iterator[Session]:
    with pg_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


@pytest.fixture
def accounts(db: Session) -> dict[str, User]:
    result = {}
    password_hash = hash_password(TEST_PASSWORD)
    for role in Role:
        user = User(
            username=role.lower(),
            full_name=f"Test {role}",
            email=f"{role.lower()}@example.com",
            role=role,
            password_hash=password_hash,
            is_active=True,
        )
        db.add(user)
        db.flush()
        codes = {
            Role.ADMIN: (RoleCode.ADMINISTRATOR,),
            Role.MANAGER: (RoleCode.PRODUCTION_MANAGER,),
            Role.ENGINEER: (RoleCode.ENGINEER, RoleCode.RND_ENGINEER),
            Role.EMPLOYEE: (),
        }[role]
        definitions = db.scalars(select(RoleDefinition).where(RoleDefinition.code.in_(codes))).all()
        user.role_assignments = [UserRole(role=item) for item in definitions]
        result[role] = user
    db.commit()
    return result


@pytest.fixture
def auth_client(db: Session) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        database_url=SecretStr(os.environ["TEST_DATABASE_URL"]),
        jwt_secret=SecretStr(TEST_SECRET),
        app_env="test",
        trusted_origins=["http://testserver"],
    )
    app = create_app(settings)
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app, headers={"Origin": "http://testserver"}) as test_client:
        yield test_client


def sign_in(client: TestClient, role: str = "ADMIN") -> dict[str, str]:
    response = client.post(
        "/api/auth/login", json={"username": role.lower(), "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": client.cookies["baza_csrf"]}
