from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.service import require_engineer
from app.modules.firmware.models import (
    FirmwareArtifact,
    FirmwareRelease,
    FirmwareRequirement,
    FirmwareRevision,
)
from app.modules.firmware.schemas import (
    ArtifactWrite,
    FirmwareFilters,
    FirmwareWrite,
    ReleaseWrite,
    RequirementRead,
    RequirementWrite,
)
from app.modules.products.service import get_revision, require_draft
from app.modules.setups.service import get_setup
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def list_firmware(session: Session, user: User, filters: FirmwareFilters) -> Page[FirmwareRevision]:
    require_engineer(user)
    statement = select(FirmwareRevision)
    if filters.setup_id:
        get_setup(session, filters.setup_id, user)
        statement = statement.where(FirmwareRevision.setup_id == filters.setup_id)
    if filters.q:
        statement = statement.where(FirmwareRevision.version_name.ilike(search_pattern(filters.q)))
    return paginate(
        session,
        statement.order_by(FirmwareRevision.created_at.desc(), FirmwareRevision.id),
        filters,
    )


def get_firmware(session: Session, revision_id: UUID, user: User) -> FirmwareRevision:
    require_engineer(user)
    revision = session.get(FirmwareRevision, revision_id)
    if revision is None:
        raise DomainError(404, "Ревізію прошивки не знайдено.")
    return revision


def create_firmware(session: Session, user: User, data: FirmwareWrite) -> FirmwareRevision:
    get_setup(session, data.setup_id, user, lock=True)
    revision = FirmwareRevision(**data.model_dump(), created_by_id=user.id)
    session.add(revision)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Назва ревізії вже використана у цій конфігурації.") from None
    session.refresh(revision)
    return revision


def artifacts(session: Session, user: User) -> list[FirmwareArtifact]:
    require_engineer(user)
    return list(session.scalars(select(FirmwareArtifact).order_by(FirmwareArtifact.name)))


def create_artifact(session: Session, user: User, data: ArtifactWrite) -> FirmwareArtifact:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для прошивок.")
    row = FirmwareArtifact(**data.model_dump())
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Артефакт з такою назвою вже існує.") from None
    session.refresh(row)
    return row


def releases(session: Session, artifact_id: UUID, user: User) -> list[FirmwareRelease]:
    require_engineer(user)
    return list(
        session.scalars(
            select(FirmwareRelease)
            .where(FirmwareRelease.artifact_id == artifact_id)
            .order_by(FirmwareRelease.created_at.desc())
        )
    )


def create_release(
    session: Session, artifact_id: UUID, user: User, data: ReleaseWrite
) -> FirmwareRelease:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для прошивок.")
    if session.get(FirmwareArtifact, artifact_id) is None:
        raise DomainError(404, "Артефакт прошивки не знайдено.")
    row = FirmwareRelease(
        artifact_id=artifact_id, created_by_id=user.id, **data.model_dump(mode="json")
    )
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, "Версія релізу вже існує.") from None
    session.refresh(row)
    return row


def requirements(session: Session, revision_id: UUID, user: User) -> list[RequirementRead]:
    get_revision(session, revision_id, user)
    rows = session.execute(
        select(FirmwareRequirement, FirmwareRelease, FirmwareArtifact)
        .join(FirmwareRelease, FirmwareRelease.id == FirmwareRequirement.release_id)
        .join(FirmwareArtifact, FirmwareArtifact.id == FirmwareRelease.artifact_id)
        .where(FirmwareRequirement.revision_id == revision_id)
        .order_by(FirmwareRequirement.created_at)
    ).all()
    return [
        RequirementRead.model_validate(
            {
                **{
                    column.name: getattr(requirement, column.name)
                    for column in FirmwareRequirement.__table__.columns
                },
                "artifact_id": artifact.id,
                "artifact_name": artifact.name,
                "artifact_description": artifact.description,
                "release_version": release.version,
                "firmware_type": release.firmware_type,
                "upstream_version": release.upstream_version,
                "release_description": release.description,
                "config_text": release.config_text,
                "checksum": release.checksum,
                "binary_attachment_id": release.binary_attachment_id,
                "config_attachment_id": release.config_attachment_id,
            }
        )
        for requirement, release, artifact in rows
    ]


def add_requirement(
    session: Session, revision_id: UUID, user: User, data: RequirementWrite
) -> RequirementRead:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для прошивок.")
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    if session.get(FirmwareRelease, data.release_id) is None:
        raise DomainError(422, "Реліз прошивки не знайдено.")
    row = FirmwareRequirement(revision_id=revision_id, **data.model_dump(mode="json"))
    session.add(row)
    session.commit()
    session.refresh(row)
    return next(item for item in requirements(session, revision_id, user) if item.id == row.id)


def delete_requirement(session: Session, requirement_id: UUID, user: User) -> None:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для прошивок.")
    row = session.get(FirmwareRequirement, requirement_id)
    if row is None:
        raise DomainError(404, "Вимогу до прошивки не знайдено.")
    require_draft(get_revision(session, row.revision_id, user, lock=True))
    session.delete(row)
    session.commit()
