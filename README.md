# BAZA

Внутрішній робочий простір інженерної команди: проєкти, задачі, конфігурації,
компоненти та випробування. Modular monolith: FastAPI + PostgreSQL + React.

**Стан за product roadmap: Phase 2.** Працюють вхід/вихід, користувачі й ролі, проєкти з
учасниками, задачі з виконавцями, строками та результатами, My/All Tasks,
фільтри, таблиця/Kanban, каталог компонентів, версійні сетапи з BOM,
прив'язки сетапів до проєктів, ревізії прошивки, універсальні випробування,
вимірювання та графіки, R&D гілки, порівняння конфігурацій, promotion requests,
файли, коментарі, глобальний пошук і реальний dashboard.
Development seed запускається лише явною CLI-командою, див. [roadmap](docs/ROADMAP.md).
Це локальна development версія; production deployment ще не налаштований.

- [Архітектура та ER](ARCHITECTURE.md)
- [Поля, обмеження та зв'язки БД](docs/DATABASE.md)
- [Залежності та їх призначення](docs/DEPENDENCIES.md)
- [Результати перевірок](docs/VERIFICATION.md)
- [Backup, restore та development seed](docs/OPERATIONS.md)
- [Правила подальшої роботи](AGENTS.md)

## Docker Compose

Потрібні Docker Engine/Desktop з Linux containers і Docker Compose v2+.
Команди виконуються з кореня проєкту. У PowerShell:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Відкрийте `.env` і встановіть власний `POSTGRES_PASSWORD` (не порожній), а також
`JWT_SECRET` — випадковий секрет щонайменше з 32 символів. Якщо локальне
Python-середовище вже встановлене, `python scripts/configure_dev.py` створить
відсутній JWT_SECRET, не показуючи його і не змінюючи наявний. Інакше отримайте
випадкове значення через `python -c "import secrets; print(secrets.token_urlsafe(48))"`
і збережіть його локально у `.env`.
Не публікуйте цей файл. Пароль передається в backend окремим параметром,
тому спеціальні символи не ламають URL; у Compose `.env` для literal `$`
використовуйте одинарні лапки навколо значення.

```powershell
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

- UI: http://localhost:8080
- API docs у development: http://localhost:8000/api/docs
- Liveness: http://localhost:8000/api/health/live
- Readiness: http://localhost:8000/api/health/ready

Після першого запуску створіть адміністратора (підставте ім’я та логін):

```powershell
docker compose exec backend python -m app.cli create-admin --name "Your Name" --username "your-login" --email "you@example.com"
```

Команда приховано попросить пароль двічі, мінімум 12 символів. Вбудованих
облікових записів і стандартного пароля немає. Bootstrap дозволений лише
до появи першого користувача; наступних додає ADMIN через Users.
Для локального backend та сама команда: `python -m app.cli create-admin`. Email
необов’язковий; для входу використовуйте username і пароль.

Користувач може мати кілька професійних ролей. Backend обчислює доступ через
capabilities; ADMINISTRATOR керує користувачами, PRODUCTION_MANAGER — поточним
контуром проєктів і задач, ENGINEER/RND_ENGINEER — інженерними записами.
Користувач без привілейованої ролі бачить свої проєкти та призначені задачі й
змінює лише їх статус/результат. Виконавець має бути
учасником проєкту. Видалення потребує підтвердження; проєкт із задачами
видалити не можна. Сесія триває 60 хвилин; зміна ролі, вимкнення користувача
або скидання пароля відкликають його сесії.

ADMIN, MANAGER та ENGINEER працюють із каталогом компонентів, сетапами, BOM і
ревізіями прошивки. Один компонент і один сетап повторно використовуються у
різних конфігураціях/проєктах через зв'язки, без копіювання записів. Прив'язки
сетапів до проєктів змінюють ADMIN/MANAGER. EMPLOYEE не має доступу до цього
інженерного контуру. Після першого випробування фізичні параметри й BOM сетапу
блокуються; для змін UI створює нову версію. FirmwareRevision і виконані тести
зберігають історію. Файли перевіряються за owner access на кожному запиті;
binary data лежать у storage volume, а не в PostgreSQL.

Compose чекає готовності PostgreSQL, backend застосовує міграції перед
запуском API. Nginx віддає React і проксіює `/api` до backend. Volumes
`postgres_data` і `file_storage` переживають перезапуск. Порти прив'язані до
127.0.0.1. `docker compose down` зупиняє stack зі збереженням даних;
не додавайте `--volumes`, якщо хочете їх зберегти.

Діагностика: `docker compose logs backend`, `docker compose logs db`.
Readiness 503 означає недоступну БД або незастосовані/застарілі міграції.
Liveness 200 сам по собі не означає, що БД працює.

## Локальна розробка

Потрібні Python 3.14, Node.js 22.12+ і PostgreSQL 17. PostgreSQL можна
запустити окремо через `docker compose up -d db`; для тестування всього stack
використовуйте повний Compose запуск вище.

Backend (корінь проєкту):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e ./backend
.\.venv\Scripts\python.exe scripts/configure_dev.py
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1
```

Backend читає кореневий `.env` незалежно від cwd. Можна задати `DATABASE_URL`
замість окремих параметрів: `postgresql+psycopg://...`; пароль у URL слід
percent-encode. Не використовуйте SQLite для обходу PostgreSQL перевірок.

Frontend (інший термінал, папка `frontend`):

```powershell
npm ci
npm run dev
```

UI: http://localhost:5173. Vite проксіює `/api` на `127.0.0.1:8000`.
Жодна backend secret variable не передається в Vite.

На Linux/macOS відповідник Python-команди — `.venv/bin/python`.
Portable tooling у `.tools`, якщо наявне, локальне й не входить до репозиторію;
для звичайного запуску використовуйте встановлені Python/Node/Docker.

## Міграції

У папці backend після імпорту нових module models в `app/migrations/env.py`:

```powershell
..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "add users"
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic current
```

Завжди переглядайте згенеровану міграцію, зокрема CHECK/unique/FK/indexes.
Міграції не замінюються `create_all`. `0001_foundation` — початковий marker;
`0002_auth_users` створює users/auth_sessions; `0003_projects_tasks` —
projects/project_members/tasks; `0004_components_setups_firmware` — components,
setups, setup_components, project_setups і firmware_revisions; `0005_tests` —
tests/test_components/test_measurements; `0006_files_comments` — attachments і
comments; `0007_identity_roles_username` — username, optional email, roles і
user_roles з deterministic backfill; `0008_rnd_evolution` — поля проєкту,
R&D branches, branch configuration links, promotion requests, generic setup
attributes і branch ownership для задач/тестів/файлів/коментарів. Переглянуто
UUID/FK/CHECK/indexes та порядок rollback; PostgreSQL тести перевіряють
upgrade/downgrade й відповідність ORM.
Для rollback лише на disposable dev DB: `alembic downgrade -1`.

## Перевірки

Backend, з папки backend:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m ruff format --check .
..\.venv\Scripts\python.exe -m build --no-isolation
```

Повний backend suite потребує **окремої disposable БД**: тести виконують
upgrade/downgrade. З кореня проєкту рекомендовано:

```powershell
.\.venv\Scripts\python.exe scripts/test_backend.py
```

Скрипт використовує підключення з `.env`, створює випадкову тестову БД і
прибирає її після перевірки. PostgreSQL user має мати CREATEDB (у локальному
Compose він доступний). Альтернатива — вручну створити окрему `baza_test`:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/baza_test'
..\.venv\Scripts\python.exe -m pytest -m integration -q
```

Без TEST_DATABASE_URL інтеграційні тести пропускаються. Unit tests
перевіряють API-контракт, error handling, CORS, конфігурацію й revision mismatch;
вони не доводять успішного запуску справжньої PostgreSQL.

Frontend, з папки frontend:

```powershell
npm test
npm run lint
npm run build
```

Vitest/Testing Library перевіряють навігацію, 404, readiness, помилку та retry,
захищені маршрути, помилку входу, інженерні ролі та відображення характеристик.
Network responses замінюються лише всередині unit tests, ніколи в продукті.

Після `npm run build`, із кореня проєкту:

```powershell
.\.venv\Scripts\python.exe scripts/run_e2e.py
```

Потрібен встановлений Google Chrome, вільні порти 8011/4173 та доступ до
PostgreSQL. Playwright перевіряє критичний workflow від входу й проєкту через
компонент, сетап/BOM, тест і вимірювання до файлу, коментаря, пошуку та виходу.
Використовуються тимчасова БД і випадковий тестовий пароль; головний застосунок
не отримує тестових записів. Desktop/mobile screenshots — у
`frontend/test-results`, backend log — `.tools/e2e-backend.log`. Тимчасова БД
і storage directory прибираються після сценарію.

При зміні Python залежностей встановіть `backend[dev]` у чисте venv,
перевірте тести, виконайте `python scripts/lock_backend.py` з кореня та
перегляньте lockfile diff. Frontend lock оновлюється `npm install`.
#   b a z a s - w o r k s  
 