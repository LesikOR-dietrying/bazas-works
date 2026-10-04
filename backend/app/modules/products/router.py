from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.products import service
from app.modules.products.schemas import (
    AlternativeRead,
    AlternativeWrite,
    BomItemRead,
    BomItemWrite,
    CategoryRead,
    CloneRevisionWrite,
    ProductFilters,
    ProductRead,
    ProductWrite,
    PromotionWrite,
    RevisionRead,
    RevisionStatusWrite,
    RevisionWrite,
    VariantRead,
    VariantWrite,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories", response_model=list[CategoryRead])
def categories(session: Database, user: CurrentUser) -> object:
    return service.categories(session, user)


@router.get("", response_model=Page[ProductRead])
def products(
    session: Database, user: CurrentUser, filters: Annotated[ProductFilters, Query()]
) -> object:
    return service.list_products(session, user, filters)


@router.post("", response_model=ProductRead, status_code=201)
def create(data: ProductWrite, session: Database, user: CurrentUser) -> object:
    return service.create_product(session, user, data)


@router.get("/{product_id}", response_model=ProductRead)
def read(product_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_product(session, product_id, user)


@router.put("/{product_id}", response_model=ProductRead)
def update(product_id: UUID, data: ProductWrite, session: Database, user: CurrentUser) -> object:
    return service.update_product(session, product_id, user, data)


@router.get("/{product_id}/revisions", response_model=list[RevisionRead])
def revisions(product_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_revisions(session, product_id, user)


@router.get("/{product_id}/variants", response_model=list[VariantRead])
def variants(product_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_variants(session, product_id, user)


@router.post("/{product_id}/variants", response_model=VariantRead, status_code=201)
def create_variant(
    product_id: UUID, data: VariantWrite, session: Database, user: CurrentUser
) -> object:
    return service.create_variant(session, product_id, user, data)


@router.post("/{product_id}/revisions", response_model=RevisionRead, status_code=201)
def create_revision(
    product_id: UUID,
    data: RevisionWrite,
    session: Database,
    user: CurrentUser,
    variant_id: UUID | None = None,
) -> object:
    return service.create_revision(session, product_id, user, data, variant_id)


@router.post("/{product_id}/promote", response_model=RevisionRead, status_code=201)
def promote(product_id: UUID, data: PromotionWrite, session: Database, user: CurrentUser) -> object:
    return service.promote(
        session, product_id, user, data.promotion_request_id, data.revision_code, data.variant_id
    )


@router.get("/revisions/{revision_id}", response_model=RevisionRead)
def revision(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_revision(session, revision_id, user)


@router.put("/revisions/{revision_id}", response_model=RevisionRead)
def update_revision(
    revision_id: UUID, data: RevisionWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_revision(session, revision_id, user, data)


@router.post("/revisions/{revision_id}/status", response_model=RevisionRead)
def transition(
    revision_id: UUID, data: RevisionStatusWrite, session: Database, user: CurrentUser
) -> object:
    return service.transition_revision(session, revision_id, user, data.status)


@router.post("/revisions/{revision_id}/clone", response_model=RevisionRead, status_code=201)
def clone(
    revision_id: UUID, data: CloneRevisionWrite, session: Database, user: CurrentUser
) -> object:
    return service.clone_revision(session, revision_id, user, data.revision_code)


@router.get("/revisions/{revision_id}/bom", response_model=list[BomItemRead])
def bom(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_bom(session, revision_id, user)


@router.post("/revisions/{revision_id}/bom", response_model=BomItemRead, status_code=201)
def add_bom(revision_id: UUID, data: BomItemWrite, session: Database, user: CurrentUser) -> object:
    return service.add_bom(session, revision_id, user, data)


@router.delete("/revisions/{revision_id}/bom/{item_id}", status_code=204)
def delete_bom(revision_id: UUID, item_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_bom(session, revision_id, item_id, user)


@router.put("/revisions/{revision_id}/bom/{item_id}", response_model=BomItemRead)
def update_bom(
    revision_id: UUID,
    item_id: UUID,
    data: BomItemWrite,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.update_bom(session, revision_id, item_id, user, data)


@router.post("/bom/{item_id}/alternatives", response_model=AlternativeRead, status_code=201)
def alternative(
    item_id: UUID, data: AlternativeWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_alternative(session, item_id, user, data)
