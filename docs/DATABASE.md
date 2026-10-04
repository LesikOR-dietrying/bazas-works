# Цільова модель PostgreSQL

> Цей файл фіксує **поточну реалізовану схему `0001–0013`**. Цільова модель і
> подальші межі описані в [ARCHITECTURE.md](../ARCHITECTURE.md).

Реалізовано users/auth_sessions (0002), projects/project_members/tasks (0003),
components/setups/setup_components/project_setups/firmware_revisions (0004),
tests/test_components/test_measurements (0005), attachments/comments (0006) та
username/multi-role authorization (0007) та R&D branches/configuration comparison (0008).
Baseline 0001 створює лише Alembic version marker.

## Спільні правила

- Усі entity/link `id`: UUID primary key, генерується backend (`uuid4`).
- `created_at`, `updated_at`: timestamptz NOT NULL, UTC, default now();
  updated_at оновлюється application layer при зміні. Незмінні записи мають
  лише created_at. Позначка **timestamps** означає обидва поля.
- Рядки ідентифікації: varchar(255), username/email varchar(320), описи/config — text.
- Status/category/role: varchar + іменований CHECK з переліченими значеннями.
  Python enum і Pydantic повторюють домен; зміна набору потребує міграції.
- Вимірювання: numeric(14,4), кількості та sequence: integer. NULL означає
  «не виміряно», нуль — справжнє значення. Заборонені NaN/Infinity.
- JSONB default `{}`, NOT NULL, CHECK jsonb_typeof(column)='object'.
  Schemas для відомих типів валідують поля та одиниці; додаткові метадані
  залишаються розширюваними. Array властивості всередині object дозволені.
- Усі FK індексуються, якщо не покриті першим полем composite index/unique.
- Business records за замовчуванням ON DELETE RESTRICT. Користувачів
  деактивуємо; компоненти/сетапи з історією не видаляємо. CASCADE дозволений
  для member/link rows і measurements при дозволеному видаленні draft owner.

## Поля

`?` = nullable. Поля без `?` обов'язкові, якщо не вказано default.

| Таблиця | Поля крім id |
|---|---|
| users | username, full_name, nullable email, password_hash, legacy role, is_active=true, timestamps |
| roles | code, name, is_active=true |
| user_roles | user_id FK users, role_id FK roles, nullable assigned_by_id FK users, assigned_at |
| auth_sessions | user_id FK users ON DELETE CASCADE, expires_at timestamptz; id є jti підписаного JWT |
| projects | name, description='', goal='', start_date?, deadline?, status=PLANNED, responsible_user_id FK users, timestamps |
| rd_branches | project_id FK projects, parent_id? self FK, name, purpose='', status=OPEN, responsible_user_id FK users, change_summary='', result_summary='', created_by_id FK users, closed_at?, timestamps |
| branch_configurations | branch_id FK rd_branches, setup_id FK setups, role BASELINE/CANDIDATE, created_by_id FK users, created_at |
| rnd_promotion_requests | branch_id FK rd_branches, candidate_setup_id FK setups, status, reason, requester/reviewer fields and timestamps |
| project_members | project_id FK projects, user_id FK users, created_at |
| project_setups | project_id FK projects, setup_id FK setups, created_at |
| tasks | title, description='', project_id FK projects, branch_id? FK rd_branches, assignee_id? FK users, created_by_id FK users, status=TODO, priority=NORMAL, deadline? timestamptz, result='', completed_at? timestamptz, timestamps |
| setups | name, drone_class, version, status=DEVELOPMENT, description='', legacy drone fields, attributes JSONB, notes='', timestamps |
| components | category, manufacturer='', model='', name, description='', specifications JSONB, datasheet_url? text, notes='', timestamps |
| setup_components | setup_id FK setups, component_id FK components, quantity integer, position='' varchar(100), notes='', timestamps |
| firmware_revisions | setup_id FK setups, version_name, firmware_type, firmware_version, description='', config_text='', created_at, created_by_id FK users |
| tests | name, test_type, project_id? FK projects, branch_id? FK rd_branches, setup_id? FK setups, component_id? FK components, firmware_revision_id? FK firmware_revisions, performed_by_id? FK users, test_date? timestamptz, status=PLANNED, description='', conditions JSONB, result_summary JSONB, conclusion='', timestamps |
| test_components | test_id FK tests, component_id FK components, role, notes='', created_at |
| test_measurements | test_id FK tests, sequence integer, throttle_percent?, voltage_v?, current_a?, power_w?, rpm?, thrust_kg?, efficiency_g_w?, motor_temperature_c?, esc_temperature_c?, timestamp_seconds?, timestamps |
| attachments | file metadata, uploaded_by FK users, created_at та рівно один owner: project_id?, branch_id?, task_id?, setup_id?, component_id?, test_id?, firmware_revision_id? |
| comments | author_id FK users, text, timestamps та рівно один owner: project_id?, branch_id?, task_id?, setup_id?, test_id? |

`completed_at` потрібний для «completed recently», бо updated_at змінюється і
після завершення. `performed_by_id/test_date` дозволено NULL лише для PLANNED;
під час виконання operator/date стають обов'язковими. ProjectMember має
включати assignee перед призначенням йому задачі. Responsible user має доступ
до проєкту незалежно від додаткового membership row.

## Значення

| Поле | Дозволені значення |
|---|---|
| users.role | ADMIN, MANAGER, ENGINEER, EMPLOYEE (тимчасове compatibility field) |
| roles.code | ADMINISTRATOR, ENGINEER, RND_ENGINEER, PRODUCTION_MANAGER, PROCUREMENT_SPECIALIST, ASSEMBLER, ELECTRONICS_TECHNICIAN, FIRMWARE_ENGINEER, TEST_PILOT, TEST_ENGINEER, QUALITY_CONTROLLER |
| projects.status | PLANNED, IN_PROGRESS, TESTING, COMPLETED, FROZEN |
| rd_branches.status | OPEN, IN_REVIEW, APPROVED, REJECTED, CLOSED |
| branch_configurations.role | BASELINE, CANDIDATE |
| rnd_promotion_requests.status | REQUESTED, APPROVED, REJECTED |
| tasks.status | TODO, IN_PROGRESS, BLOCKED, TESTING, DONE |
| tasks.priority | LOW, NORMAL, HIGH, CRITICAL |
| setups.status | DEVELOPMENT, TESTING, READY, DEPRECATED |
| components.category | MOTOR, ESC, FLIGHT_CONTROLLER, PROPELLER, BATTERY, CAMERA, VTX, RX, GPS, ANTENNA, FRAME, POWER_MODULE, OTHER |
| tests.status | PLANNED, IN_PROGRESS, PASS, FAIL, PARTIAL |
| tests.test_type | MOTOR_BENCH, ESC_BENCH, BATTERY, PROPELLER, FLIGHT, ENDURANCE, RANGE, TEMPERATURE, FRAME, ANTENNA, OTHER |
| test_components.role | ESC, PROPELLER, BATTERY, OTHER |

Kanban показує BLOCKED явно (окрема смуга або видимий filter), щоб заблоковані
задачі не зникали між чотирма основними колонками.

## Uniqueness та перевірки

- users: unique indexes lower(username) та lower(email); username обов’язковий,
  нормалізований і використовується для входу, email — необов’язковий контакт.
- user_roles: UNIQUE(user_id, role_id); ролі призначаються окремо від власності
  записів і майбутнього призначення виробничої операції.
- project_members: UNIQUE(project_id,user_id).
- rd_branches: UNIQUE(project_id,name); parent and branch belong to the same project.
- branch_configurations: UNIQUE(branch_id,setup_id), partial UNIQUE baseline per branch.
- tasks/tests: composite FK `(project_id,branch_id)` prevents cross-project branch links.
- project_setups: UNIQUE(project_id,setup_id).
- setups: UNIQUE(name,version); version визначає конфігурацію BOM.
- setup_components: UNIQUE(setup_id,component_id,position), quantity > 0.
  position NOT NULL default '' дозволяє PostgreSQL уникнути дублів через NULL.
- firmware_revisions: UNIQUE(setup_id,version_name), UNIQUE(setup_id,id).
- tests: composite FK (setup_id,firmware_revision_id) ->
  firmware_revisions(setup_id,id); CHECK firmware_revision_id IS NULL OR
  setup_id IS NOT NULL. Це не дозволяє прив'язати чужу ревізію.
- tests: CHECK test_type NOT IN ('FLIGHT','ENDURANCE') OR setup_id IS NOT NULL;
  CHECK test_type != 'MOTOR_BENCH' OR component_id IS NOT NULL.
- tests: CHECK status='PLANNED' OR (performed_by_id IS NOT NULL AND test_date
  IS NOT NULL). Тип головного компонента MOTOR/ESC перевіряє сервіс у транзакції.
- Якщо test має project і setup, пара має бути в ProjectSetup; composite FK
  (project_id,setup_id) -> project_setups(project_id,setup_id) (NULL дозволені).
- test_components: UNIQUE(test_id,component_id,role). Категорія має відповідати
  role, крім OTHER; перевірка сервісу.
- test_measurements: UNIQUE(test_id,sequence), sequence >= 0;
  throttle_percent BETWEEN 0 AND 100. voltage/current/power/rpm/thrust/
  efficiency/time >= 0, температури можуть бути від'ємними.
- setup числові характеристики >= 0; max_current_a >= average_current_a,
  коли обидва задані. attachments.size >= 0; UNIQUE(storage_path).
- attachments: CHECK num_nonnulls(project_id,task_id,setup_id,component_id,
  test_id,firmware_revision_id)=1. comments: аналогічний CHECK для чотирьох FK.
- tasks: DONE iff completed_at IS NOT NULL; сервіс проставляє/очищає timestamp.
- comments.text, names/titles не можуть бути порожні після trim (Pydantic + CHECK).

## Індекси та історія

Додаткові btree: projects(status), tasks(assignee_id,status,deadline),
tasks(project_id,status), tasks(priority), tasks(completed_at), setups(status),
components(category), components(manufacturer,model), tests(test_type,test_date),
tests(status,test_date), tests(setup_id,test_date), tests(component_id,test_date).
Сортування стабільне: другий ключ id. JSONB GIN/trigram — лише якщо виміряні
запити обґрунтовують їх. Тести не копіюються у Component.specifications.

FirmwareRevision є append-only: API не має update/delete;
business FK RESTRICT зберігають посилання. BOM конфігурації, що має тести,
незмінний: сервіс створює новий Setup/version при копіюванні. Ці правила
перевіряються сервісом і PostgreSQL integration tests. Історія активності першої
версії формується з timestamps задач/тестів/коментарів; повний audit log —
окреме майбутнє рішення, не прихована властивість updated_at.

## Phase 3 product definition

Migration 0009_phase3_products adds shared units of measure, product categories, products,
immutable released product revisions, revision BOM and approved alternatives, reusable firmware
artifacts/releases and exact requirements, extensible technology-card blocks/checklists, and
acyclic production-route definitions. Attachment ownership now supports products, product
revisions and firmware releases with one-owner enforcement.

Component.default_uom_id is required. The migration seeds PCS, KG, M and L, backfills existing
components with PCS, then makes the foreign key non-null. Released revision content is changed
only by cloning a new draft.

Migration `0012_product_variants` додає постійні комплектації каталогу між
`products` і `product_revisions`. Для кожної наявної моделі створюється
«Стандартна» комплектація; UUID версій, продуктів і посилання старих замовлень
не змінюються. Composite FK `(product_id, variant_id)` не дозволяє прив'язати
версію до комплектації іншої моделі. Кожна комплектація має власну чинну
затверджену версію, а `Product.current_revision_id` тимчасово лишається для
сумісності старих клієнтів.

## Phase 4 orders and procurement

Migration `0010_phase4_orders` adds `customers`, `orders`, `order_items`,
`order_variants`, `variant_deviations`, `deviation_tests`, `material_requirements`,
`suppliers`, `procurement_records` and `procurement_allocations`.

An order item stores both product and its released revision. Its variants form a quantity
partition checked by the service before release. `VariantDeviation` references the original BOM
row and replacement component, so the released BOM is never edited. Releasing variants computes
`MaterialRequirement` snapshots from the original BOM plus approved deviations. Procurement
allocations must match the requirement component and cannot exceed the procurement record amount.

Order status transitions are explicit. A DRAFT can be confirmed only after it has at least one
item and every active variant is RELEASED. Material quantities are calculated by the backend;
clients cannot submit requirement or missing values.

Migration `0013_order_draft_version` adds a positive `orders.draft_version` with a compatible
default for existing rows. Every composition or deviation change increments it. Confirmation
compares the client's expected value under a row lock and rejects stale drafts.

## Phase 5 production execution

Migration `0011_phase5_execution` adds `production_items`, `stage_executions`,
`stage_events` and `stage_checklist_results`. Attachments gain an optional
`stage_execution_id` owner while retaining the exactly-one-owner constraint.

SERIAL production items always have quantity one. BATCH and QUANTITY items carry a positive group
quantity. Each item references the released variant and selected revision route. Stage executions
store planned/completed/failed quantities and audited worker timestamps; aggregate order progress
is queried from these rows rather than stored on orders. `StageEvent.idempotency_key` prevents a
retried completion request from incrementing progress twice. Checklist results copy the template
text and requirement flags so later template changes cannot rewrite production history.
