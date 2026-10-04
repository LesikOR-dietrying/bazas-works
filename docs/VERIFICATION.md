# Р РµР·СѓР»СЊС‚Р°С‚Рё РїРµСЂРµРІС–СЂРѕРє

## Product roadmap Phase 2 вЂ” 2026-10-02

- Additive migration `0008_rnd_evolution` and offline PostgreSQL SQL generation: **PASS**.
- Backend Ruff/format, import/compile checks and sdist/wheel build: **PASS**. Local pytest:
  **12 passed, 34 skipped**; PostgreSQL integration cases, including the new
  R&D branch/comparison/promotion flow, were skipped because Docker/PostgreSQL
  is unavailable while virtualization is disabled.
- Frontend ESLint and strict TypeScript/Vite production build: **PASS**.
  Build retains informational Rollup warnings about Zod comments, shared
  TestsPage loading and the main chunk size.
- `docker compose config --quiet`: **PASS** (Docker CLI warned that the user-level
  config file is inaccessible, but the project configuration validated).
- Compose runtime, migration round trip and browser E2E remain unavailable on
  this machine until virtualization and Docker Engine are enabled.

## PHASE 5вЂ“7 вЂ” 2026-09-30

- `python scripts/test_backend.py`: **43 passed, 0 skipped** РЅР° РѕРєСЂРµРјС–Р№
  PostgreSQL 17 Р±Р°Р·С– Р·Р° 37,57 СЃ. Suite РїРµСЂРµРІС–СЂСЏС” РјС–РіСЂР°С†С–С— РґРѕ `0006`, universal
  motor/flight tests, equipment С– measurements, РЅРµР·РјС–РЅРЅС–СЃС‚СЊ BOM, upload/
  download С‚Р° owner authorization, comments, search isolation, dashboard С–
  development-only idempotent seed. Test runner РІРёРєРѕСЂРёСЃС‚РѕРІСѓС” РІР»Р°СЃРЅРёР№ temp
  РєР°С‚Р°Р»РѕРі Сѓ `.tools` С‚Р° РІРёРґР°Р»СЏС” С‚РµСЃС‚РѕРІСѓ Р‘Р” РїС–СЃР»СЏ Р·Р°РїСѓСЃРєСѓ.
- Ruff lint/format: **PASS** РґР»СЏ 103 Python files; `pip check`: **PASS**;
  Python sdist/wheel: **PASS**, РѕР±РёРґРІС– РЅРѕРІС– РјС–РіСЂР°С†С–С— С‚Р° РјРѕРґСѓР»С– РІРєР»СЋС‡РµРЅС–.
  Р„ РѕРґРЅРµ upstream РїРѕРїРµСЂРµРґР¶РµРЅРЅСЏ Starlette РїСЂРѕ РјР°Р№Р±СѓС‚РЅСЋ Р·Р°РјС–РЅСѓ TestClient/httpx.
- Vitest: **12 passed**; ESLint С– strict TypeScript/Vite production build:
  **PASS**. Recharts detail Р·Р°РІР°РЅС‚Р°Р¶СѓС”С‚СЊСЃСЏ РѕРєСЂРµРјРёРј lazy chunk. Rollup Р·Р°Р»РёС€Р°С”
  С–РЅС„РѕСЂРјР°С†С–Р№РЅС– РїРѕРїРµСЂРµРґР¶РµРЅРЅСЏ РїСЂРѕ РєРѕРјРµРЅС‚Р°СЂС– Zod С– main chunk 548,21 kB.
- Playwright + Chrome + СЂРµР°Р»СЊРЅРёР№ API/PostgreSQL: **1 passed** Р·Р° 12,2 СЃ
  (15,0 СЃ СЂР°Р·РѕРј С–Р· Р·Р°РїСѓСЃРєРѕРј). Р’С…С–Рґ в†’ project в†’ MOTOR в†’ setup/BOM/firmware в†’
  motor test в†’ measurement/charts в†’ file в†’ comment в†’ global search в†’ task/
  result/Kanban в†’ mobile в†’ logout. РўРёРјС‡Р°СЃРѕРІС– `baza_e2e_*` Р‘Р” С– storage РІРёРґР°Р»РµРЅРѕ.
- Docker Compose config С– `up --build -d --wait`: **PASS**. `db`, `backend` С–
  `frontend` РјР°СЋС‚СЊ status `healthy`; backend РїРѕРєР°Р·СѓС”
  `0006_files_comments (head)`. Host readiness/UI: **200/200** РЅР° РїРѕСЂС‚Р°С…
  8000/8080. `npm ci` РїРѕРІС–РґРѕРјР»СЏС” РїСЂРѕ 2 moderate dev-only advisory Сѓ test tools;
  С—С… РІРёРїСЂР°РІР»РµРЅРЅСЏ РїРѕС‚СЂРµР±СѓС” major РѕРЅРѕРІР»РµРЅРЅСЏ Vitest С– РЅРµ РІС…РѕРґРёС‚СЊ Сѓ runtime image.

## PHASE 4 вЂ” 2026-09-30

- `python scripts/test_backend.py`: **36 passed, 0 skipped** РЅР° РѕРєСЂРµРјС–Р№
  PostgreSQL 17 Р±Р°Р·С–. РџРµСЂРµРІС–СЂРµРЅРѕ РјС–РіСЂР°С†С–СЋ 0004 С‚Р° schema drift, CRUD С– СЂРѕР»С–,
  MOTOR/ESC specifications, BOM С–Р· РїРѕСЃРёР»Р°РЅРЅСЏРјРё РЅР° СЃРїС–Р»СЊРЅС– РєРѕРјРїРѕРЅРµРЅС‚Рё, clone,
  РІРёРєРѕСЂРёСЃС‚Р°РЅРЅСЏ СЃРµС‚Р°РїСѓ Сѓ РєС–Р»СЊРєРѕС… РїСЂРѕС”РєС‚Р°С…, firmware ownership/append-only,
  РєРѕРЅС„Р»С–РєС‚Рё FK/unique С– С„С–Р»СЊС‚СЂРё Р·Р° РїСЂРѕС”РєС‚РѕРј/РєРѕРјРїРѕРЅРµРЅС‚РѕРј.
- Ruff: **PASS**. Vitest: **10 passed**; ESLint С– strict TypeScript/Vite
  production build: **PASS**. Vite build РјР°С” С–РЅС„РѕСЂРјР°С†С–Р№РЅРµ РїРѕРїРµСЂРµРґР¶РµРЅРЅСЏ РїСЂРѕ
  РѕСЃРЅРѕРІРЅРёР№ chunk 537.03 kB С‚Р° РєРѕРјРµРЅС‚Р°СЂС– `@__PURE__` СѓСЃРµСЂРµРґРёРЅС– Zod.
- Playwright + Chrome + СЂРµР°Р»СЊРЅРёР№ API/PostgreSQL: **1 passed** Р·Р° 5,6 СЃ.
  Р’С…С–Рґ в†’ РїСЂРѕС”РєС‚ в†’ MOTOR в†’ СЃРµС‚Р°Рї в†’ BOM в†’ СЃРїРёСЃРѕРє РІРёРєРѕСЂРёСЃС‚Р°РЅРЅСЏ РєРѕРјРїРѕРЅРµРЅС‚Р° в†’
  firmware revision в†’ РїСЂРёРІ'СЏР·РєР° СЃРµС‚Р°РїСѓ РґРѕ РїСЂРѕС”РєС‚Сѓ в†’ Р·Р°РґР°С‡Р°/result/Kanban в†’
  mobile в†’ logout. РЎРєСЂРёРїС‚ СЃС‚РІРѕСЂРёРІ С– РІРёРґР°Р»РёРІ РІРёРїР°РґРєРѕРІСѓ `baza_e2e_*` Р±Р°Р·Сѓ.
- Desktop firmware/BOM С– mobile project screenshots РїРµСЂРµРіР»СЏРЅСѓС‚Рѕ. Destructive
  actions РјР°СЋС‚СЊ РїС–РґС‚РІРµСЂРґР¶РµРЅРЅСЏ; EMPLOYEE РЅРµ Р±Р°С‡РёС‚СЊ engineering navigation,
  Р° backend РїРѕРІРµСЂС‚Р°С” 403 РґР»СЏ РїСЂСЏРјРёС… engineering-Р·Р°РїРёС‚С–РІ.
- РџРѕРІРЅРµ Р±Р»РѕРєСѓРІР°РЅРЅСЏ Р·РјС–РЅРё BOM РїС–СЃР»СЏ РїРѕСЏРІРё РІРёРїСЂРѕР±СѓРІР°РЅРЅСЏ РЅР°РІРјРёСЃРЅРѕ РЅР°Р»РµР¶РёС‚СЊ PHASE 5:
  РґРѕ СЃС‚РІРѕСЂРµРЅРЅСЏ С‚Р°Р±Р»РёС†С– tests РЅРµРјР°С” РїСЂР°РІРґРёРІРѕРіРѕ Р·РІ'СЏР·РєСѓ, СЏРєРёР№ РјРѕР¶РЅР° РїРµСЂРµРІС–СЂРёС‚Рё.

- Ruff format: **69 files formatted**; `pip check`: **PASS**; Python sdist/wheel:
  **PASS**, РјС–РіСЂР°С†С–СЏ 0004 С‚Р° С‚СЂРё РЅРѕРІС– РјРѕРґСѓР»С– РІРєР»СЋС‡РµРЅС– РґРѕ РїР°РєРµС‚Р°.
- Docker Compose config С– `up --build -d --wait`: **PASS**. PostgreSQL, backend
  С– frontend РјР°СЋС‚СЊ status `healthy`; РєРѕРЅС‚РµР№РЅРµСЂ backend РїРѕРєР°Р·СѓС”
  `0004_components_setups_firmware (head)`. Host HTTP readiness С– UI: **200/200**
  РЅР° `127.0.0.1:8000` С‚Р° `127.0.0.1:8080`.

## PHASE 3 вЂ” 2026-09-30

- `python scripts/test_backend.py`: **33 passed, 0 skipped**, СЂРµР°Р»СЊРЅРёР№ PostgreSQL 17.
  РџРµСЂРµРІС–СЂРµРЅРѕ РјС–РіСЂР°С†С–С— upgrade/downgrade, Alembic schema drift, CRUD,
  СѓС‡Р°СЃРЅРёРєС–РІ/РїСЂРёР·РЅР°С‡РµРЅРЅСЏ, РѕР±РјРµР¶РµРЅРЅСЏ ENGINEER/EMPLOYEE, С–Р·РѕР»СЏС†С–СЋ СЃРїРёСЃРєС–РІ С– detail,
  С„С–Р»СЊС‚СЂРё, СЃРѕСЂС‚СѓРІР°РЅРЅСЏ, РїР°РіС–РЅР°С†С–СЋ, РїСЂРѕСЃС‚СЂРѕС‡РµРЅС–/Р·Р°Р±Р»РѕРєРѕРІР°РЅС– Р·Р°РґР°С‡С–, summary,
  completed_at С‚Р° Р·Р°Р±РѕСЂРѕРЅСѓ РІРёРґР°Р»РµРЅРЅСЏ РїСЂРѕС”РєС‚Сѓ С–Р· Р·Р°РґР°С‡Р°РјРё.
- Ruff lint/format: **PASS**, 57 Python files; `pip check`: **PASS**;
  Python sdist/wheel build: **PASS**, СѓСЃС– С‚СЂРё РјС–РіСЂР°С†С–С— РІРєР»СЋС‡РµРЅРѕ.
- Vitest: **9 passed**; ESLint, strict TypeScript/Vite production build: **PASS**.
  РџРµСЂРµРІС–СЂРµРЅРѕ РїРµСЂРµС…РѕРґРё РЅР° login РїС–СЃР»СЏ logout С– СЃРµСЂРІРµСЂРЅРѕС— РІС–РґРјРѕРІРё СЃРµСЃС–С—.
- Playwright + installed Chrome + СЂРµР°Р»СЊРЅРёР№ API/PostgreSQL: **1 passed**.
  Р’С…С–Рґ в†’ РїСЂРѕС”РєС‚ в†’ Р·Р°РґР°С‡Р° Р· РІРёРєРѕРЅР°РІС†РµРј в†’ Р·Р±РµСЂРµР¶РµРЅРЅСЏ СЂРµР·СѓР»СЊС‚Р°С‚Сѓ С‚Р° reload в†’
  BLOCKED/DONE Сѓ Kanban в†’ СЃРєР°СЃСѓРІР°РЅРЅСЏ РїС–РґС‚РІРµСЂРґР¶РµРЅРЅСЏ РІРёРґР°Р»РµРЅРЅСЏ в†’ mobile в†’ logout.
  Р’РёСЏРІР»РµРЅСѓ Р·Р°С‚СЂРёРјРєСѓ РїРµСЂРµС…РѕРґСѓ РїС–СЃР»СЏ logout РІРёРїСЂР°РІР»РµРЅРѕ: auth query Р·Р±РµСЂС–РіР°С”
  observers, С‚РѕРґС– СЏРє РєРµС€ Р±С–Р·РЅРµСЃ-РґР°РЅРёС… РѕС‡РёС‰СѓС”С‚СЊСЃСЏ РїСЂРё Р·РјС–РЅС– СЃРµСЃС–С—.
- Desktop (1440Г—1000) С‚Р° mobile (390Г—844) screenshots РѕРіР»СЏРЅСѓС‚Рѕ.
  РЎРєСЂРёРїС‚ E2E СЃС‚РІРѕСЂСЋС” Р№ РІРёРґР°Р»СЏС” Р»РёС€Рµ РІРёРїР°РґРєРѕРІСѓ `baza_e2e_*` Р±Р°Р·Сѓ.
- РќР°СЏРІРЅС– dependency warnings (Starlette/httpx, Zod PURE comments, ESLint 9)
  РЅРµ РїРµСЂРµС€РєРѕРґР¶Р°СЋС‚СЊ С‚РµСЃС‚Р°Рј С– Р·Р±С–СЂРєР°Рј. Production hardening С– РїРѕРІРЅРёР№ E2E
  РєРѕРЅС„С–РіСѓСЂР°С†С–С—/РІРёРїСЂРѕР±СѓРІР°РЅРЅСЏ Р·Р°Р»РёС€Р°СЋС‚СЊСЃСЏ PHASE 7.

Docker Compose `config --quiet` РїСЂРѕР№С€РѕРІ. `docker compose up --build -d --wait`
Р·С–Р±СЂР°РІ backend/frontend С– РїРѕРІС–РґРѕРјРёРІ `Healthy` РґР»СЏ db, backend С‚Р° frontend.
РџС–СЃР»СЏ Р·Р°РїСѓСЃРєСѓ HTTP РїРµСЂРµРІС–СЂРєРё Р· С…РѕСЃС‚Р° РґР°Р»Рё `200` РґР»СЏ
`http://127.0.0.1:8000/api/health/ready` С– `http://127.0.0.1:8080/`.
Р”РѕРґР°С‚РєРѕРІР° РєРѕРјР°РЅРґР° `docker compose ps` РЅРµ РїСЂРѕР№С€Р»Р° sandbox РґРѕСЃС‚СѓРї РґРѕ Docker pipe;
РµСЃРєР°Р»Р°С†С–СЋ Р°РІС‚РѕРјР°С‚РёС‡РЅР° РїРµСЂРµРІС–СЂРєР° РІС–РґС…РёР»РёР»Р° С‡РµСЂРµР· Р»С–РјС–С‚ РІРёРєРѕСЂРёСЃС‚Р°РЅРЅСЏ.
Р¦Рµ РЅРµ РІРїР»РёРІР°С” РЅР° РІР¶Рµ РѕС‚СЂРёРјР°РЅС– healthchecks С‚Р° HTTP РІС–РґРїРѕРІС–РґС–.

`npm audit` РїРѕРІС–РґРѕРјР»СЏС” РїСЂРѕ РґРІР° moderate РїРѕРІС–РґРѕРјР»РµРЅРЅСЏ С‰РѕРґРѕ Vitest/@vitest/mocker
Сѓ Р·Р°Р»РµР¶РЅРѕСЃС‚СЏС… РґР»СЏ С‚РµСЃС‚СѓРІР°РЅРЅСЏ. Р’РѕРЅРё РЅРµ РІС…РѕРґСЏС‚СЊ РґРѕ runtime Nginx РѕР±СЂР°Р·Сѓ;
РІРёРїСЂР°РІР»РµРЅРЅСЏ РїРѕС‚СЂРµР±СѓС” РѕРєСЂРµРјРѕРіРѕ РѕРЅРѕРІР»РµРЅРЅСЏ Vitest major С– РїРµСЂРµРІС–СЂРєРё СЃСѓРјС–СЃРЅРѕСЃС‚С–.

## РћРЅРѕРІР»РµРЅРЅСЏ PHASE 2 вЂ” 2026-09-30

- PostgreSQL 17 С– Docker Engine С‚РµРїРµСЂ РґРѕСЃС‚СѓРїРЅС–.
- `python scripts/test_backend.py`: 25 passed, Р¶РѕРґРЅРѕРіРѕ skipped. РЎРєСЂРёРїС‚ СЃС‚РІРѕСЂСЋС”
  РѕРєСЂРµРјСѓ С‚РёРјС‡Р°СЃРѕРІСѓ Р‘Р” С– РїСЂРёР±РёСЂР°С” С—С— РїС–СЃР»СЏ С‚РµСЃС‚С–РІ; РґР°РЅС– Р·Р°СЃС‚РѕСЃСѓРЅРєСѓ РЅРµ Р·РјС–РЅСЋСЋС‚СЊСЃСЏ.
- Frontend: 7 passed; ESLint С– strict TypeScript/Vite build СѓСЃРїС–С€РЅС–.
- Backend: Ruff С– Python wheel/sdist build СѓСЃРїС–С€РЅС–; Compose config РІР°Р»С–РґРЅРёР№.
- РџРµСЂРµРІС–СЂРµРЅРѕ logout revocation, CSRF/origin, expired/tampered/wrong-audience
  tokens, disabled accounts, СЂРѕР»СЊ EMPLOYEE, РѕСЃС‚Р°РЅРЅСЊРѕРіРѕ ADMIN, password reset,
  email uniqueness, filters С– login throttle.
- Р—Р°СЃС‚РµСЂРµР¶РµРЅРЅСЏ РїСЂРѕ httpx/Starlette Р·Р°Р»РёС€Р°С”С‚СЊСЃСЏ. Vite С‚Р°РєРѕР¶ РїРѕРІС–РґРѕРјР»СЏС” РїСЂРѕ
  РєРѕРјРµРЅС‚Р°СЂС– `@__PURE__` Сѓ Р·Р°Р»РµР¶РЅРѕСЃС‚С– Zod; production build СѓСЃРїС–С€РЅРёР№.

РќРёР¶С‡Рµ Р·Р±РµСЂРµР¶РµРЅРёР№ С–СЃС‚РѕСЂРёС‡РЅРёР№ Р·РІС–С‚ PHASE 1.

Р”Р°С‚Р°: 2026-09-29. РЎРµСЂРµРґРѕРІРёС‰Рµ: Windows, Python 3.14.6, portable Node 22.22.0,
npm 10.9.4. Р—Р°Р»РµР¶РЅРѕСЃС‚С– Р·Р°С„С–РєСЃРѕРІР°РЅС– Сѓ Python lockfiles С‚Р° package-lock.json.

| РџРµСЂРµРІС–СЂРєР° | Р РµР·СѓР»СЊС‚Р°С‚ |
|---|---|
| Backend `pytest -q` | **12 passed, 1 skipped** |
| Backend Ruff lint + format check, РІРєР»СЋС‡РЅРѕ Р· lock script | **PASS**, 19 Python files |
| Backend `python -m build --no-isolation` | **PASS**, sdist + wheel; migrations РІРєР»СЋС‡РµРЅРѕ РґРѕ wheel |
| `pip check` | **PASS**, dependency conflicts РЅРµ РІРёСЏРІР»РµРЅРѕ |
| Alembic `upgrade head --sql` | **PASS**, PostgreSQL SQL РґР»СЏ baseline/version table |
| Frontend `npm test` | **PASS**, 5 Vitest/Testing Library tests |
| Frontend `npm run lint` | **PASS** |
| Frontend `npm run build` | **PASS**, strict TypeScript + Vite production assets |
| Docker Compose 5.5.1 `config --quiet` | **PASS**, С‚СЂРё СЃРµСЂРІС–СЃРё: db/backend/frontend |
| Desktop browser smoke check | **PASS**, production preview РІС–РґРєСЂРёС‚Рѕ Сѓ headless Chrome, layout РѕРіР»СЏРЅСѓС‚Рѕ |
| Mobile browser screenshot | **РќР• РџР†Р”РўР’Р•Р Р”Р–Р•РќРћ**, РґСЂСѓРіРёР№ headless Р·Р°РїСѓСЃРє РЅРµ Р·Р°РІРµСЂС€РёРІСЃСЏ; Р№РѕРіРѕ Р·СѓРїРёРЅРµРЅРѕ |
| Docker Engine/container build/start | **РќР• Р’РРљРћРќРђРќРћ**, Docker Engine РЅРµРґРѕСЃС‚СѓРїРЅРёР№ |
| PostgreSQL migration round trip/readiness | **SKIPPED**, TEST_DATABASE_URL РЅРµ Р·Р°РґР°РЅРёР№ С– Р»РѕРєР°Р»СЊРЅРѕРіРѕ PostgreSQL РЅРµРјР°С” |

Compose `ps` РїРѕРІРµСЂРЅСѓРІ: `open //./pipe/docker_engine: The system cannot find
the file specified`. Р’Р°Р»С–РґР°С†С–СЏ Compose РєРѕРЅС„С–РіСѓСЂР°С†С–С— **РЅРµ С”** РїРµСЂРµРІС–СЂРєРѕСЋ
РїРѕР±СѓРґРѕРІРё РѕР±СЂР°Р·С–РІ, Nginx СѓСЃРµСЂРµРґРёРЅС– РєРѕРЅС‚РµР№РЅРµСЂР° Р°Р±Рѕ РіРѕС‚РѕРІРЅРѕСЃС‚С– PostgreSQL.

Р”Р»СЏ Р·Р°РІРµСЂС€РµРЅРЅСЏ runtime РїРµСЂРµРІС–СЂРєРё РЅР° РјР°С€РёРЅС– Р· Docker:

```powershell
# РЎРїРµСЂС€Сѓ РЅР°Р»Р°С€С‚СѓРІР°С‚Рё .env Р·РіС–РґРЅРѕ Р· README.
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

РџС–СЃР»СЏ С†СЊРѕРіРѕ СЃС‚РІРѕСЂРёС‚Рё РѕРєСЂРµРјСѓ disposable test DB С– РІРёРєРѕРЅР°С‚Рё integration test
Р·Р° С–РЅСЃС‚СЂСѓРєС†С–С”СЋ README. РўРµСЃС‚ РїРµСЂРµРІС–СЂСЏС” upgrade в†’ readiness 200 в†’ downgrade в†’
readiness 503 в†’ upgrade в†’ readiness 200.

## Р©Рѕ РїРµСЂРµРІС–СЂСЏСЋС‚СЊ С‚РµСЃС‚Рё

Backend: liveness Р±РµР· РїСЂР°С†СЋСЋС‡РѕС— Р‘Р”, С‡РµСЃРЅРёР№ 503 РїСЂРё РЅРµРґРѕСЃС‚СѓРїРЅС–Р№ Р‘Р”,
РЅРµРѕРїСЂРёР»СЋРґРЅРµРЅРЅСЏ driver errors, revision mismatch, CORS allowlist, РѕР±РѕРІ'СЏР·РєРѕРІС–
credentials, РїР°СЂРѕР»СЊ Р·С– СЃРїРµС†С–Р°Р»СЊРЅРёРјРё СЃРёРјРІРѕР»Р°РјРё, PostgreSQL driver validation,
OpenAPI off Сѓ production, РІС–РґСЃСѓС‚РЅС–СЃС‚СЊ С„Р°Р»СЊС€РёРІРёС… business endpoints.

Frontend: РЅР°РІС–РіР°С†С–СЏ Р№ active route, СЏРІРЅС– TODO, РІС–РґСЃСѓС‚РЅС–СЃС‚СЊ admin navigation
РґРѕ СЂРµР°Р»С–Р·Р°С†С–С— auth, 404 Р·С– Р·Р±РµСЂРµР¶РµРЅРѕСЋ РЅР°РІС–РіР°С†С–С”СЋ, СЃРїСЂР°РІР¶РЅС” РІС–РґРѕР±СЂР°Р¶РµРЅРЅСЏ СЃС‚Р°РЅС–РІ
API, retry РїС–СЃР»СЏ 503, РІС–РґРјРѕРІР° РїСЂРёР№РјР°С‚Рё РЅРµРєРѕСЂРµРєС‚РЅРёР№ readiness JSON СЏРє СѓСЃРїС–С….

РЈ browser preview backend РЅРµ Р·Р°РїСѓС‰РµРЅРёР№, С‚РѕРјСѓ UI РєРѕСЂРµРєС‚РЅРѕ РїРѕРєР°Р·СѓС”
В«Р—вЂ™С”РґРЅР°РЅРЅСЏ РЅРµРґРѕСЃС‚СѓРїРЅРµВ». Р¦Рµ РїРµСЂРµРІС–СЂРєР° failure state, РЅРµ СѓСЃРїС–С€РЅРѕРіРѕ end-to-end.
РўРёРјС‡Р°СЃРѕРІРёР№ preview Р·СѓРїРёРЅРµРЅРѕ РїС–СЃР»СЏ РїРµСЂРµРІС–СЂРєРё. РђРґР°РїС‚РёРІРЅС– CSS РїСЂР°РІРёР»Р° СЂРµР°Р»С–Р·РѕРІР°РЅС–,
Р°Р»Рµ РІС–Р·СѓР°Р»СЊРЅСѓ РїРµСЂРµРІС–СЂРєСѓ РІСѓР·СЊРєРѕРіРѕ РµРєСЂР°РЅР° С‰Рµ РїРѕС‚СЂС–Р±РЅРѕ Р·Р°РІРµСЂС€РёС‚Рё Сѓ Р·РІРёС‡Р°Р№РЅРѕРјСѓ Р±СЂР°СѓР·РµСЂС–.

## Р’С–РґРѕРјС– РїРѕРїРµСЂРµРґР¶РµРЅРЅСЏ С‚Р° РјРµР¶С–

- Starlette 1.7.0 РїРѕРїРµСЂРµРґР¶Р°С” РїСЂРѕ РјР°Р№Р±СѓС‚РЅС” РїСЂРёРїРёРЅРµРЅРЅСЏ httpx support Сѓ СЃРІРѕС”РјСѓ
  TestClient. Р—Р°Р»РёС€РµРЅРѕ Р·Р°РїРёС‚Р°РЅРёР№ СЃС‚РµРє httpx; РїРѕС‚РѕС‡РЅС– С‚РµСЃС‚Рё РїСЂРѕС…РѕРґСЏС‚СЊ.
- npm РїРѕРІС–РґРѕРјР»СЏС” РїСЂРѕ Р·Р°РІРµСЂС€РµРЅРЅСЏ РїС–РґС‚СЂРёРјРєРё ESLint 9. РџРѕС‚РѕС‡РЅРёР№ lock СЃСѓРјС–СЃРЅРёР№
  С– lint РїСЂРѕС…РѕРґРёС‚СЊ; РѕРЅРѕРІР»РµРЅРЅСЏ major РІРµСЂСЃС–С— РїРµСЂРµРІС–СЂРёС‚Рё СЂР°Р·РѕРј С–Р· plugins.
- Р–РѕРґРЅРѕРіРѕ business CRUD/auth Р°Р±Рѕ production deployment Сѓ PHASE 1 РЅРµРјР°С”.
- Unit test doubles Р·Р°СЃС‚РѕСЃРѕРІСѓСЋС‚СЊСЃСЏ Р»РёС€Рµ РІ tests. РЈ product РєРѕРґС– РЅРµРјР°С”
  fake records, fallback metrics Р°Р±Рѕ С€С‚СѓС‡РЅРѕРіРѕ СЃС‚Р°С‚СѓСЃСѓ РіРѕС‚РѕРІРЅРѕСЃС‚С–.
## Phase 1 authorization shell вЂ” 2026-10-02

- Added additive migration `0007_identity_roles_username`; offline PostgreSQL
  SQL generation succeeds and includes deterministic legacy role backfill.
- Backend Ruff/format, import/unit checks and sdist/wheel build pass. The local
  run completed with 12 non-PostgreSQL tests passed; 32 integration tests were
  skipped because PostgreSQL/Docker Engine was unavailable.
- Frontend: 12 tests, ESLint, strict TypeScript and Vite production build pass.
- `docker compose config` renders successfully. Compose up/health, full
  PostgreSQL migration round-trip and Playwright E2E could not run because
  Docker Desktop reports that its engine is not running (virtualization is not
  available on this machine).

## Phase 1-2 runtime gate - 2026-10-02

- Docker Compose rebuilt and started PostgreSQL, backend and frontend; readiness returned HTTP 200.
- PostgreSQL suite passed: **46 tests**. It covered migrations 0001-0008, schema drift,
  downgrade to base, readiness failure, upgrade to head and restored readiness.
- Frontend passed **12 tests**, ESLint and the strict TypeScript/Vite production build.
- Playwright passed the authenticated R&D workflow including promotion review and logout.

## Phase 3 Products - 2026-10-02

- Alembic 0009_phase3_products passed 0008 -> 0009 -> 0008 -> 0009; alembic check
  reports no schema drift. Existing components are backfilled to the seeded PCS UOM.
- Full PostgreSQL suite is green (**47 tests**), including the product lifecycle
  and released-immutability integration test passes.
- Frontend passed **12 tests**, ESLint and strict TypeScript/Vite build with the real Products UI.
- Docker Compose rebuilt successfully after Phase 3; db/backend/frontend are healthy and backend/frontend HTTP checks return 200.

- Development seed completed idempotently and loaded UAV, ground-station and antenna route templates.

## Phase 4 Orders and procurement - 2026-10-02

- Migration `0010_phase4_orders` applies cleanly and `alembic check` reports no schema drift.
  Disposable PostgreSQL regression tests cover downgrade to base and restoration to head.
- Full PostgreSQL suite passed: **49 tests**. The Phase 4 scenario verifies a 100-unit line split
  into 90 standard and 10 substituted units, unchanged source BOM, generated requirements,
  allocation to an ordered procurement record and calculated missing quantity.
- Backend Ruff passed. Frontend passed **12 tests**, ESLint and strict TypeScript/Vite build.
- Playwright passed the authenticated workspace workflow on a disposable Phase 4 database.
- Docker Compose rebuilt successfully; PostgreSQL, backend and frontend reached healthy state,
  and readiness plus the `/production` frontend route returned HTTP 200.
- The Production UI now exposes real orders, variants, approval actions, material progress and
  procurement records; it contains no placeholder success states or sample metrics.

## Phase 5 Production execution - 2026-10-02

- Migration `0011_phase5_execution` applies cleanly and `alembic check` reports no schema drift.
  The disposable PostgreSQL test run also verifies downgrade to base and restoration to head.
- Full PostgreSQL suite passed: **52 tests**. Phase 5 coverage includes serial, batch and quantity
  tracking, route dependency unlocking, worker eligibility, required checklist/note/photo evidence,
  idempotent completion and SQL-derived progress counters.
- Backend Ruff and the Python sdist/wheel build passed. Frontend passed **12 tests**, ESLint and the
  strict TypeScript/Vite production build.
- Playwright passed the authenticated R&D promotion and logout regression workflow on a disposable
  database after the Phase 5 changes.
- Docker Compose rebuilt successfully; PostgreSQL, backend and frontend reached healthy state.
  Backend readiness and the `/my-work` frontend route returned HTTP 200.
- Production orders can now be launched from material readiness into route-based execution. The UI
  provides printable QR labels, assignment and operation progress for managers, plus a tablet-focused
  My Work flow with scanning, instructions, checklists, photo evidence and partial quantity completion.
- `npm audit` reports two moderate findings in the Vitest development dependency chain. They do not
  enter the runtime Nginx image; resolving them requires a separately reviewed Vitest major upgrade.

## Visual system refresh - 2026-10-03

- Reworked the shared application shell and R&D landing page around the product specification's
  restrained engineering style, grouped navigation, compact tables and responsive desktop/tablet UI.
- Frontend passed **12 tests**, ESLint, strict TypeScript and the Vite production build.
- Playwright passed the full authenticated R&D promotion, search and logout workflow (**1 test**).
- Docker rebuilt and restarted the frontend successfully. `/rnd` and backend readiness returned HTTP 200.
- Production form regression was fixed by making customer, order, procurement, order-item, variant,
  deviation and stage-completion actions explicit form submissions. A frontend integration test verifies
  customer creation followed by order creation; the frontend suite now passes **13 tests**.
- Product BOM gained a draft-only component editor with UOM, quantity, position, required flag and
  confirmed deletion. Production procurement gained backend-enforced status transitions and an inline
  next-status control. Full backend suite passed **52 tests**; Ruff, frontend tests, ESLint, strict build
  and Compose healthchecks passed.
