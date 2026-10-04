from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.tasks.schemas import TaskSummary


class DashboardProject(BaseModel):
    id: UUID
    name: str
    status: str
    responsible_name: str


class DashboardSetup(BaseModel):
    id: UUID
    name: str
    version: str
    status: str
    updated_at: datetime


class DashboardTest(BaseModel):
    id: UUID
    name: str
    test_type: str
    status: str
    test_date: datetime | None


class DashboardProblem(BaseModel):
    type: str
    id: UUID
    title: str
    status: str
    path: str


class EngineeringDashboard(BaseModel):
    development_setups: list[DashboardSetup]
    ready_setups: list[DashboardSetup]
    recent_tests: list[DashboardTest]
    failed_tests: list[DashboardProblem]


class DashboardRead(BaseModel):
    my_tasks: TaskSummary
    active_projects: list[DashboardProject]
    blocked_tasks: list[DashboardProblem]
    engineering: EngineeringDashboard | None
