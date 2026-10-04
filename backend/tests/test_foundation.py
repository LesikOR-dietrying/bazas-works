from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.main import create_app
from app.services.health import DatabaseNotReady, migration_heads, verify_database


def test_liveness_without_database(client: TestClient) -> None:
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_rejects_unreachable_database(client: TestClient) -> None:
    response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not ready"}
    assert "psycopg" not in response.text


def test_unimplemented_api_is_not_a_fake_success(client: TestClient) -> None:
    assert client.get("/api/audit-log").status_code == 404


def test_cors_only_allows_configured_origin(client: TestClient) -> None:
    allowed = client.get("/api/health/live", headers={"Origin": "http://localhost:5173"})
    forbidden = client.get("/api/health/live", headers={"Origin": "https://untrusted.invalid"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in forbidden.headers


def test_database_url_preserves_special_password_characters() -> None:
    settings = Settings(_env_file=None, postgres_password=SecretStr("p@ss:/%#word"))
    assert settings.sqlalchemy_url().password == "p@ss:/%#word"
    assert "p@ss" not in repr(settings)


def test_requires_database_credentials() -> None:
    settings = Settings(_env_file=None, database_url=None, postgres_password=SecretStr(""))
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        settings.sqlalchemy_url()


def test_rejects_other_database_drivers() -> None:
    with pytest.raises(ValidationError, match="postgresql"):
        Settings(_env_file=None, database_url=SecretStr("sqlite:///test.db"))


def test_production_hides_openapi() -> None:
    application = create_app(Settings(_env_file=None, app_env="production"))
    assert application.docs_url is None
    assert application.openapi_url is None


def test_migration_graph_has_one_head() -> None:
    assert len(migration_heads()) == 1


def test_readiness_rejects_stale_schema() -> None:
    engine = MagicMock()
    with patch("app.services.health.MigrationContext") as context:
        context.configure.return_value.get_current_heads.return_value = ()
        with pytest.raises(DatabaseNotReady, match="migrations"):
            verify_database(engine)


def test_readiness_accepts_current_schema() -> None:
    engine = MagicMock()
    with patch("app.services.health.MigrationContext") as context:
        context.configure.return_value.get_current_heads.return_value = tuple(migration_heads())
        verify_database(engine)
    engine.connect.return_value.__enter__.return_value.execute.assert_called_once()


def test_driver_error_is_not_exposed() -> None:
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("secret SQL", {}, Exception("secret password"))
    with pytest.raises(DatabaseNotReady, match="^Database unavailable$"):
        verify_database(engine)
