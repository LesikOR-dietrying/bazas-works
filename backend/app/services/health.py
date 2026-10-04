import logging

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseNotReady(Exception):
    """Database connection or schema revision is not ready."""


def migration_heads() -> set[str]:
    config = Config()
    config.set_main_option("script_location", "app:migrations")
    return set(ScriptDirectory.from_config(config).get_heads())


def verify_database(engine: Engine) -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            actual = set(MigrationContext.configure(connection).get_current_heads())
            if actual != migration_heads():
                raise DatabaseNotReady("Database migrations are not current")
    except SQLAlchemyError:
        # Do not expose connection strings, credentials or raw driver errors.
        logger.warning("Database readiness check failed")
        raise DatabaseNotReady("Database unavailable") from None
