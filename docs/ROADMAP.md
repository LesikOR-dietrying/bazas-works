# План реалізації за CODEX_PRODUCT_SPEC

> Статус: доменні Phase 0–5 та етапи rework 0–3 реалізовано. Поточний застосунок
> і migrations `0001–0012` є робочим additive baseline.

## Phase 0 — Architecture (proposal complete)

- [x] Повністю прочитано `CODEX_PRODUCT_SPEC.md`.
- [x] Проінвентаризовано ORM models, migrations, API, access rules, frontend
  routes/navigation, tests, storage та Compose.
- [x] Визначено reusable code і gaps.
- [x] Спроєктовано R&D → Product Revision → Order → Production flow.
- [x] Спроєктовано branches, immutable revisions, BOM, technology cards,
  configurable routes, substitutions, tracking modes та automatic counters.
- [x] Уточнено username authentication, reusable firmware artifact/release,
  explicit work assignment, extensible content blocks та annotated-image source.
- [x] Додано ER diagram, permission model і migration risks до ARCHITECTURE.md.
- [x] Жодної destructive migration або application refactor не виконано.

Approval gate: погодити терміни, entity boundaries, role mapping, migration
strategy та implementation order.

## Phase 1 — Foundation, multi-role authorization and shell

**Статус: завершено.**

Backend:

- additive normalized username migration; optional email; username login while
  existing UUID/session rows remain valid;
- additive `roles`/`user_roles` migration and deterministic legacy backfill;
- capability policy, ownership predicates, active-admin invariant;
- audit helpers for explicit domain events;
- compatibility layer while `users.role` still exists.

Frontend:

- sidebar `Dashboard / R&D / Products / Production / Inventory`;
- `My Tasks / My Work` shortcuts and role-sensitive dashboard shell;
- multi-role Users editor with professional Ukrainian labels.
- real-data role-sensitive dashboard and structural My Work empty state.

Acceptance:

- existing admin and sessions remain usable after upgrade;
- login uses `Логін` + password; normalized username is unique;
- users may hold multiple roles; backend denies unauthorized direct requests;
- all current backend tests and R&D E2E continue to pass.

## Phase 2 — R&D evolution

**Статус: реалізовано; PostgreSQL/Compose/E2E перевірку очікує середовище з virtualization.**

- [x] project goal/start date/deadline and status compatibility;
- [x] R&D branches with parent, responsible user, summaries and close/review flow;
- [x] branch-scoped tasks/tests/configurations/files/firmware;
- [x] generic configuration attributes while preserving current Setup UUID/data;
- [x] configuration comparison and explicit promotion request.

Acceptance:

- create main/child branch, compare candidate configuration with baseline,
  attach tests/files and submit promotion;
- existing projects/tasks/setups/tests remain accessible without data loss;
- no R&D branch is presented as a Product Revision.

## Phase 3 — Products and approved production definition

**Статус: реалізовано, включно з постійними комплектаціями каталогу.**

- UOM and shared component catalog extensions;
- products, extensible categories and SERIAL/BATCH/QUANTITY mode;
- persistent ProductVariant configurations with compatible Standard backfill;
- draft/review/released Product Revisions and explicit R&D promotion;
- revision BOM and approved alternatives;
- visual technology cards, photos, operation checklist templates;
- extensible TechnologyContentBlock and editable annotated-image source model;
- configurable route stages/dependencies/required roles;
- exact firmware/config requirements and documentation.

Acceptance:

- promote approved R&D evidence into a draft, review and release a snapshot;
- released definition is immutable and cloneable to the next revision;
- UAV, ground station and antenna routes differ without code/schema changes;
- worker preview shows photos/checklist and exact firmware requirement.

## Phase 4 — Orders, variants, requirements and procurement

- customers, orders and multi-line items pinned to released revisions;
- automatic standard variant and quantity partitions;
- requested/approved deviations and replacement impact preview;
- optional retest evidence and promote-deviation-to-new-revision action;
- calculated material requirement snapshots;
- procurement records and requirement allocations;
- compact required/available/reserved/ordered/in-transit/missing read model.

Acceptance:

- 100-unit order can split 90 standard + 10 approved substitution;
- base revision BOM remains unchanged;
- variant quantities equal order line before release;
- required/missing quantities are calculated, never manually entered.

## Phase 5 — Production execution and worker UX

- ProductionItem for SERIAL/BATCH/QUANTITY;
- serial/batch identifiers, printable QR and scan route;
- stage attempts/events, dependency enforcement and role assignment;
- nullable explicit worker assignment distinct from RouteStage role eligibility;
- historical checklist snapshots with required note/photo;
- tablet-oriented `My Work` and focused Start/Complete workflow;
- derived order/variant progress bars and bottleneck read models.

Acceptance:

- SERIAL UAV advances unit-by-unit; BATCH antenna advances as a batch;
  QUANTITY cable kit completes N pieces in one action;
- route controls whether flight/VNA/functional stages exist;
- duplicate completion is idempotent and audit history names the worker;
- assembled/flashed/tested/ready counters exactly match stage evidence.

## Phase 6 — Quality, defects, rework and shipment

- stage PASS/FAIL and automatic defect creation on failure;
- defect severity, assignment, attachments and append-only events;
- repair/rework/scrap/accepted-deviation resolution;
- configured return to a previous route stage with a new attempt;
- final readiness and shipment allocations.

Acceptance:

- failed QC removes item quantity from ready count and opens a defect;
- repaired item returns through configured stage without deleting history;
- shipment cannot exceed effective ready quantity;
- defect/repair/shipped counters derive from underlying records.

## Phase 7 — Inventory

- locations, stock lots, movements and reservations;
- physical/reserved/available/defective/incoming/in-transit quantities;
- receipts connected to procurement and reservations connected to variants;
- material picking consumption and traceability where required.

Acceptance:

- BOM/procurement models integrate without redesign;
- stock cannot be silently negative; adjustments are audited;
- availability feeds the material readiness read model.

## Cross-phase delivery rules

- one reviewed Alembic migration per schema step; never edit `0001–0006`;
- expand/migrate/contract; destructive cleanup has a separate approval gate;
- routes stay thin, services own authorization/business transactions;
- every phase preserves existing data and keeps Compose deployable;
- backend PostgreSQL tests/Ruff/package, frontend tests/ESLint/build,
  Playwright and Compose validation are mandatory before the next phase;
- no editable production aggregate counters and no fake dashboard data.

## Phase 3 - Products (implemented)

- Product categories, lifecycle and serial/batch/quantity tracking.
- Draft/review/released/retired revisions with release immutability and clone flow.
- Explicit approved R&D promotion into a draft revision and BOM snapshot.
- Revision BOM, alternatives, firmware requirements, technology cards and route DAGs.
- Products catalog/detail UI with revision, BOM, worker preview, firmware, route and document tabs.

## Phase 4 - Orders and procurement (implemented)

- Customers and multi-line orders are pinned to RELEASED product revisions.
- Every line starts with a standard variant; managers can partition quantity and request a
  component substitution without changing the released BOM.
- Substitutions have an explicit approval decision and optional retest evidence links.
- Releasing a complete variant partition creates immutable material-requirement snapshots.
- Supplier, procurement and requirement-allocation records feed the material readiness view.
- Production UI shows order status, 90/10-style partitions, material progress and procurement.

## Phase 5 - Production execution and worker UX (implemented)

- Released variants launch into SERIAL units or grouped BATCH/QUANTITY production items.
- Every route stage gets an audited execution; dependency completion unlocks the next work.
- Required stage roles and optional explicit assignment control worker eligibility on the backend.
- Technology instructions and checklist templates drive a tablet-oriented Start/Complete flow.
- Checklist text and requirements are snapshotted with worker, time, note and photo evidence.
- Completion requests are idempotent; QUANTITY work supports partial quantity completion.
- Order progress and per-stage counters are derived from execution evidence.
- Production managers can print local SVG QR labels that open the unit page.

Phase 6 remains out of scope: defects, rework, QC failure handling and shipment allocation are not
started.

## Visual system refresh after Phase 5 (implemented)

- Shared application shell now uses a restrained engineering visual language with grouped primary,
  personal and administration navigation, a compact global search and a clearer signed-in identity.
- Tables, filters, panels, status badges, progress bars and responsive breakpoints share one visual
  system across R&D, Products and Production.
- The R&D landing page now explains the Project -> Branch -> Configuration -> Evidence flow and
  provides distinct engineering-library entry points without adding fake metrics.
- Desktop remains the primary layout; the navigation collapses for narrow screens and production
  worker controls retain their tablet-focused sizing.

Phase 6 should reuse this visual system for quality, defects, rework and shipment screens.
