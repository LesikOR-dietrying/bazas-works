from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.orders import service
from app.modules.orders.schemas import (
    CustomerRead,
    CustomerWrite,
    DeviationRead,
    DeviationWrite,
    ItemRead,
    ItemWrite,
    MaterialSummary,
    OrderFilters,
    OrderRead,
    OrderStatusWrite,
    OrderWrite,
    ReleasedRevisionOption,
    RequirementRead,
    VariantRead,
    VariantWrite,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/revision-options", response_model=list[ReleasedRevisionOption])
def revision_options(session: Database, user: CurrentUser) -> object:
    return service.released_revisions(session, user)


@router.get("/customers", response_model=list[CustomerRead])
def customers(session: Database, user: CurrentUser) -> object:
    return service.customers(session, user)


@router.post("/customers", response_model=CustomerRead, status_code=201)
def customer(data: CustomerWrite, session: Database, user: CurrentUser) -> object:
    return service.create_customer(session, user, data)


@router.get("", response_model=Page[OrderRead])
def orders(
    session: Database, user: CurrentUser, filters: Annotated[OrderFilters, Query()]
) -> object:
    return service.list_orders(session, user, filters)


@router.post("", response_model=OrderRead, status_code=201)
def create(data: OrderWrite, session: Database, user: CurrentUser) -> object:
    return service.create_order(session, user, data)


@router.get("/{order_id}", response_model=OrderRead)
def read(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_order(session, order_id, user)


@router.post("/{order_id}/status", response_model=OrderRead)
def status(order_id: UUID, data: OrderStatusWrite, session: Database, user: CurrentUser) -> object:
    return service.transition_order(session, order_id, user, data.status)


@router.get("/{order_id}/items", response_model=list[ItemRead])
def items(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.items(session, order_id, user)


@router.post("/{order_id}/items", response_model=ItemRead, status_code=201)
def item(order_id: UUID, data: ItemWrite, session: Database, user: CurrentUser) -> object:
    return service.add_item(session, order_id, user, data)


@router.get("/items/{item_id}/variants", response_model=list[VariantRead])
def variants(item_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.variants(session, item_id, user)


@router.post("/items/{item_id}/variants", response_model=VariantRead, status_code=201)
def split(item_id: UUID, data: VariantWrite, session: Database, user: CurrentUser) -> object:
    return service.split_variant(session, item_id, user, data)


@router.post("/variants/{variant_id}/deviations", response_model=DeviationRead, status_code=201)
def deviation(
    variant_id: UUID, data: DeviationWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_deviation(session, variant_id, user, data)


@router.get("/variants/{variant_id}/deviations", response_model=list[DeviationRead])
def deviations(variant_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.deviations(session, variant_id, user)


@router.post("/deviations/{deviation_id}/approve", response_model=DeviationRead)
def approve(deviation_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.approve_deviation(session, deviation_id, user, True)


@router.post("/deviations/{deviation_id}/reject", response_model=DeviationRead)
def reject(deviation_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.approve_deviation(session, deviation_id, user, False)


@router.post("/items/{item_id}/release-variants", response_model=list[VariantRead])
def release(item_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.release_variants(session, item_id, user)


@router.get("/{order_id}/requirements", response_model=list[RequirementRead])
def requirements(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.requirements(session, order_id, user)


@router.get("/{order_id}/materials", response_model=list[MaterialSummary])
def materials(order_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.material_summary(session, order_id, user)
