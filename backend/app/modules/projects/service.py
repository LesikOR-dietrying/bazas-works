from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.projects.access import get_project, require_project_manager, visible_projects
from app.modules.projects.models import Project, ProjectMember
from app.modules.projects.schemas import ProjectFilters, ProjectWrite
from app.modules.users.models import User


def project_options(session: Session, user: User) -> list[Project]:
    return list(session.scalars(visible_projects(user).order_by(Project.name, Project.id)).all())


def list_projects(session: Session, user: User, filters: ProjectFilters) -> Page[Project]:
    statement = visible_projects(user)
    if filters.q:
        statement = statement.where(Project.name.ilike(search_pattern(filters.q)))
    if filters.status:
        statement = statement.where(Project.status == filters.status)
    if filters.responsible_user_id:
        statement = statement.where(Project.responsible_user_id == filters.responsible_user_id)
    column = getattr(Project, filters.sort)
    order = column.asc() if filters.direction == "asc" else column.desc()
    return paginate(session, statement.order_by(order, Project.id), filters)


def validate_members(
    session: Session, data: ProjectWrite, existing: set[UUID] | None = None
) -> set[UUID]:
    members = set(data.participant_ids) | {data.responsible_user_id}
    users = session.scalars(select(User).where(User.id.in_(members))).all()
    if len(users) != len(members):
        raise DomainError(422, "Одного з учасників не знайдено.")
    if any(not user.is_active and user.id not in (existing or set()) for user in users):
        raise DomainError(422, "Нові учасники повинні мати активний обліковий запис.")
    return members


def create_project(session: Session, user: User, data: ProjectWrite) -> Project:
    require_project_manager(user)
    members = validate_members(session, data)
    project = Project(**data.model_dump(exclude={"participant_ids"}))
    project.memberships = [ProjectMember(user_id=member_id) for member_id in members]
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def update_project(session: Session, project_id: UUID, user: User, data: ProjectWrite) -> Project:
    from app.modules.tasks.models import Task

    require_project_manager(user)
    project = get_project(session, project_id, user, lock=True)
    existing = {member.user_id for member in project.memberships}
    members = validate_members(session, data, existing)
    removed = existing - members
    if removed and session.scalar(
        select(Task.id).where(Task.project_id == project.id, Task.assignee_id.in_(removed)).limit(1)
    ):
        raise DomainError(409, "Спочатку перепризначте задачі учасників, яких видаляєте.")
    for name, value in data.model_dump(exclude={"participant_ids"}).items():
        setattr(project, name, value)
    project.memberships[:] = [member for member in project.memberships if member.user_id in members]
    project.memberships.extend(ProjectMember(user_id=member_id) for member_id in members - existing)
    session.commit()
    session.refresh(project)
    return project


def delete_project(session: Session, project_id: UUID, user: User) -> None:
    require_project_manager(user)
    project = get_project(session, project_id, user, lock=True)
    try:
        session.delete(project)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(
            409, "Проєкт має пов’язані записи. Спочатку приберіть їх або заморозьте проєкт."
        ) from None
