from uuid import UUID

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.firmware.schemas import FirmwareRead
from app.modules.rnd import service
from app.modules.rnd.schemas import (
    BranchConfigurationRead,
    BranchConfigurationWrite,
    BranchRead,
    BranchTransition,
    BranchWrite,
    ConfigurationComparison,
    PromotionRequestCreate,
    PromotionRequestRead,
    PromotionRequestReview,
)

project_router = APIRouter(prefix="/projects/{project_id}/branches", tags=["rnd"])
router = APIRouter(prefix="/rnd/branches", tags=["rnd"])
promotion_router = APIRouter(prefix="/rnd/promotion-requests", tags=["rnd"])


@project_router.get("", response_model=list[BranchRead])
def list_branches(project_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_branches(session, project_id, user)


@project_router.post("", response_model=BranchRead, status_code=201)
def create_branch(
    project_id: UUID, data: BranchWrite, session: Database, user: CurrentUser
) -> object:
    return service.create_branch(session, project_id, user, data)


@router.get("/{branch_id}", response_model=BranchRead)
def read_branch(branch_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.get_branch(session, branch_id, user)


@router.put("/{branch_id}", response_model=BranchRead)
def update_branch(
    branch_id: UUID, data: BranchWrite, session: Database, user: CurrentUser
) -> object:
    return service.update_branch(session, branch_id, user, data)


@router.post("/{branch_id}/transition", response_model=BranchRead)
def transition_branch(
    branch_id: UUID, data: BranchTransition, session: Database, user: CurrentUser
) -> object:
    return service.transition_branch(session, branch_id, user, data)


@router.get("/{branch_id}/configurations", response_model=list[BranchConfigurationRead])
def list_configurations(branch_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_configurations(session, branch_id, user)


@router.get("/{branch_id}/firmware", response_model=list[FirmwareRead])
def list_firmware(branch_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_firmware(session, branch_id, user)


@router.post("/{branch_id}/configurations", response_model=BranchConfigurationRead, status_code=201)
def link_configuration(
    branch_id: UUID,
    data: BranchConfigurationWrite,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.link_configuration(session, branch_id, user, data)


@router.delete("/{branch_id}/configurations/{link_id}", status_code=204)
def unlink_configuration(
    branch_id: UUID, link_id: UUID, session: Database, user: CurrentUser
) -> None:
    service.unlink_configuration(session, branch_id, link_id, user)


@router.get("/{branch_id}/comparison", response_model=ConfigurationComparison)
def compare_configurations(
    branch_id: UUID,
    candidate_setup_id: UUID,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.compare_configurations(session, branch_id, candidate_setup_id, user)


@router.get("/{branch_id}/promotion-requests", response_model=list[PromotionRequestRead])
def list_promotion_requests(branch_id: UUID, session: Database, user: CurrentUser) -> object:
    return service.list_promotion_requests(session, branch_id, user)


@router.post(
    "/{branch_id}/promotion-requests", response_model=PromotionRequestRead, status_code=201
)
def request_promotion(
    branch_id: UUID,
    data: PromotionRequestCreate,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.request_promotion(session, branch_id, user, data)


@promotion_router.post("/{request_id}/review", response_model=PromotionRequestRead)
def review_promotion(
    request_id: UUID,
    data: PromotionRequestReview,
    session: Database,
    user: CurrentUser,
) -> object:
    return service.review_promotion(session, request_id, user, data)
