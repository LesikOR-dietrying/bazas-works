from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.errors import DomainError

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash("invalid-login-timing-placeholder")
SESSION_COOKIE = "baza_session"
CSRF_COOKIE = "baza_csrf"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def issue_token(user_id: UUID, session_id: UUID, csrf: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "jti": str(session_id),
            "csrf": csrf,
            "iat": now,
            "exp": now + timedelta(minutes=settings.session_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.signing_key(),
        algorithm="HS256",
    )


def decode_token(token: str, settings: Settings) -> dict[str, object]:
    try:
        claims = jwt.decode(
            token,
            settings.signing_key(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "jti", "csrf", "iat", "exp", "iss", "aud"]},
        )
        UUID(claims["sub"])
        UUID(claims["jti"])
        if not isinstance(claims["csrf"], str) or not claims["csrf"]:
            raise ValueError("Invalid CSRF claim")
        return claims
    except jwt.InvalidTokenError, ValueError, TypeError:
        raise DomainError(401, "Сесія недійсна або завершилась. Увійдіть повторно.") from None
