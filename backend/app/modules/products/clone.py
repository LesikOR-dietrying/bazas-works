from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.firmware.models import FirmwareRequirement
from app.modules.routes.models import (
    ProductionRoute,
    RouteStage,
    RouteStageDependency,
    RouteStageRole,
)
from app.modules.technology.models import (
    ChecklistTemplateItem,
    TechnologyCard,
    TechnologyContentBlock,
    TechnologyOperation,
)


def clone_revision_definition(session: Session, source_id: UUID, target_id: UUID) -> None:
    _clone_firmware(session, source_id, target_id)
    operation_ids = _clone_card(session, source_id, target_id)
    _clone_routes(session, source_id, target_id, operation_ids)


def _clone_firmware(session: Session, source_id: UUID, target_id: UUID) -> None:
    rows = session.scalars(
        select(FirmwareRequirement).where(FirmwareRequirement.revision_id == source_id)
    ).all()
    for row in rows:
        session.add(
            FirmwareRequirement(
                revision_id=target_id,
                release_id=row.release_id,
                purpose=row.purpose,
                notes=row.notes,
                configuration=row.configuration,
            )
        )


def _clone_card(session: Session, source_id: UUID, target_id: UUID) -> dict[UUID, UUID]:
    source = session.scalar(select(TechnologyCard).where(TechnologyCard.revision_id == source_id))
    operation_ids: dict[UUID, UUID] = {}
    if source is None:
        return operation_ids
    target = TechnologyCard(
        revision_id=target_id, title=source.title, description=source.description
    )
    session.add(target)
    session.flush()
    operations = session.scalars(
        select(TechnologyOperation).where(TechnologyOperation.card_id == source.id)
    ).all()
    for operation in operations:
        copied_operation = TechnologyOperation(
            card_id=target.id,
            name=operation.name,
            sequence=operation.sequence,
            expected_result=operation.expected_result,
            acceptance_criteria=operation.acceptance_criteria,
        )
        session.add(copied_operation)
        session.flush()
        operation_ids[operation.id] = copied_operation.id
        blocks = session.scalars(
            select(TechnologyContentBlock).where(
                TechnologyContentBlock.operation_id == operation.id
            )
        ).all()
        for block in blocks:
            copied_block = TechnologyContentBlock(
                operation_id=copied_operation.id,
                block_type=block.block_type,
                sequence=block.sequence,
                payload=block.payload,
                attachment_id=block.attachment_id,
                annotation_source=block.annotation_source,
                annotation_version=block.annotation_version,
            )
            session.add(copied_block)
            session.flush()
            items = session.scalars(
                select(ChecklistTemplateItem).where(ChecklistTemplateItem.block_id == block.id)
            ).all()
            for item in items:
                session.add(
                    ChecklistTemplateItem(
                        block_id=copied_block.id,
                        text=item.text,
                        sequence=item.sequence,
                        required=item.required,
                        note_required=item.note_required,
                        photo_required=item.photo_required,
                    )
                )
    return operation_ids


def _clone_routes(
    session: Session,
    source_id: UUID,
    target_id: UUID,
    operation_ids: dict[UUID, UUID],
) -> None:
    routes = session.scalars(
        select(ProductionRoute).where(ProductionRoute.revision_id == source_id)
    ).all()
    for route in routes:
        copied_route = ProductionRoute(
            revision_id=target_id,
            version=route.version,
            name=route.name,
            description=route.description,
        )
        session.add(copied_route)
        session.flush()
        stage_ids: dict[UUID, UUID] = {}
        stages = session.scalars(select(RouteStage).where(RouteStage.route_id == route.id)).all()
        for stage in stages:
            copied_stage = RouteStage(
                route_id=copied_route.id,
                code=stage.code,
                name=stage.name,
                sequence=stage.sequence,
                technology_operation_id=operation_ids.get(stage.technology_operation_id),
                supports_pass_fail=stage.supports_pass_fail,
                measurement_required=stage.measurement_required,
                attachment_required=stage.attachment_required,
                instructions=stage.instructions,
            )
            session.add(copied_stage)
            session.flush()
            stage_ids[stage.id] = copied_stage.id
            roles = session.scalars(
                select(RouteStageRole).where(RouteStageRole.stage_id == stage.id)
            ).all()
            for role in roles:
                session.add(RouteStageRole(stage_id=copied_stage.id, role_id=role.role_id))
        dependencies = session.scalars(
            select(RouteStageDependency)
            .join(RouteStage, RouteStage.id == RouteStageDependency.stage_id)
            .where(RouteStage.route_id == route.id)
        ).all()
        for dependency in dependencies:
            session.add(
                RouteStageDependency(
                    stage_id=stage_ids[dependency.stage_id],
                    predecessor_id=stage_ids[dependency.predecessor_id],
                )
            )
