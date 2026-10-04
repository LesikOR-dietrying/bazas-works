import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from conftest import TEST_SECRET
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.mark.integration
def test_migration_and_readiness_on_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database")
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    settings = Settings(
        _env_file=None,
        database_url=SecretStr(url),
        app_env="test",
        jwt_secret=SecretStr(TEST_SECRET),
    )
    try:
        command.upgrade(config, "head")
        command.check(config)
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/health/ready").status_code == 200
            command.downgrade(config, "base")
            assert client.get("/api/health/ready").status_code == 503
            command.upgrade(config, "head")
            assert client.get("/api/health/ready").status_code == 200
    finally:
        get_settings.cache_clear()
