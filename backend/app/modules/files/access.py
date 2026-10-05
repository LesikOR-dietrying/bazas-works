from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.components.service import get_component
from app.modules.firmware.service import get_firmware
from app.modules.projects.access import get_project
from app.modules.setups.service import get_setup
from app.modules.tasks.queries import get_task
from app.modules.tests.service import get_test
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability

OWNER_FIELDS = (
    "project_id",
    "task_id",
    "setup_id",
    "component_id",
    "test_id",
    "firmware_revision_id",
    "branch_id",
    "product_id",
    "product_revision_id",
    "firmware_release_id",
    "stage_execution_id",
)


def authorize_owner(session: Session, user: User, owners: dict[str, UUID | None]) -> None:
    selected = [(field, value) for field, value in owners.items() if value is not None]
    if len(selected) != 1:
        raise DomainError(422, "Вкажіть рівно один запис-власник.")
    field, owner_id = selected[0]
    if field == "project_id":
        get_project(session, owner_id, user)
    elif field == "task_id":
        get_task(session, owner_id, user)
    elif field == "setup_id":
        get_setup(session, owner_id, user)
    elif field == "component_id":
        get_component(session, owner_id, user)
    elif field == "test_id":
        get_test(session, owner_id, user)
    elif field == "firmware_revision_id":
        get_firmware(session, owner_id, user)
    elif field == "branch_id":
        from app.modules.rnd.service import get_branch

        get_branch(session, owner_id, user)
    elif field == "product_id":
        from app.modules.products.service import get_product

        get_product(session, owner_id, user)
    elif field == "product_revision_id":
        from app.modules.products.service import get_revision

        if has_capability(user, Capability.VIEW_ENGINEERING):
            get_revision(session, owner_id, user)
        else:
            from app.modules.production.service import can_view_revision_files

            if not can_view_revision_files(session, owner_id, user):
                raise DomainError(404, "Файл не знайдено.")
    elif field == "firmware_release_id":
        from app.modules.firmware.models import FirmwareRelease

        if session.get(FirmwareRelease, owner_id) is None:
            raise DomainError(404, "Реліз прошивки не знайдено.")
        if not has_capability(user, Capability.VIEW_ENGINEERING):
            from app.modules.production.service import can_view_firmware_release_files

            if not can_view_firmware_release_files(session, owner_id, user):
                raise DomainError(404, "Файл не знайдено.")
    elif field == "stage_execution_id":
        from app.modules.production.service import _get_execution

        _get_execution(session, owner_id, user)
    else:
        raise DomainError(422, "Невідомий тип власника.")


def may_manage_owned_record(user: User, creator_id: UUID) -> bool:
    return user.id == creator_id or has_capability(user, Capability.MANAGE_ALL_FILES)
