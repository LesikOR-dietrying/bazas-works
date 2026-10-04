# CODEX PRODUCT SPEC — Internal R&D / Production System

## 0. Purpose

Build an internal web system for an engineering/manufacturing company that develops and produces UAVs, ground stations, repeaters, antennas, electronics and other technical products.

The system is not a generic CRM.

It is an internal **R&D + Product + Production + Inventory** system with strong traceability and a very simple UX for employees.

The system must be easy to use on a desktop and usable on a tablet on the shop floor.

The main rule:

> If an employee needs to fill more than 3–5 fields for a common production action, reconsider the UX.

If the system can infer data from Product, Revision, Order, User, Role or previous stage, do not ask the user to enter it again.

---

# 1. Main modules

There are only four top-level modules in the sidebar:

1. **R&D**
2. **Products**
3. **Production**
4. **Inventory**

Do not add more top-level modules unless explicitly requested.

Secondary entities such as Tasks, Tests, Firmware, Documents, Orders, Procurement, QC, Defects, Shipments, etc. live inside these four modules.

---

# 2. UX principles

The UI must feel like a modern engineering/manufacturing product, not an old ERP.

Use:
- clean tables
- checkboxes
- progress bars
- status badges
- filters
- search
- compact cards
- clear tabs
- sticky headers where useful
- inline editing where safe
- row actions
- clear empty states
- readable dark and light themes
- desktop-first layout
- tablet-friendly production screens

Avoid:
- giant modal forms
- 20-field create dialogs
- endless nested menus
- raw JSON
- showing database IDs to users
- too many colors
- too many icons
- duplicated information
- separate forms for data the system already knows
- forcing employees to manually update aggregate counters

The UI should calculate counters automatically from underlying unit/stage states.

Example:
- assembled = count of units that completed assembly stage
- flashed = count of units that completed firmware stage
- flight-tested = count of units that completed flight stage
- ready = count of units that passed final required stage
- defect = count of active defects

Employees must not manually type those totals.

---

# 3. Global visual style

Use a restrained engineering/industrial visual language.

Suggested:
- shadcn/ui
- Tailwind CSS
- Lucide icons
- TanStack Table for complex tables
- TanStack Query for server state
- React Hook Form + Zod
- Recharts for simple charts

Preferred table behavior:
- sortable columns
- filters
- search
- row selection where useful
- visible status
- optional compact density
- sticky first column when table is wide
- saved filters later if needed

Checkboxes should be used for:
- production step checklists
- tech-card instructions
- task completion
- QC items
- acceptance checks

Do not use checkbox state as a replacement for real workflow state when a stage needs audit history.

---

# 4. R&D module

R&D is for everything that is still being developed, tested or improved.

Projects are generic.

A project may be:
- UAV
- ground station
- repeater
- antenna
- motor test stand
- ESC
- camera system
- software
- RF system
- mechanical frame
- any other engineering project

## 4.1 Project

Project fields:
- name
- description
- goal
- status
- responsible_user_id
- participants
- start_date
- deadline
- created_at
- updated_at

Statuses:
- planned
- active
- testing
- completed
- frozen

Project page tabs:
- Overview
- Tasks
- Branches
- Setups / Configurations
- Tests
- Firmware
- Files
- Results

## 4.2 Tasks

Task fields:
- title
- description
- project_id
- assignee_id
- created_by_id
- status
- priority
- deadline
- result
- attachments

Statuses:
- todo
- in_progress
- blocked
- testing
- done

Priority:
- low
- normal
- high
- critical

Views:
- My Tasks
- All Tasks
- Table
- Kanban

Must support filters by:
- project
- assignee
- status
- priority
- deadline

## 4.3 R&D branches

Projects need lightweight Git-like branches for experiments and improvements.

Do not implement actual Git.

Example:

main
- new-motor-155kv
- new-frame-v2
- digital-video
- 12s-power

Branch fields:
- name
- project_id
- parent_branch_id nullable
- purpose
- status
- responsible_user_id
- summary_of_changes
- result_summary
- created_at
- closed_at

Branch page:
- purpose
- changed items
- tasks
- tests
- results
- files
- firmware/configs
- comparison to parent branch

A successful branch may be approved and promoted into a new Product Revision.

Important distinction:

- Branch = experimental development path
- Product Revision = approved production definition

Do not merge these concepts.

## 4.4 Setups / configurations

R&D setups are experimental configurations.

Example:
- Drone 15 / 6215 / 22in / 12S
- Drone 15 / 6212 / 17in / 12S
- Ground Station / Fiber / Rev2

A setup may reference:
- components
- firmware
- configuration files
- project branch
- tests
- flight logs
- notes

Do not hardcode drone-only fields into the core model.

Use a generic configuration model plus typed/specific attributes where needed.

## 4.5 Tests

R&D tests may include:
- motor bench
- ESC bench
- battery
- propeller
- antenna
- range
- endurance
- thermal
- flight
- ground station
- RF
- frame
- software
- other

Tests must be attachable to:
- project
- branch
- setup/configuration
- component

Test page:
- test type
- author/operator
- date
- conditions
- measurements
- result
- conclusion
- attachments
- logs
- photos
- charts where relevant

Motor test measurements may include:
- throttle
- voltage
- current
- power
- RPM
- thrust
- efficiency
- motor temperature
- ESC temperature

Flight test may include:
- flight duration
- current
- voltage
- consumed capacity
- distance
- speed
- temperatures
- log file
- result
- notes

---

# 5. Products module

Products contains approved items that the company knows how to manufacture.

Examples:
- Drone 15 Fiber
- Drone 15 Digital
- Ground Station Fiber
- Ground Station Digital
- Repeater
- Antenna Kit
- Cable Kit

Product is not the same as R&D Project.

A Product may originate from an approved R&D project/branch.

## 5.1 Product

Fields:
- name
- category
- description
- status
- current_revision_id
- image
- technical_characteristics
- user_manual
- notes

Statuses:
- development
- production
- deprecated

## 5.2 Product Revision

Every production-ready definition is versioned.

Examples:
- REV A
- REV B
- REV C
- REV D

A Product Revision contains:
- BOM
- production route
- technology card
- firmware requirements
- configuration files
- technical characteristics
- standard cost
- instructions
- drawings/photos/files
- QC requirements

Never silently overwrite an old revision.

If production definition changes permanently, create a new revision.

## 5.3 BOM

BOM = Bill of Materials / product specification.

Each BOM row:
- component
- quantity
- unit
- optional position
- notes
- required / optional
- approved alternatives later

The BOM must integrate with Inventory and Production.

From an order, the system must calculate:
- required quantity
- stock
- reserved
- ordered
- in transit
- missing

## 5.4 Technology card

Technology card is a visual step-by-step production instruction.

It is not just a PDF.

Each operation can contain:
- title
- assigned role
- description
- photos
- annotated photos
- wiring images
- connection instructions
- tools
- materials
- warnings
- checklist
- expected result
- acceptance criteria

Example:

Step 4 / 11 — FC wiring

Photo of FC

- RX -> UART2
- VTX -> UART4
- GPS -> UART6
- VBAT -> VBAT
- GND -> GND

Checklist:
- [ ] FC orientation correct
- [ ] RX soldered
- [ ] VTX soldered
- [ ] GPS soldered
- [ ] no short circuit
- [ ] visual inspection passed

Button:
- Complete stage

Keep the worker UI focused and visual.

## 5.5 Firmware per product revision

Each Product Revision may define required firmware/configuration.

Example:
- firmware type
- firmware version
- firmware package/file
- config file
- CLI dump
- notes

For a production unit, the firmware operator should see the exact required firmware automatically.

Do not make the worker guess which firmware belongs to the unit.

If changing firmware requires engineering approval, enforce permissions.

---

# 6. Production module

Production tracks work from customer/order request to shipment.

Core flow:

Order
-> order items
-> material requirements
-> procurement
-> available components
-> production
-> product-specific production route
-> QC / testing
-> ready
-> shipment

Production must work for drones and non-drone products.

Do not hardcode "flight test" as mandatory for all products.

Each Product Revision has its own configurable Production Route.

---

# 7. Orders

An order has:
- order number
- customer
- recipient
- destination
- order date
- deadline
- status
- notes

An order contains multiple order items.

Example:

ORDER-124
- 100 x Drone 15 Fiber
- 1 x Ground Station Fiber
- 4 x Antenna Kit

Order item fields:
- product
- product revision
- quantity
- required date
- configuration variant(s)
- notes

Order page should clearly show progress for every line item.

Example:

Drone 15 Fiber — 100 pcs
- components readiness: 91%
- assembled: 68 / 100
- flashed: 61 / 100
- tested: 54 / 100
- flight tested: 54 / 100 only if route includes flight
- ready: 51 / 100
- defects: 3
- repair: 2

Ground Station Fiber — 1 pc
- components readiness: 100%
- assembled: 1 / 1
- flashed: 1 / 1
- functional test: 1 / 1
- ready: 1 / 1

All counters must be derived automatically.

---

# 8. Procurement inside Production

Do not make Procurement a separate top-level module.

It belongs inside Production.

When an order is created, calculate material requirements from Product Revision BOMs.

Procurement screen should show a compact table:

| Component | Required | Available | Reserved | Ordered | In transit | Missing | ETA |
|-----------|----------|-----------|----------|---------|------------|---------|-----|

Procurement status options:
- required
- RFQ
- ordered
- paid
- in_transit
- customs
- received
- issue

Procurement record fields:
- component
- supplier
- quantity
- price
- currency
- order date
- expected date
- tracking number
- status
- notes

Later this integrates with Inventory.

---

# 9. Dynamic substitutions / order variants

This is critical.

Real production often cannot use the exact standard BOM because the required component is unavailable.

Do not modify the approved Product Revision just because one order needs a temporary replacement.

Use an Order Variant / Production Variant.

Example standard product:
Drone 15 Fiber REV4
- Motor 6215

ORDER-124 needs 100 units.

Only enough 6215 motors for 90 units.

Create:

Variant A
- 90 units
- standard REV4
- Motor 6215

Variant B
- 10 units
- REV4 + approved deviation
- Motor 6212

Deviation fields:
- original component
- replacement component
- quantity of affected units
- reason
- requested_by
- approved_by
- date
- notes
- required retest flag
- linked tests if needed

The UI must make this easy.

Suggested flow:

Component shortage detected
-> "Request replacement"
-> engineer selects replacement
-> system shows affected products/orders/quantity
-> engineer approves
-> variant created automatically

Do not silently rewrite the base BOM.

If the replacement becomes standard later:
- allow "Promote to new Product Revision"
- create REV5 from REV4 + approved changes

---

# 10. Production routes

Each Product Revision has its own configurable route.

Example Drone route:
1. Material picking
2. Mechanical assembly
3. Electronics assembly
4. Firmware
5. Configuration
6. Ground test
7. Flight test
8. QC
9. Packaging
10. Ready

Example Ground Station route:
1. Material picking
2. Mechanical assembly
3. Electronics assembly
4. Firmware
5. Functional test
6. QC
7. Packaging
8. Ready

Example Antenna route:
1. Material picking
2. Assembly
3. VNA measurement
4. QC
5. Packaging
6. Ready

Every route stage may define:
- name
- required role(s)
- technology-card instruction
- checklist
- required previous stage
- pass/fail support
- whether measurements are required
- whether attachments are required

Do not assume every product uses the same route.

---

# 11. Tracking modes

Different products need different tracking granularity.

Add product tracking mode:

## SERIAL

Every unit has its own serial number / unit ID.

Use for:
- UAVs
- ground stations
- repeaters
- expensive equipment

Example:
D15-00451

Track:
- exact product revision
- order
- order variant
- completed stages
- workers
- firmware
- defects
- tests
- QC
- shipment

## BATCH

Track a batch as a group.

Use for:
- antennas
- repeated mechanical items
- small assemblies

Example:
ANT-BATCH-0045
Quantity: 50

## QUANTITY

Simple quantity progress only.

Use for:
- cable kits
- simple accessory sets

This avoids forcing workers to click 100 times for simple products.

---

# 12. Production worker UX

Production workers must not work in giant tables all day.

Primary worker flow:

1. Log in
2. See "My Work"
3. Scan QR or select unit/batch
4. See current stage
5. Read visual instruction
6. Complete checklist
7. Press Complete
8. System automatically moves item to next stage

Example:

My Work

3 units waiting for Electronics Assembly:
- D15-00541
- D15-00542
- D15-00543

[Scan QR]

Unit page:

D15-00541
Drone 15 Fiber REV4

Current stage:
Electronics Assembly

[Start]

Visual instructions...

Checklist...

[Complete Stage]

Do not show irrelevant company-wide data to shop-floor roles.

---

# 13. QR / unit identity

For SERIAL products generate QR codes.

QR opens the unit page.

The unit page displays:
- unit ID
- product
- revision
- order
- current stage
- assigned work
- warnings
- active defect
- required firmware/config
- stage history

QR should be printable.

---

# 14. Defects and rework

Workers/testers should not manually maintain aggregate defect counters.

At a test/QC stage:
- PASS
- FAIL

If FAIL:
create a Defect / Nonconformity.

Fields:
- unit/batch
- stage
- issue type
- description
- severity
- component if relevant
- created_by
- assigned_to
- status
- resolution
- attachments

Possible resolutions:
- repair
- component replaced
- rework
- scrap
- accepted deviation
- returned to previous stage

After repair/rework, unit may return to a configured previous stage.

Preserve audit history.

---

# 15. Inventory module

Inventory will be implemented later, but design interfaces now.

Important future quantities:
- physical stock
- reserved
- available
- defective
- incoming
- in transit

Do not deeply implement warehouse logic in the first milestone.

But BOM and Procurement models must be designed so Inventory can be connected later without major schema rewrite.

---

# 16. Roles

A user can have multiple roles.

Do not use one `role` string on User.

Use many-to-many:
User <-> Role

Initial roles:
- Administrator
- Engineer
- R&D Engineer
- Production Manager
- Procurement Specialist
- Assembler
- Electronics Technician
- Firmware Engineer
- Test Pilot
- Test Engineer
- Quality Controller

Use professional names.

Preferred Ukrainian display names:
- Адміністратор
- Інженер
- R&D інженер
- Керівник виробництва
- Спеціаліст із закупівель
- Складальник
- Монтажник електроніки
- Інженер з прошивок
- Пілот-випробувач
- Інженер-випробувач
- Контролер якості

Permissions must be enforced on backend.

The UI should hide irrelevant sections/actions, but backend authorization is mandatory.

---

# 17. Main navigation

Keep sidebar very simple:

Dashboard

R&D

Products

Production

Inventory

My Tasks / My Work

Admin / Settings only for permitted users

Do not create 15 main navigation items.

Use tabs inside modules.

---

# 18. Dashboard

Dashboard content depends on role.

Management dashboard may show:
- active orders
- order progress
- overdue orders
- component shortages
- production bottlenecks
- defect count
- ready for shipment
- active R&D projects
- overdue tasks

Engineer dashboard:
- my R&D projects
- my tasks
- pending substitutions
- failed tests
- branches awaiting review

Production worker dashboard:
- My Work
- units waiting for my role
- QR scan action
- active rework

Procurement dashboard:
- missing components
- purchase requirements
- overdue ETA
- in-transit items
- substitution requests

Do not show irrelevant widgets.

---

# 19. Tables

Tables are a first-class UX element.

Use them where they improve speed and clarity.

Examples:
- tasks
- orders
- procurement
- BOM
- product revisions
- test results
- production units
- defects

Tables should support:
- search
- sorting
- filters
- pagination or virtualization if needed
- status badges
- quick row actions
- row click to details
- optional checkbox selection for bulk actions

For production progress, prefer compact counters and progress bars over huge tables.

---

# 20. Checklists

Use checklists extensively in:
- technology cards
- QC
- setup verification
- production stage completion
- acceptance
- R&D task subtasks

Checklist item model should support:
- text
- required
- completed
- completed_by
- completed_at
- optional note
- optional photo/attachment requirement

If checklist is part of an audited production stage, preserve historical completion data.

---

# 21. Audit and history

Important changes must be traceable.

Track:
- who
- what
- when

At minimum for:
- Product Revision
- BOM change
- firmware change
- order variant/deviation
- production stage completion
- defect resolution
- substitution approval
- R&D branch promotion

Do not build a giant enterprise audit platform initially.

But preserve basic history so we can answer:
- who changed this?
- when?
- why?
- which units/orders were affected?

---

# 22. Files and attachments

Support attachments for:
- projects
- branches
- tests
- products
- product revisions
- technology cards
- firmware
- orders
- defects
- units

Files may include:
- photos
- PDF
- CSV
- Excel
- BBL
- BIN
- TLOG
- firmware
- config files
- drawings
- STEP
- ZIP
- manuals

Binary files must not be stored directly in PostgreSQL.

Use a storage abstraction:
- local storage first
- MinIO/S3 later

Database stores metadata and storage key/path.

---

# 23. Technical architecture

Keep the software architecture simple.

Use a modular monolith.

Recommended stack:

Backend:
- Python
- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic
- PostgreSQL
- psycopg
- PyJWT
- pwdlib[argon2]
- pytest

Frontend:
- React
- TypeScript
- Vite
- React Router
- TanStack Query
- TanStack Table
- React Hook Form
- Zod
- Tailwind CSS
- shadcn/ui
- Lucide
- Recharts

Infrastructure:
- Docker Compose
- PostgreSQL
- backend
- frontend

Do not add:
- Kubernetes
- microservices
- Kafka
- Elasticsearch
- Redis
- Celery
unless a later requirement clearly needs them.

---

# 24. Coding rules for Codex

Before changing code:
1. Read this file.
2. Read `ARCHITECTURE.md`.
3. Inspect the current repository.
4. Do not assume the repository is empty.
5. Reuse existing working code where sensible.
6. Do not rewrite large modules without explaining why.

For every non-trivial change:
- state what you plan to change
- state which entities/files are affected
- implement
- run tests
- run frontend build
- summarize result

Do not generate giant files.

Use clear module boundaries.

Do not create abstraction for abstraction's sake.

Do not add dependencies unless necessary.

If adding a dependency:
- explain why
- prefer a mature, well-supported library

No hardcoded secrets.

Use `.env` and `.env.example`.

Use Alembic for database migrations.

Do not use `create_all()` as production migration strategy.

---

# 25. UX rules for Codex

Before generating a CRUD page, ask:

"Does the user really need a generic CRUD page?"

Prefer role-specific workflows.

Examples:

Bad:
- worker opens ProductionUnit table
- searches ID
- edits status dropdown
- saves form

Good:
- worker scans QR
- sees current operation
- completes checklist
- presses Complete

Bad:
- procurement specialist manually types required quantity

Good:
- system calculates required quantity from order + BOM

Bad:
- firmware operator chooses firmware from 50 files

Good:
- system displays exact required firmware for the unit revision/variant

Bad:
- manager manually updates "assembled = 44"

Good:
- system derives 44 from completed stages

---

# 26. Initial implementation phases

Do not attempt the whole system at once.

## Phase 0 — architecture

Before major code changes:
- inspect repository
- map existing entities
- propose revised entity model
- create/update `ARCHITECTURE.md`
- create Mermaid ER diagram
- identify reusable existing code
- identify migration impact
- create implementation roadmap

STOP after Phase 0 and report the plan before destructive refactoring.

## Phase 1 — foundation / auth / roles

- users
- multiple roles
- permissions
- sidebar
- role-based dashboard shell
- audit helpers

## Phase 2 — R&D

- projects
- tasks
- branches
- setups/configurations
- tests
- firmware/files

## Phase 3 — Products

- products
- revisions
- BOM
- technology card
- production route
- firmware requirements
- documentation

## Phase 4 — Production Orders

- orders
- order items
- order variants
- component requirements
- procurement tracking

## Phase 5 — Production Execution

- units/batches/quantity tracking modes
- production stages
- worker "My Work"
- QR unit flow
- stage checklists
- automatic progress counters

## Phase 6 — Quality / defects / shipment

- pass/fail
- defects
- repair/rework
- final readiness
- shipment

## Phase 7 — Inventory

Implement only after the production model is stable.

---

# 27. Important domain invariants

These rules must remain true:

1. R&D Project != Product.
2. R&D Branch != Product Revision.
3. Product Revision is immutable once used in production, except controlled metadata corrections.
4. Temporary component substitution must not silently modify the base Product Revision.
5. Temporary substitution creates an approved order/production variant or deviation.
6. A successful recurring deviation may be promoted into a new Product Revision.
7. Every Product Revision has its own configurable Production Route.
8. Flight Test is only present when the route requires it.
9. Aggregate production counts are derived from underlying states.
10. Workers should interact with stages/checklists, not database-like status forms.
11. Historical production traceability must be preserved.
12. A user may have multiple roles.
13. Inventory must later integrate with BOM and Procurement without redesigning the entire system.

---

# 28. Current priority

The immediate goal is not to implement everything.

The immediate goal is to make sure the architecture supports:

R&D
-> approved Product Revision
-> Order
-> component requirements / procurement
-> optional substitutions / variants
-> production route
-> stage completion
-> QC / testing
-> ready
-> shipment

with a clean table/checklist-oriented UX.

Start by reviewing the current repository and creating/updating `ARCHITECTURE.md`.

Do not perform destructive refactoring until the new entity model and migration plan are shown and approved.
