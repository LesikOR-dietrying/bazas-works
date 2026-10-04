from collections import deque
from threading import Lock
from time import monotonic

from fastapi import Request

from app.core.errors import DomainError


class LoginThrottle:
    """Bounded per-process throttle for the single-instance deployment."""

    def __init__(self) -> None:
        self.attempts: dict[str, deque[float]] = {}
        self.lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        with self.lock:
            for client in list(self.attempts):
                entries = self.attempts[client]
                while entries and entries[0] < now - 60:
                    entries.popleft()
                if not entries:
                    del self.attempts[client]
            if key not in self.attempts and len(self.attempts) >= 1024:
                raise DomainError(429, "Забагато спроб входу. Зачекайте хвилину.")
            entries = self.attempts.setdefault(key, deque())
            if len(entries) >= 10:
                raise DomainError(429, "Забагато спроб входу. Зачекайте хвилину.")
            entries.append(now)


def limit_login(request: Request) -> None:
    request.app.state.login_throttle.check(request.client.host if request.client else "unknown")
