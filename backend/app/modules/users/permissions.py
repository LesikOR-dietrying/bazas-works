from enum import StrEnum

from app.core.errors import DomainError
from app.modules.users.models import Role, RoleCode, User


class Capability(StrEnum):
    ADMIN_USERS = "ADMIN_USERS"
    VIEW_ALL_PROJECTS = "VIEW_ALL_PROJECTS"
    MANAGE_PROJECTS = "MANAGE_PROJECTS"
    MANAGE_TASKS = "MANAGE_TASKS"
    VIEW_ENGINEERING = "VIEW_ENGINEERING"
    MANAGE_ENGINEERING = "MANAGE_ENGINEERING"
    MANAGE_ALL_FILES = "MANAGE_ALL_FILES"
    VIEW_RND_DASHBOARD = "VIEW_RND_DASHBOARD"
    VIEW_PRODUCTION = "VIEW_PRODUCTION"
    MANAGE_ORDERS = "MANAGE_ORDERS"
    APPROVE_DEVIATIONS = "APPROVE_DEVIATIONS"
    MANAGE_PROCUREMENT = "MANAGE_PROCUREMENT"


ROLE_CAPABILITIES: dict[RoleCode, frozenset[Capability]] = {
    RoleCode.ADMINISTRATOR: frozenset(Capability),
    RoleCode.PRODUCTION_MANAGER: frozenset(
        {
            Capability.VIEW_ALL_PROJECTS,
            Capability.MANAGE_PROJECTS,
            Capability.MANAGE_TASKS,
            Capability.VIEW_ENGINEERING,
            Capability.MANAGE_ENGINEERING,
            Capability.MANAGE_ALL_FILES,
            Capability.VIEW_RND_DASHBOARD,
            Capability.VIEW_PRODUCTION,
            Capability.MANAGE_ORDERS,
            Capability.APPROVE_DEVIATIONS,
            Capability.MANAGE_PROCUREMENT,
        }
    ),
    RoleCode.ENGINEER: frozenset(
        {
            Capability.VIEW_ALL_PROJECTS,
            Capability.MANAGE_TASKS,
            Capability.VIEW_ENGINEERING,
            Capability.MANAGE_ENGINEERING,
            Capability.VIEW_RND_DASHBOARD,
        }
    ),
    RoleCode.RND_ENGINEER: frozenset(
        {
            Capability.VIEW_ALL_PROJECTS,
            Capability.MANAGE_TASKS,
            Capability.VIEW_ENGINEERING,
            Capability.MANAGE_ENGINEERING,
            Capability.VIEW_RND_DASHBOARD,
        }
    ),
    RoleCode.PROCUREMENT_SPECIALIST: frozenset(
        {
            Capability.VIEW_ENGINEERING,
            Capability.VIEW_PRODUCTION,
            Capability.MANAGE_PROCUREMENT,
        }
    ),
    RoleCode.ASSEMBLER: frozenset({Capability.VIEW_PRODUCTION}),
    RoleCode.ELECTRONICS_TECHNICIAN: frozenset({Capability.VIEW_PRODUCTION}),
    RoleCode.FIRMWARE_ENGINEER: frozenset({Capability.VIEW_PRODUCTION}),
    RoleCode.TEST_PILOT: frozenset({Capability.VIEW_PRODUCTION}),
    RoleCode.TEST_ENGINEER: frozenset({Capability.VIEW_PRODUCTION}),
    RoleCode.QUALITY_CONTROLLER: frozenset({Capability.VIEW_PRODUCTION}),
}

LEGACY_ROLE_CODES = {
    Role.ADMIN: frozenset({RoleCode.ADMINISTRATOR}),
    Role.MANAGER: frozenset({RoleCode.PRODUCTION_MANAGER}),
    Role.ENGINEER: frozenset({RoleCode.ENGINEER, RoleCode.RND_ENGINEER}),
    Role.EMPLOYEE: frozenset(),
}


def role_codes_for(user: User) -> frozenset[RoleCode]:
    assigned = frozenset(RoleCode(item.role.code) for item in user.role_assignments)
    return assigned or LEGACY_ROLE_CODES[Role(user.role)]


def capabilities_for(user: User) -> frozenset[Capability]:
    return frozenset(
        capability
        for role_code in role_codes_for(user)
        for capability in ROLE_CAPABILITIES.get(role_code, frozenset())
    )


def has_capability(user: User, capability: Capability) -> bool:
    return capability in capabilities_for(user)


def require_capability(user: User, capability: Capability, message: str) -> None:
    if not has_capability(user, capability):
        raise DomainError(403, message)
