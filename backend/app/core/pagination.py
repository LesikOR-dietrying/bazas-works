from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class ListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    q: str = Field(default="", max_length=200)
    direction: Literal["asc", "desc"] = "asc"


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


def paginate[T](session: Session, statement: Select[tuple[T]], params: ListParams) -> Page[T]:
    total = session.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    items = session.scalars(
        statement.offset((params.page - 1) * params.page_size).limit(params.page_size)
    ).all()
    return Page(items=list(items), total=total or 0, page=params.page, page_size=params.page_size)


def search_pattern(query: str) -> str:
    return "%" + query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
