from typing import Annotated

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.search.schemas import SearchFilters, SearchResult
from app.modules.search.service import search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page[SearchResult])
def global_search(
    session: Database, user: CurrentUser, filters: Annotated[SearchFilters, Query()]
) -> object:
    return search(session, user, filters)
