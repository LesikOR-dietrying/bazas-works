"""Run tests against a temporary PostgreSQL database; never touch application tables."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import psycopg
from app.core.config import get_settings
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    tools_directory = ROOT / ".tools"
    tools_directory.mkdir(exist_ok=True)
    url = get_settings().sqlalchemy_url()
    database_name = "baza_test_" + uuid4().hex
    connection = psycopg.connect(
        host=url.host,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        dbname="postgres",
        autocommit=True,
        connect_timeout=5,
    )
    try:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )
        environment = dict(os.environ)
        environment["TEST_DATABASE_URL"] = url.set(
            database=database_name
        ).render_as_string(hide_password=False)
        with tempfile.TemporaryDirectory(
            prefix="pytest-", dir=tools_directory
        ) as base_temp:
            return subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--basetemp",
                    base_temp,
                    *sys.argv[1:],
                ],
                cwd=ROOT / "backend",
                env=environment,
            )
    finally:
        connection.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(database_name)
            )
        )
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
