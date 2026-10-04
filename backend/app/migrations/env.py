from alembic import context

from app.core.config import get_settings
from app.core.database import Base, create_database_engine
from app.modules.auth.models import AuthSession  # noqa: F401
from app.modules.comments.models import Comment  # noqa: F401
from app.modules.components.models import Component, UnitOfMeasure  # noqa: F401
from app.modules.files.models import Attachment  # noqa: F401
from app.modules.firmware.models import (  # noqa: F401
    FirmwareArtifact,
    FirmwareRelease,
    FirmwareRequirement,
    FirmwareRevision,
)
from app.modules.orders.models import (  # noqa: F401
    Customer,
    DeviationTest,
    MaterialRequirement,
    Order,
    OrderItem,
    OrderVariant,
    VariantDeviation,
)
from app.modules.procurement.models import (  # noqa: F401
    ProcurementAllocation,
    ProcurementRecord,
    Supplier,
)
from app.modules.production.models import (  # noqa: F401
    ProductionItem,
    StageChecklistResult,
    StageEvent,
    StageExecution,
)
from app.modules.products.models import (  # noqa: F401
    BomApprovedAlternative,
    Product,
    ProductCategory,
    ProductRevision,
    ProductRevisionBomItem,
    ProductRevisionDocument,
    ProductVariant,
)
from app.modules.projects.models import Project, ProjectMember  # noqa: F401
from app.modules.rnd.models import BranchConfiguration, RDBranch, RNDPromotionRequest  # noqa: F401
from app.modules.routes.models import (  # noqa: F401
    ProductionRoute,
    RouteStage,
    RouteStageDependency,
    RouteStageRole,
)
from app.modules.setups.models import ProjectSetup, Setup, SetupComponent  # noqa: F401
from app.modules.tasks.models import Task  # noqa: F401
from app.modules.technology.models import (  # noqa: F401
    ChecklistTemplateItem,
    TechnologyCard,
    TechnologyContentBlock,
    TechnologyOperation,
)
from app.modules.tests.models import Test, TestComponent, TestMeasurement  # noqa: F401
from app.modules.users.models import RoleDefinition, User, UserRole  # noqa: F401

# Import module models here to register their metadata before autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().sqlalchemy_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_database_engine(get_settings())
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata, compare_type=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
