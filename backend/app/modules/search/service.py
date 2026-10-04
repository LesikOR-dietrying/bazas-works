from sqlalchemy import Text, cast, func, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.core.pagination import Page, search_pattern
from app.modules.components.models import Component
from app.modules.projects.access import visible_projects
from app.modules.projects.models import Project
from app.modules.search.schemas import SearchFilters, SearchResult
from app.modules.setups.models import Setup, SetupComponent
from app.modules.tasks.models import Task
from app.modules.tasks.queries import visible_tasks
from app.modules.tests.models import Test, TestComponent
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability


def _result_query(entity_type: str, identifier: object, title: object, context: object):
    return select(
        literal(entity_type).label("type"),
        identifier.label("id"),
        title.label("title"),
        context.label("context"),
    )


def search(session: Session, user: User, filters: SearchFilters) -> Page[SearchResult]:
    pattern = search_pattern(filters.q)
    requested = filters.type
    statements = []

    if requested in (None, "PROJECT"):
        projects = visible_projects(user).where(
            or_(Project.name.ilike(pattern), Project.description.ilike(pattern))
        )
        statements.append(
            projects.with_only_columns(
                literal("PROJECT").label("type"),
                Project.id.label("id"),
                Project.name.label("title"),
                literal("Проєкт").label("context"),
            )
        )
    if requested in (None, "TASK"):
        tasks = visible_tasks(user).where(
            or_(
                Task.title.ilike(pattern),
                Task.description.ilike(pattern),
                Task.result.ilike(pattern),
            )
        )
        statements.append(
            tasks.with_only_columns(
                literal("TASK").label("type"),
                Task.id.label("id"),
                Task.title.label("title"),
                literal("Задача").label("context"),
            )
        )

    if has_capability(user, Capability.VIEW_ENGINEERING):
        component_match = or_(
            Component.name.ilike(pattern),
            Component.manufacturer.ilike(pattern),
            Component.model.ilike(pattern),
            cast(Component.specifications, Text).ilike(pattern),
        )
        matching_component_ids = select(Component.id).where(component_match)
        related_setup_ids = select(SetupComponent.setup_id).where(
            SetupComponent.component_id.in_(matching_component_ids)
        )
        if requested in (None, "COMPONENT"):
            statements.append(
                _result_query(
                    "COMPONENT",
                    Component.id,
                    Component.name,
                    func.concat(
                        Component.category, " · ", Component.manufacturer, " ", Component.model
                    ),
                ).where(component_match)
            )
        if requested in (None, "SETUP"):
            statements.append(
                _result_query(
                    "SETUP",
                    Setup.id,
                    func.concat(Setup.name, " · ", Setup.version),
                    func.concat("Сетап · ", Setup.status),
                ).where(
                    or_(
                        Setup.name.ilike(pattern),
                        Setup.version.ilike(pattern),
                        Setup.drone_class.ilike(pattern),
                        Setup.id.in_(related_setup_ids),
                    )
                )
            )
        if requested in (None, "TEST"):
            equipment_test_ids = select(TestComponent.test_id).where(
                TestComponent.component_id.in_(matching_component_ids)
            )
            statements.append(
                _result_query(
                    "TEST",
                    Test.id,
                    Test.name,
                    func.concat("Випробування · ", Test.test_type, " · ", Test.status),
                ).where(
                    or_(
                        Test.name.ilike(pattern),
                        Test.description.ilike(pattern),
                        Test.conclusion.ilike(pattern),
                        cast(Test.conditions, Text).ilike(pattern),
                        cast(Test.result_summary, Text).ilike(pattern),
                        Test.component_id.in_(matching_component_ids),
                        Test.setup_id.in_(related_setup_ids),
                        Test.id.in_(equipment_test_ids),
                    )
                )
            )

    if not statements:
        return Page(items=[], total=0, page=filters.page, page_size=filters.page_size)
    combined = union_all(*statements).subquery()
    total = session.scalar(select(func.count()).select_from(combined)) or 0
    rows = session.execute(
        select(combined)
        .order_by(func.lower(combined.c.title), combined.c.type, combined.c.id)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).mappings()
    path_prefix = {
        "PROJECT": "projects",
        "TASK": "tasks",
        "SETUP": "setups",
        "COMPONENT": "components",
        "TEST": "tests",
    }
    items = [
        SearchResult(
            type=row["type"],
            id=row["id"],
            title=row["title"],
            context=row["context"],
            path=f"/{path_prefix[row['type']]}/{row['id']}",
        )
        for row in rows
    ]
    return Page(items=items, total=total, page=filters.page, page_size=filters.page_size)
