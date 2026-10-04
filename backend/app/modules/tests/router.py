from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.tests import service
from app.modules.tests.schemas import (
    TestComponentRead,
    TestComponentWrite,
    TestFilters,
    TestMeasurementRead,
    TestMeasurementWrite,
    TestRead,
    TestWrite,
)

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("", response_model=Page[TestRead])
def list_tests(
    session: Database, user: CurrentUser, filters: Annotated[TestFilters, Query()]
) -> object:
    return service.list_tests(session, user, filters)


@router.post("", response_model=TestRead, status_code=201)
def create_test(data: TestWrite, session: Database, user: CurrentUser) -> object:
    return service.create_test(session, user, data)


@router.get("/{test_id}", response_model=TestRead)
def read_test(test_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_test(session, test_id, user)


@router.put("/{test_id}", response_model=TestRead)
def update_test(test_id: UUID, data: TestWrite, session: Database, user: CurrentUser) -> object:
    return service.update_test(session, test_id, user, data)


@router.delete("/{test_id}", status_code=204)
def delete_test(test_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_test(session, test_id, user)


@router.get("/{test_id}/components", response_model=list[TestComponentRead])
def list_equipment(test_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_equipment(session, test_id, user)


@router.post("/{test_id}/components", response_model=TestComponentRead, status_code=201)
def add_equipment(
    test_id: UUID, data: TestComponentWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_equipment(session, test_id, user, data)


@router.delete("/{test_id}/components/{item_id}", status_code=204)
def delete_equipment(test_id: UUID, item_id: UUID, session: Database, user: CurrentUser) -> None:
    service.delete_equipment(session, test_id, item_id, user)


@router.get("/{test_id}/measurements", response_model=list[TestMeasurementRead])
def list_measurements(test_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_measurements(session, test_id, user)


@router.post("/{test_id}/measurements", response_model=TestMeasurementRead, status_code=201)
def add_measurement(
    test_id: UUID, data: TestMeasurementWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_measurement(session, test_id, user, data)


@router.put("/{test_id}/measurements/{measurement_id}", response_model=TestMeasurementRead)
def update_measurement(
    test_id: UUID,
    measurement_id: UUID,
    data: TestMeasurementWrite,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.update_measurement(session, test_id, measurement_id, user, data)


@router.delete("/{test_id}/measurements/{measurement_id}", status_code=204)
def delete_measurement(
    test_id: UUID, measurement_id: UUID, session: Database, user: CurrentUser
) -> None:
    service.delete_measurement(session, test_id, measurement_id, user)
