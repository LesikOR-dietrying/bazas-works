from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.pagination import ListParams

SearchType = Literal["PROJECT", "TASK", "SETUP", "COMPONENT", "TEST"]


class SearchFilters(ListParams):
    q: str = Field(min_length=1, max_length=200)
    type: SearchType | None = None


class SearchResult(BaseModel):
    type: SearchType
    id: UUID
    title: str
    context: str
    path: str
