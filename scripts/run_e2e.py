"""Run browser checks against disposable data, without touching application tables."""

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.database import create_database_engine
from app.modules.users.schemas import UserCreate
from app.modules.users.service import bootstrap_admin
from psycopg import sql
from pydantic import SecretStr
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    url = get_settings().sqlalchemy_url()
    database_name = "baza_e2e_" + uuid4().hex
    node = shutil.which("node") or str(ROOT / ".tools/node/package/bin/node.exe")
    connection = psycopg.connect(
        host=url.host,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        dbname="postgres",
        autocommit=True,
        connect_timeout=5,
    )
    backend: subprocess.Popen[bytes] | None = None
    frontend: subprocess.Popen[bytes] | None = None
    frontend_log = None
    (ROOT / ".tools").mkdir(exist_ok=True)
    storage = tempfile.TemporaryDirectory(
        prefix="baza-e2e-storage-", dir=ROOT / ".tools"
    )
    try:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )
        os.environ.update(
            {
                "DATABASE_URL": url.set(database=database_name).render_as_string(
                    hide_password=False
                ),
                "JWT_SECRET": secrets.token_urlsafe(48),
                "APP_ENV": "test",
                "TRUSTED_ORIGINS": json.dumps(["http://127.0.0.1:4173"]),
                "E2E_USERNAME": "e2e-admin",
                "E2E_PASSWORD": secrets.token_urlsafe(24),
                "STORAGE_DIRECTORY": storage.name,
                "PATH": str(Path(node).parent)
                + os.pathsep
                + os.environ.get("PATH", ""),
            }
        )
        get_settings.cache_clear()
        config = Config(str(ROOT / "backend/alembic.ini"))
        command.upgrade(config, "head")
        engine = create_database_engine(get_settings())
        try:
            with Session(engine) as session:
                bootstrap_admin(
                    session,
                    UserCreate(
                        full_name="E2E Admin",
                        username=os.environ["E2E_USERNAME"],
                        email="e2e@example.com",
                        password=SecretStr(os.environ["E2E_PASSWORD"]),
                    ),
                )
        finally:
            engine.dispose()
        with (ROOT / ".tools/e2e-backend.log").open("wb") as log:
            backend = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8011",
                ],
                cwd=ROOT / "backend",
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            for _ in range(60):
                if backend.poll() is not None:
                    raise RuntimeError(
                        "E2E backend failed; inspect .tools/e2e-backend.log"
                    )
                try:
                    if httpx.get(
                        "http://127.0.0.1:8011/api/health/ready", timeout=1
                    ).is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError("E2E backend readiness timeout")
            frontend_log = (ROOT / ".tools/e2e-frontend.log").open("wb")
            frontend = subprocess.Popen(
                [
                    node,
                    "node_modules/vite/bin/vite.js",
                    "preview",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "4173",
                    "--strictPort",
                ],
                cwd=ROOT / "frontend",
                stdout=frontend_log,
                stderr=subprocess.STDOUT,
                env={
                    **os.environ,
                    "API_PROXY_TARGET": "http://127.0.0.1:8011",
                },
            )
            for _ in range(60):
                if frontend.poll() is not None:
                    raise RuntimeError(
                        "E2E frontend failed; inspect .tools/e2e-frontend.log"
                    )
                try:
                    if httpx.get("http://127.0.0.1:4173", timeout=1).is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError("E2E frontend readiness timeout")
            os.environ["E2E_EXTERNAL_SERVER"] = "1"
            return subprocess.call(
                [node, "node_modules/@playwright/test/cli.js", "test"],
                cwd=ROOT / "frontend",
            )
    finally:
        if frontend is not None:
            frontend.terminate()
            try:
                frontend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                frontend.kill()
                frontend.wait(timeout=5)
        if frontend_log is not None:
            frontend_log.close()
        if backend is not None:
            backend.terminate()
            try:
                backend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend.kill()
                backend.wait(timeout=5)
        connection.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(database_name)
            )
        )
        connection.close()
        storage.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
