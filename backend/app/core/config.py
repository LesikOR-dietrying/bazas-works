from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr | None = None
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "baza"
    postgres_user: str = "baza"
    postgres_password: SecretStr = SecretStr("")
    storage_directory: Path = ROOT / "storage"
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, ge=1, le=1024 * 1024 * 1024)
    cors_origins: list[str] = []
    jwt_secret: SecretStr = SecretStr("")
    seed_password: SecretStr = SecretStr("")
    jwt_issuer: str = "baza"
    jwt_audience: str = "baza-web"
    session_minutes: int = Field(default=60, ge=5, le=1440)
    trusted_origins: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    def signing_key(self) -> str:
        secret = self.jwt_secret.get_secret_value()
        if len(secret) < 32:
            raise ValueError("Set JWT_SECRET to at least 32 random characters")
        return secret

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                driver = make_url(value.get_secret_value()).drivername
            except Exception:
                raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
            if driver != "postgresql+psycopg":
                raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    def sqlalchemy_url(self) -> URL:
        if self.database_url is not None:
            return make_url(self.database_url.get_secret_value())
        if not self.postgres_password.get_secret_value():
            raise ValueError("Set POSTGRES_PASSWORD or DATABASE_URL before starting the backend")
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
