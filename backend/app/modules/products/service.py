from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import Page, paginate, search_pattern
from app.modules.components.models import Component
from app.modules.products.models import (
    BomApprovedAlternative,
    Product,
    ProductCategory,
    ProductLifecycle,
    ProductRevision,
    ProductRevisionBomItem,
    RevisionStatus,
)
from app.modules.products.schemas import (
    AlternativeWrite,
    BomItemWrite,
    ProductFilters,
    ProductWrite,
    RevisionWrite,
)
from app.modules.rnd.models import PromotionRequestStatus, RNDPromotionRequest
from app.modules.setups.models import SetupComponent
from app.modules.users.models import User
from app.modules.users.permissions import Capability, require_capability


def _view(user: User) -> None:
    require_capability(
        user, Capability.VIEW_ENGINEERING, "Недостатньо прав для перегляду продуктів."
    )


def _edit(user: User) -> None:
    require_capability(user, Capability.MANAGE_ENGINEERING, "Недостатньо прав для зміни продуктів.")


def categories(session: Session, user: User) -> list[ProductCategory]:
    _view(user)
    return list(
        session.scalars(
            select(ProductCategory).where(ProductCategory.is_active).order_by(ProductCategory.name)
        )
    )


def list_products(session: Session, user: User, filters: ProductFilters) -> Page[Product]:
    _view(user)
    statement = select(Product)
    if filters.q:
        pattern = search_pattern(filters.q)
        statement = statement.where(or_(Product.name.ilike(pattern), Product.code.ilike(pattern)))
    for field in ("category_id", "lifecycle", "tracking_mode"):
        value = getattr(filters, field)
        if value is not None:
            statement = statement.where(getattr(Product, field) == value)
    return paginate(session, statement.order_by(Product.updated_at.desc(), Product.id), filters)


def get_product(session: Session, product_id: UUID, user: User, *, lock: bool = False) -> Product:
    _view(user)
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update(of=Product)
    item = session.scalar(statement)
    if item is None:
        raise DomainError(404, "Продукцію не знайдено.")
    return item


def _commit(session: Session, message: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DomainError(409, message) from None


def create_product(session: Session, user: User, data: ProductWrite) -> Product:
    _edit(user)
    if session.get(ProductCategory, data.category_id) is None:
        raise DomainError(422, "Категорію продукції не знайдено.")
    product = Product(**data.model_dump(mode="json"))
    session.add(product)
    _commit(session, "Код продукту вже використовується.")
    session.refresh(product)
    return product


def update_product(session: Session, product_id: UUID, user: User, data: ProductWrite) -> Product:
    _edit(user)
    product = get_product(session, product_id, user, lock=True)
    if session.get(ProductCategory, data.category_id) is None:
        raise DomainError(422, "Категорію продукції не знайдено.")
    for key, value in data.model_dump(mode="json").items():
        setattr(product, key, value)
    _commit(session, "Код продукту вже використовується.")
    session.refresh(product)
    return product


def list_revisions(session: Session, product_id: UUID, user: User) -> list[ProductRevision]:
    get_product(session, product_id, user)
    return list(
        session.scalars(
            select(ProductRevision)
            .where(ProductRevision.product_id == product_id)
            .order_by(ProductRevision.created_at.desc())
        )
    )


def get_revision(
    session: Session, revision_id: UUID, user: User, *, lock: bool = False
) -> ProductRevision:
    _view(user)
    statement = select(ProductRevision).where(ProductRevision.id == revision_id)
    if lock:
        statement = statement.with_for_update(of=ProductRevision)
    revision = session.scalar(statement)
    if revision is None:
        raise DomainError(404, "Версію продукції не знайдено.")
    return revision


def require_draft(revision: ProductRevision) -> None:
    if revision.status != RevisionStatus.DRAFT:
        raise DomainError(409, "Змінювати вміст можна лише у чернетці версії.")


def create_revision(
    session: Session, product_id: UUID, user: User, data: RevisionWrite
) -> ProductRevision:
    _edit(user)
    get_product(session, product_id, user)
    revision = ProductRevision(
        product_id=product_id, created_by_id=user.id, **data.model_dump(mode="json")
    )
    session.add(revision)
    _commit(session, "Код ревізії вже використовується для цього продукту.")
    session.refresh(revision)
    return revision


def update_revision(
    session: Session, revision_id: UUID, user: User, data: RevisionWrite
) -> ProductRevision:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    for key, value in data.model_dump(mode="json").items():
        setattr(revision, key, value)
    _commit(session, "Код ревізії вже використовується для цього продукту.")
    session.refresh(revision)
    return revision


def transition_revision(
    session: Session, revision_id: UUID, user: User, target: RevisionStatus
) -> ProductRevision:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    allowed = {
        RevisionStatus.DRAFT: {RevisionStatus.IN_REVIEW},
        RevisionStatus.IN_REVIEW: {RevisionStatus.DRAFT, RevisionStatus.RELEASED},
        RevisionStatus.RELEASED: {RevisionStatus.RETIRED},
        RevisionStatus.RETIRED: set(),
    }
    if target not in allowed[RevisionStatus(revision.status)]:
        raise DomainError(409, "Недопустимий перехід стану версії.")
    if target == RevisionStatus.RELEASED:
        require_capability(
            user, Capability.MANAGE_PROJECTS, "Випускати ревізії може керівник проєкту."
        )
        revision.released_at = datetime.now(UTC)
        revision.released_by_id = user.id
        revision.product.current_revision_id = revision.id
        revision.product.lifecycle = ProductLifecycle.PRODUCTION
    revision.status = target
    session.commit()
    session.refresh(revision)
    return revision


def promote(
    session: Session, product_id: UUID, user: User, request_id: UUID, revision_code: str
) -> ProductRevision:
    _edit(user)
    get_product(session, product_id, user)
    request = session.get(RNDPromotionRequest, request_id)
    if request is None or request.status != PromotionRequestStatus.APPROVED:
        raise DomainError(409, "Передавання має бути схвалене в розробці.")
    revision = ProductRevision(
        product_id=product_id,
        revision_code=revision_code.strip(),
        status=RevisionStatus.DRAFT,
        source_branch_id=request.branch_id,
        source_setup_id=request.candidate_setup_id,
        source_promotion_request_id=request.id,
        created_by_id=user.id,
    )
    session.add(revision)
    session.flush()
    rows = session.scalars(
        select(SetupComponent).where(SetupComponent.setup_id == request.candidate_setup_id)
    ).all()
    for sequence, row in enumerate(rows):
        component = session.get(Component, row.component_id)
        assert component is not None
        session.add(
            ProductRevisionBomItem(
                revision_id=revision.id,
                component_id=row.component_id,
                quantity=row.quantity,
                uom_id=component.default_uom_id,
                position=row.position,
                sequence=sequence,
                notes=row.notes,
            )
        )
    _commit(session, "Цей promotion або код ревізії вже використано.")
    session.refresh(revision)
    return revision


def list_bom(session: Session, revision_id: UUID, user: User) -> list[ProductRevisionBomItem]:
    get_revision(session, revision_id, user)
    return list(
        session.scalars(
            select(ProductRevisionBomItem)
            .where(ProductRevisionBomItem.revision_id == revision_id)
            .order_by(ProductRevisionBomItem.sequence, ProductRevisionBomItem.id)
        )
    )


def add_bom(
    session: Session, revision_id: UUID, user: User, data: BomItemWrite
) -> ProductRevisionBomItem:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    component = session.get(Component, data.component_id)
    if component is None:
        raise DomainError(422, "Компонент не знайдено.")
    values = data.model_dump(mode="json")
    values["uom_id"] = values["uom_id"] or component.default_uom_id
    row = ProductRevisionBomItem(revision_id=revision_id, **values)
    session.add(row)
    _commit(session, "Такий рядок BOM уже існує.")
    session.refresh(row)
    return row


def delete_bom(session: Session, revision_id: UUID, item_id: UUID, user: User) -> None:
    _edit(user)
    revision = get_revision(session, revision_id, user, lock=True)
    require_draft(revision)
    row = session.scalar(
        select(ProductRevisionBomItem).where(
            ProductRevisionBomItem.id == item_id, ProductRevisionBomItem.revision_id == revision_id
        )
    )
    if row is None:
        raise DomainError(404, "Рядок специфікації не знайдено.")
    session.delete(row)
    session.commit()


def add_alternative(
    session: Session, item_id: UUID, user: User, data: AlternativeWrite
) -> BomApprovedAlternative:
    _edit(user)
    row = session.get(ProductRevisionBomItem, item_id)
    if row is None:
        raise DomainError(404, "Рядок специфікації не знайдено.")
    require_draft(get_revision(session, row.revision_id, user, lock=True))
    alternative = BomApprovedAlternative(bom_item_id=item_id, **data.model_dump(mode="json"))
    session.add(alternative)
    _commit(session, "Цю альтернативу вже додано.")
    session.refresh(alternative)
    return alternative


def clone_revision(session: Session, revision_id: UUID, user: User, code: str) -> ProductRevision:
    _edit(user)
    source = get_revision(session, revision_id, user)
    clone = ProductRevision(
        product_id=source.product_id,
        revision_code=code.strip(),
        status=RevisionStatus.DRAFT,
        technical_characteristics=source.technical_characteristics,
        standard_cost=source.standard_cost,
        currency=source.currency,
        revision_instructions=source.revision_instructions,
        created_by_id=user.id,
    )
    session.add(clone)
    session.flush()
    for row in list_bom(session, source.id, user):
        session.add(
            ProductRevisionBomItem(
                revision_id=clone.id,
                component_id=row.component_id,
                quantity=row.quantity,
                uom_id=row.uom_id,
                position=row.position,
                sequence=row.sequence,
                required=row.required,
                notes=row.notes,
            )
        )
    from app.modules.products.clone import clone_revision_definition

    clone_revision_definition(session, source.id, clone.id)
    _commit(session, "Код нової ревізії вже використовується.")
    session.refresh(clone)
    return clone
