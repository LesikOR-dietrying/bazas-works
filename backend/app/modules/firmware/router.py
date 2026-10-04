from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.firmware import service
from app.modules.firmware.schemas import (
    ArtifactRead,
    ArtifactWrite,
    FirmwareFilters,
    FirmwareRead,
    FirmwareWrite,
    ReleaseRead,
    ReleaseWrite,
    RequirementRead,
    RequirementWrite,
)

router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.get("/artifacts", response_model=list[ArtifactRead])
def artifacts(session: Database, user: CurrentUser) -> object:
    return service.artifacts(session, user)


@router.post("/artifacts", response_model=ArtifactRead, status_code=201)
def artifact(data: ArtifactWrite, session: Database, user: CurrentUser) -> object:
    return service.create_artifact(session, user, data)


@router.get("/artifacts/{artifact_id}/releases", response_model=list[ReleaseRead])
def releases(artifact_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.releases(session, artifact_id, user)


@router.post("/artifacts/{artifact_id}/releases", response_model=ReleaseRead, status_code=201)
def release(artifact_id: UUID, data: ReleaseWrite, session: Database, user: CurrentUser) -> object:
    return service.create_release(session, artifact_id, user, data)


@router.get("/requirements/{revision_id}", response_model=list[RequirementRead])
def requirements(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.requirements(session, revision_id, user)


@router.post("/requirements/{revision_id}", response_model=RequirementRead, status_code=201)
def requirement(
    revision_id: UUID, data: RequirementWrite, session: Database, user: CurrentUser
) -> object:
    return service.add_requirement(session, revision_id, user, data)


@router.get("", response_model=Page[FirmwareRead])
def list_firmware(
    session: Database, user: CurrentUser, filters: Annotated[FirmwareFilters, Query()]
) -> object:
    return service.list_firmware(session, user, filters)


@router.post("", response_model=FirmwareRead, status_code=201)
def create_firmware(data: FirmwareWrite, session: Database, user: CurrentUser) -> object:
    return service.create_firmware(session, user, data)


@router.get("/{revision_id}", response_model=FirmwareRead)
def read_firmware(revision_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_firmware(session, revision_id, user)
