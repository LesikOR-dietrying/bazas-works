from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUser, Database
from app.modules.dashboard.schemas import DashboardRead
from app.modules.dashboard.service import dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def read_dashboard(session: Database, user: CurrentUser) -> DashboardRead:
    return dashboard(session, user)
