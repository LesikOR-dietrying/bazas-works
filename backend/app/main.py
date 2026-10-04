from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.database import create_database_engine
from app.core.errors import register_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.auth.throttle import LoginThrottle
from app.modules.comments.router import router as comments_router
from app.modules.components.router import router as components_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.files.router import router as files_router
from app.modules.firmware.router import router as firmware_router
from app.modules.orders.router import router as orders_router
from app.modules.procurement.router import router as procurement_router
from app.modules.production.router import router as production_router
from app.modules.products.router import router as products_router
from app.modules.projects.router import router as projects_router
from app.modules.rnd.router import project_router as rnd_project_router
from app.modules.rnd.router import promotion_router as rnd_promotion_router
from app.modules.rnd.router import router as rnd_router
from app.modules.routes.router import router as production_routes_router
from app.modules.search.router import router as search_router
from app.modules.setups.router import project_router as project_setups_router
from app.modules.setups.router import router as setups_router
from app.modules.tasks.router import router as tasks_router
from app.modules.technology.router import router as technology_router
from app.modules.tests.router import router as tests_router
from app.modules.users.router import router as users_router


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        configuration.signing_key()
        application.state.engine = create_database_engine(configuration)
        try:
            yield
        finally:
            application.state.engine.dispose()

    application = FastAPI(
        title="BAZA API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if configuration.app_env != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if configuration.app_env != "production" else None,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    application.include_router(health_router, prefix="/api")
    application.state.settings = configuration
    application.state.login_throttle = LoginThrottle()
    register_error_handlers(application)
    application.include_router(auth_router, prefix="/api")
    application.include_router(users_router, prefix="/api")
    application.include_router(projects_router, prefix="/api")
    application.include_router(rnd_project_router, prefix="/api")
    application.include_router(rnd_router, prefix="/api")
    application.include_router(rnd_promotion_router, prefix="/api")
    application.include_router(tasks_router, prefix="/api")
    application.include_router(components_router, prefix="/api")
    application.include_router(setups_router, prefix="/api")
    application.include_router(project_setups_router, prefix="/api")
    application.include_router(firmware_router, prefix="/api")
    application.include_router(products_router, prefix="/api")
    application.include_router(technology_router, prefix="/api")
    application.include_router(production_routes_router, prefix="/api")
    application.include_router(orders_router, prefix="/api")
    application.include_router(procurement_router, prefix="/api")
    application.include_router(production_router, prefix="/api")
    application.include_router(tests_router, prefix="/api")
    application.include_router(files_router, prefix="/api")
    application.include_router(comments_router, prefix="/api")
    application.include_router(search_router, prefix="/api")
    application.include_router(dashboard_router, prefix="/api")
    return application
