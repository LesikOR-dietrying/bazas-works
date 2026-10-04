from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dashboard.schemas import (
    DashboardProblem,
    DashboardProject,
    DashboardRead,
    DashboardSetup,
    DashboardTest,
    EngineeringDashboard,
)
from app.modules.projects.access import visible_projects
from app.modules.projects.models import Project, ProjectStatus
from app.modules.setups.models import Setup, SetupStatus
from app.modules.tasks.models import Task, TaskStatus
from app.modules.tasks.queries import visible_tasks
from app.modules.tasks.service import task_summary
from app.modules.tests.models import Test, TestStatus
from app.modules.users.models import User
from app.modules.users.permissions import Capability, has_capability


def dashboard(session: Session, user: User) -> DashboardRead:
    projects = session.scalars(
        visible_projects(user)
        .where(Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.TESTING]))
        .order_by(Project.updated_at.desc(), Project.id)
        .limit(6)
    ).all()
    blocked = session.scalars(
        visible_tasks(user)
        .where(Task.status == TaskStatus.BLOCKED)
        .order_by(Task.updated_at.desc(), Task.id)
        .limit(6)
    ).all()
    engineering = None
    if has_capability(user, Capability.VIEW_RND_DASHBOARD):
        development = session.scalars(
            select(Setup)
            .where(Setup.status.in_([SetupStatus.DEVELOPMENT, SetupStatus.TESTING]))
            .order_by(Setup.updated_at.desc(), Setup.id)
            .limit(6)
        ).all()
        ready = session.scalars(
            select(Setup)
            .where(Setup.status == SetupStatus.READY)
            .order_by(Setup.updated_at.desc(), Setup.id)
            .limit(6)
        ).all()
        recent_tests = session.scalars(
            select(Test)
            .order_by(Test.test_date.desc().nulls_last(), Test.created_at.desc())
            .limit(8)
        ).all()
        failed = session.scalars(
            select(Test)
            .where(Test.status.in_([TestStatus.FAIL, TestStatus.PARTIAL]))
            .order_by(Test.test_date.desc().nulls_last(), Test.updated_at.desc())
            .limit(6)
        ).all()
        engineering = EngineeringDashboard(
            development_setups=[
                DashboardSetup(
                    id=item.id,
                    name=item.name,
                    version=item.version,
                    status=item.status,
                    updated_at=item.updated_at,
                )
                for item in development
            ],
            ready_setups=[
                DashboardSetup(
                    id=item.id,
                    name=item.name,
                    version=item.version,
                    status=item.status,
                    updated_at=item.updated_at,
                )
                for item in ready
            ],
            recent_tests=[
                DashboardTest(
                    id=item.id,
                    name=item.name,
                    test_type=item.test_type,
                    status=item.status,
                    test_date=item.test_date,
                )
                for item in recent_tests
            ],
            failed_tests=[
                DashboardProblem(
                    type="TEST",
                    id=item.id,
                    title=item.name,
                    status=item.status,
                    path=f"/tests/{item.id}",
                )
                for item in failed
            ],
        )
    return DashboardRead(
        my_tasks=task_summary(session, user),
        active_projects=[
            DashboardProject(
                id=item.id,
                name=item.name,
                status=item.status,
                responsible_name=item.responsible_name,
            )
            for item in projects
        ],
        blocked_tasks=[
            DashboardProblem(
                type="TASK",
                id=item.id,
                title=item.title,
                status=item.status,
                path=f"/tasks/{item.id}",
            )
            for item in blocked
        ],
        engineering=engineering,
    )
