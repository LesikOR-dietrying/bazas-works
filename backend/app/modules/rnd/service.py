from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.firmware.models import FirmwareRevision
from app.modules.projects.access import get_project
from app.modules.projects.models import ProjectMember
from app.modules.rnd.models import (
    BranchConfiguration,
    BranchStatus,
    ConfigurationRole,
    PromotionRequestStatus,
    RDBranch,
    RNDPromotionRequest,
)
from app.modules.rnd.schemas import (
    BomChange,
    BranchConfigurationWrite,
    BranchTransition,
    BranchWrite,
    ConfigurationComparison,
    ConfigurationSummary,
    PromotionRequestCreate,
    PromotionRequestReview,
    ValueChange,
)
from app.modules.setups.models import ProjectSetup, SetupComponent
from app.modules.setups.service import get_setup
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def _require_editor(user: User) -> None:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для зміни R&D гілок.")


def get_branch(session: Session, branch_id: UUID, user: User, *, lock: bool = False) -> RDBranch:
    branch = session.get(RDBranch, branch_id)
    if branch is None:
        raise DomainError(404, "R&D гілку не знайдено.")
    get_project(session, branch.project_id, user, lock=lock)
    if lock:
        branch = session.scalar(
            select(RDBranch)
            .where(RDBranch.id == branch_id)
            .with_for_update(of=RDBranch)
            .execution_options(populate_existing=True)
        )
        if branch is None:
            raise DomainError(404, "R&D гілку не знайдено.")
    return branch


def list_branches(session: Session, project_id: UUID, user: User) -> list[RDBranch]:
    get_project(session, project_id, user)
    return list(
        session.scalars(
            select(RDBranch)
            .where(RDBranch.project_id == project_id)
            .order_by(RDBranch.created_at, RDBranch.id)
        ).all()
    )


def _require_mutable(branch: RDBranch) -> None:
    if branch.status not in {BranchStatus.OPEN, BranchStatus.REJECTED}:
        raise DomainError(409, "Перед редагуванням поверніть гілку у стан «Відкрито».")


def _validate_responsible(session: Session, project_id: UUID, user_id: UUID) -> None:
    if (
        session.scalar(
            select(ProjectMember.id).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
        )
        is None
    ):
        raise DomainError(422, "Відповідальний за гілку має бути учасником проєкту.")


def _validate_parent(
    session: Session, project_id: UUID, parent_id: UUID | None, branch_id: UUID | None = None
) -> None:
    current = parent_id
    visited = {branch_id} if branch_id else set()
    while current:
        if current in visited:
            raise DomainError(422, "R&D гілка не може бути власним предком.")
        visited.add(current)
        parent = session.get(RDBranch, current)
        if parent is None or parent.project_id != project_id:
            raise DomainError(422, "Батьківська гілка має належати цьому проєкту.")
        current = parent.parent_id


def _commit(session: Session, record: object, conflict: str) -> object:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, conflict) from None
    session.refresh(record)
    return record


def create_branch(session: Session, project_id: UUID, user: User, data: BranchWrite) -> RDBranch:
    _require_editor(user)
    get_project(session, project_id, user, lock=True)
    _validate_responsible(session, project_id, data.responsible_user_id)
    _validate_parent(session, project_id, data.parent_id)
    branch = RDBranch(
        project_id=project_id,
        created_by_id=user.id,
        status=BranchStatus.OPEN,
        **data.model_dump(),
    )
    session.add(branch)
    return _commit(session, branch, "Гілка з такою назвою вже існує.")  # type: ignore[return-value]


def update_branch(session: Session, branch_id: UUID, user: User, data: BranchWrite) -> RDBranch:
    _require_editor(user)
    branch = get_branch(session, branch_id, user, lock=True)
    _require_mutable(branch)
    _validate_responsible(session, branch.project_id, data.responsible_user_id)
    _validate_parent(session, branch.project_id, data.parent_id, branch.id)
    for field, value in data.model_dump().items():
        setattr(branch, field, value)
    return _commit(session, branch, "Гілка з такою назвою вже існує.")  # type: ignore[return-value]


ALLOWED_TRANSITIONS = {
    BranchStatus.OPEN: {BranchStatus.IN_REVIEW, BranchStatus.CLOSED},
    BranchStatus.IN_REVIEW: {
        BranchStatus.OPEN,
        BranchStatus.APPROVED,
        BranchStatus.REJECTED,
        BranchStatus.CLOSED,
    },
    BranchStatus.REJECTED: {BranchStatus.OPEN, BranchStatus.CLOSED},
    BranchStatus.APPROVED: {BranchStatus.CLOSED},
    BranchStatus.CLOSED: set(),
}


def transition_branch(
    session: Session, branch_id: UUID, user: User, data: BranchTransition
) -> RDBranch:
    _require_editor(user)
    branch = get_branch(session, branch_id, user, lock=True)
    current = BranchStatus(branch.status)
    if data.status not in ALLOWED_TRANSITIONS[current]:
        raise DomainError(409, f"Перехід {current} → {data.status} недоступний.")
    if data.status in {BranchStatus.APPROVED, BranchStatus.REJECTED}:
        require_capability(
            user, Capability.MANAGE_PROJECTS, "Рішення може прийняти керівник проєкту."
        )
    branch.status = data.status
    if data.result_summary is not None:
        branch.result_summary = data.result_summary
    branch.closed_at = datetime.now(UTC) if data.status == BranchStatus.CLOSED else None
    session.commit()
    session.refresh(branch)
    return branch


def list_configurations(session: Session, branch_id: UUID, user: User) -> list[BranchConfiguration]:
    get_branch(session, branch_id, user)
    return list(
        session.scalars(
            select(BranchConfiguration)
            .where(BranchConfiguration.branch_id == branch_id)
            .order_by(BranchConfiguration.role, BranchConfiguration.created_at)
        ).all()
    )


def list_firmware(session: Session, branch_id: UUID, user: User) -> list[FirmwareRevision]:
    get_branch(session, branch_id, user)
    return list(
        session.scalars(
            select(FirmwareRevision)
            .join(
                BranchConfiguration,
                BranchConfiguration.setup_id == FirmwareRevision.setup_id,
            )
            .where(BranchConfiguration.branch_id == branch_id)
            .order_by(FirmwareRevision.created_at.desc(), FirmwareRevision.id)
        ).all()
    )


def link_configuration(
    session: Session, branch_id: UUID, user: User, data: BranchConfigurationWrite
) -> BranchConfiguration:
    _require_editor(user)
    branch = get_branch(session, branch_id, user, lock=True)
    _require_mutable(branch)
    get_setup(session, data.setup_id, user)
    if (
        session.scalar(
            select(ProjectSetup.id).where(
                ProjectSetup.project_id == branch.project_id, ProjectSetup.setup_id == data.setup_id
            )
        )
        is None
    ):
        raise DomainError(422, "Спочатку прив’яжіть конфігурацію до проєкту.")
    link = BranchConfiguration(
        branch_id=branch.id,
        setup_id=data.setup_id,
        role=data.role,
        created_by_id=user.id,
    )
    session.add(link)
    return _commit(session, link, "Конфігурацію вже додано або baseline вже визначено.")  # type: ignore[return-value]


def unlink_configuration(session: Session, branch_id: UUID, link_id: UUID, user: User) -> None:
    _require_editor(user)
    branch = get_branch(session, branch_id, user, lock=True)
    _require_mutable(branch)
    link = session.scalar(
        select(BranchConfiguration).where(
            BranchConfiguration.id == link_id, BranchConfiguration.branch_id == branch_id
        )
    )
    if link is None:
        raise DomainError(404, "Прив’язку конфігурації не знайдено.")
    if session.scalar(
        select(RNDPromotionRequest.id).where(
            RNDPromotionRequest.branch_id == branch_id,
            RNDPromotionRequest.candidate_setup_id == link.setup_id,
        )
    ):
        raise DomainError(409, "Конфігурація вже використана в запиті на передавання.")
    session.delete(link)
    session.commit()


def _configuration_summary(link: BranchConfiguration) -> ConfigurationSummary:
    return ConfigurationSummary(
        id=link.setup.id,
        name=link.setup.name,
        version=link.setup.version,
        status=link.setup.status,
        role=ConfigurationRole(link.role),
    )


def compare_configurations(
    session: Session, branch_id: UUID, candidate_setup_id: UUID, user: User
) -> ConfigurationComparison:
    get_branch(session, branch_id, user)
    links = session.scalars(
        select(BranchConfiguration).where(BranchConfiguration.branch_id == branch_id)
    ).all()
    baseline = next((item for item in links if item.role == ConfigurationRole.BASELINE), None)
    candidate = next((item for item in links if item.setup_id == candidate_setup_id), None)
    if baseline is None or candidate is None or candidate.role != ConfigurationRole.CANDIDATE:
        raise DomainError(422, "Для порівняння потрібні базова конфігурація і вибраний кандидат.")
    legacy_fields = (
        "drone_class",
        "weight_kg",
        "payload_kg",
        "battery_description",
        "battery_voltage",
        "battery_capacity_ah",
        "propeller_description",
        "flight_time_minutes",
        "average_current_a",
        "max_current_a",
        "firmware_type",
        "firmware_version",
    )
    baseline_values = {
        **baseline.setup.attributes,
        **{field: getattr(baseline.setup, field) for field in legacy_fields},
    }
    candidate_values = {
        **candidate.setup.attributes,
        **{field: getattr(candidate.setup, field) for field in legacy_fields},
    }
    attribute_changes = [
        ValueChange(
            field=field, baseline=baseline_values.get(field), candidate=candidate_values.get(field)
        )
        for field in sorted(baseline_values.keys() | candidate_values.keys())
        if baseline_values.get(field) != candidate_values.get(field)
    ]
    rows = session.scalars(
        select(SetupComponent).where(
            SetupComponent.setup_id.in_([baseline.setup_id, candidate.setup_id])
        )
    ).all()
    baseline_bom = {
        (row.component_id, row.position): row for row in rows if row.setup_id == baseline.setup_id
    }
    candidate_bom = {
        (row.component_id, row.position): row for row in rows if row.setup_id == candidate.setup_id
    }
    bom_changes = []
    for key in sorted(
        baseline_bom.keys() | candidate_bom.keys(), key=lambda item: (str(item[0]), item[1])
    ):
        before, after = baseline_bom.get(key), candidate_bom.get(key)
        before_quantity, after_quantity = (
            before.quantity if before else 0,
            after.quantity if after else 0,
        )
        if before_quantity != after_quantity:
            row = before or after
            assert row is not None
            bom_changes.append(
                BomChange(
                    component_id=row.component_id,
                    component_name=row.component.name,
                    position=row.position,
                    baseline_quantity=before_quantity,
                    candidate_quantity=after_quantity,
                )
            )
    return ConfigurationComparison(
        baseline=_configuration_summary(baseline),
        candidate=_configuration_summary(candidate),
        attribute_changes=attribute_changes,
        bom_changes=bom_changes,
    )


def list_promotion_requests(
    session: Session, branch_id: UUID, user: User
) -> list[RNDPromotionRequest]:
    get_branch(session, branch_id, user)
    return list(
        session.scalars(
            select(RNDPromotionRequest)
            .where(RNDPromotionRequest.branch_id == branch_id)
            .order_by(RNDPromotionRequest.created_at.desc(), RNDPromotionRequest.id)
        ).all()
    )


def request_promotion(
    session: Session, branch_id: UUID, user: User, data: PromotionRequestCreate
) -> RNDPromotionRequest:
    _require_editor(user)
    branch = get_branch(session, branch_id, user, lock=True)
    if branch.status != BranchStatus.OPEN:
        raise DomainError(409, "Запит можна створити лише для відкритої гілки.")
    if (
        session.scalar(
            select(BranchConfiguration.id).where(
                BranchConfiguration.branch_id == branch_id,
                BranchConfiguration.setup_id == data.candidate_setup_id,
                BranchConfiguration.role == ConfigurationRole.CANDIDATE,
            )
        )
        is None
    ):
        raise DomainError(422, "Оберіть конфігурацію-кандидата цієї гілки.")
    request = RNDPromotionRequest(
        branch_id=branch_id,
        candidate_setup_id=data.candidate_setup_id,
        reason=data.reason.strip(),
        requested_by_id=user.id,
        status=PromotionRequestStatus.REQUESTED,
    )
    branch.status = BranchStatus.IN_REVIEW
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def review_promotion(
    session: Session, request_id: UUID, user: User, data: PromotionRequestReview
) -> RNDPromotionRequest:
    require_capability(
        user, Capability.MANAGE_PROJECTS, "Розглядати promotion може керівник проєкту."
    )
    if data.status not in {PromotionRequestStatus.APPROVED, PromotionRequestStatus.REJECTED}:
        raise DomainError(422, "Оберіть стан «Погоджено» або «Відхилено».")
    request = session.get(RNDPromotionRequest, request_id)
    if request is None:
        raise DomainError(404, "Запит на передавання не знайдено.")
    branch = get_branch(session, request.branch_id, user, lock=True)
    request = session.scalar(
        select(RNDPromotionRequest)
        .where(RNDPromotionRequest.id == request_id)
        .with_for_update(of=RNDPromotionRequest)
        .execution_options(populate_existing=True)
    )
    if request is None or request.status != PromotionRequestStatus.REQUESTED:
        raise DomainError(409, "Запит уже розглянуто.")
    request.status = data.status
    request.reviewed_by_id = user.id
    request.reviewed_at = datetime.now(UTC)
    request.review_notes = data.review_notes
    branch.status = (
        BranchStatus.APPROVED
        if data.status == PromotionRequestStatus.APPROVED
        else BranchStatus.REJECTED
    )
    session.commit()
    session.refresh(request)
    return request
