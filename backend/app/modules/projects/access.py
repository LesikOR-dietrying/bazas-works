from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.projects.models import Project, ProjectMember
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability, require_capability


def visible_projects(user: User) -> Select[tuple[Project]]:
    statement = select(Project)
    if not has_capability(user, Capability.VIEW_ALL_PROJECTS):
        statement = statement.where(
            or_(
                Project.responsible_user_id == user.id,
                Project.id.in_(
                    select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
                ),
            )
        )
    return statement


def get_project(session: Session, project_id: UUID, user: User, *, lock: bool = False) -> Project:
    statement = visible_projects(user).where(Project.id == project_id)
    if lock:
        statement = statement.with_for_update(of=Project).execution_options(populate_existing=True)
    project = session.scalar(statement)
    if project is None:
        raise DomainError(404, "Проєкт не знайдено або доступ відсутній.")
    return project


def require_project_manager(user: User) -> None:
    require_capability(user, Capability.MANAGE_PROJECTS, "Недостатньо прав для зміни проєктів.")
