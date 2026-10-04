from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from app.core.errors import DomainError


@dataclass(frozen=True)
class StoredObject:
    key: str
    size: int


class Storage(Protocol):
    def put(self, stream: BinaryIO, max_bytes: int) -> StoredObject: ...

    def open(self, key: str) -> BinaryIO: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not key or Path(key).name != key or "/" in key or "\\" in key:
            raise DomainError(404, "Файл не знайдено.")
        target = (self.root / key).resolve()
        if target.parent != self.root:
            raise DomainError(404, "Файл не знайдено.")
        return target

    def put(self, stream: BinaryIO, max_bytes: int) -> StoredObject:
        key = uuid4().hex
        target = self._path(key)
        temporary = self._path(f"{key}.upload")
        size = 0
        try:
            with temporary.open("xb") as output:
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise DomainError(413, "Файл перевищує дозволений розмір.")
                    output.write(chunk)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return StoredObject(key=key, size=size)

    def open(self, key: str) -> BinaryIO:
        try:
            return self._path(key).open("rb")
        except FileNotFoundError:
            raise DomainError(404, "Файл не знайдено у сховищі.") from None

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
