# Залежності та їх призначення

Додаємо бібліотеки на етапі, коли вони використовуються. Frontend lockfile і
backend requirements.lock фіксують фактично перевірений набір версій.

| Етап | Залежності | Навіщо |
|---|---|---|
| 1 backend | FastAPI, Uvicorn | HTTP API, OpenAPI та ASGI server |
| 1 backend | SQLAlchemy 2, psycopg[binary] | typed ORM/session та PostgreSQL driver без локального компілятора |
| 1 backend | Alembic | контрольована історія schema migrations |
| 1 backend | Pydantic, pydantic-settings | response validation та конфігурація з environment/.env |
| 1 backend dev | pytest, httpx | API/configuration/integration tests |
| 1 backend dev | Ruff, build, setuptools | lint/format, перевірка Python package build |
| 1 frontend | React, React DOM, TypeScript, Vite, React plugin | UI, strict typecheck, dev server, static build |
| 1 frontend | React Router | сторінки та постійний layout |
| 1 frontend | TanStack Query | асинхронний API стан, кеш, retry/refetch |
| 1 frontend | Tailwind CSS, @tailwindcss/vite | utility styles та дизайн-токени |
| 1 frontend | lucide-react | узгоджені SVG іконки |
| 1 frontend dev | ESLint, typescript-eslint, hooks/refresh plugins, globals | lint React/TypeScript |
| 1 frontend dev | Vitest, jsdom, Testing Library/react + jest-dom | DOM і routing tests |
| 2 | PyJWT, pwdlib[argon2] | підпис/перевірка JWT та password hashing |
| 2 | email-validator | перевірка email через Pydantic EmailStr без власного неповного regex |
| 2 | @radix-ui/react-slot, class-variance-authority, clsx, tailwind-merge | композиція кнопки shadcn/ui та узгодження Tailwind-класів і варіантів |
| 2–3 | React Hook Form, Zod, @hookform/resolvers | керування формами та schema validation |
| 5 frontend | qrcode.react | локальне SVG-генерування друкованих QR-міток без зовнішнього сервісу |
| 2–3 | shadcn/ui компоненти та лише потрібні їм primitives | доступні reusable UI компоненти; source у репозиторії, не blanket UI dependency |
| 5 | Recharts | графіки з TestMeasurement |
| 6 | python-multipart | streaming file upload через FastAPI |
| 3 dev; 7 розширення | @playwright/test | browser/API/PostgreSQL smoke для auth/projects/tasks; повний workflow у PHASE 7 |

Python 3.14, Node 22 (>=22.12), PostgreSQL 17 — baseline runtime.
Node мінімум обрано за [вимогами Vite](https://vite.dev/guide/).
Контейнери мають major-tag runtime images; для production release варто
фіксувати перевірені image digests і регулярно оновлювати їх.
