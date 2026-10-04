from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import Identity, Timestamps


class ProductionRoute(Identity, Timestamps, Base):
    __tablename__ = "production_routes"
    __table_args__ = (
        UniqueConstraint("revision_id", "version", name="uq_routes_revision_version"),
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_revisions.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="", server_default="")


class RouteStage(Identity, Timestamps, Base):
    __tablename__ = "route_stages"
    __table_args__ = (
        UniqueConstraint("route_id", "code", name="uq_route_stages_code"),
        UniqueConstraint("route_id", "sequence", name="uq_route_stages_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_nonnegative"),
        CheckConstraint("length(trim(code)) > 0", name="code_nonempty"),
        CheckConstraint("length(trim(name)) > 0", name="name_nonempty"),
    )

    route_id: Mapped[UUID] = mapped_column(
        ForeignKey("production_routes.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer)
    technology_operation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("technology_operations.id", ondelete="RESTRICT")
    )
    supports_pass_fail: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    measurement_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    attachment_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    instructions: Mapped[str] = mapped_column(Text, default="", server_default="")


class RouteStageDependency(Identity, Base):
    __tablename__ = "route_stage_dependencies"
    __table_args__ = (
        UniqueConstraint("stage_id", "predecessor_id", name="uq_stage_dependencies_edge"),
        CheckConstraint("stage_id <> predecessor_id", name="not_self"),
    )

    stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("route_stages.id", ondelete="CASCADE"), index=True
    )
    predecessor_id: Mapped[UUID] = mapped_column(
        ForeignKey("route_stages.id", ondelete="CASCADE"), index=True
    )


class RouteStageRole(Identity, Base):
    __tablename__ = "route_stage_roles"
    __table_args__ = (UniqueConstraint("stage_id", "role_id", name="uq_route_stage_roles"),)

    stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("route_stages.id", ondelete="CASCADE"), index=True
    )
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"))
