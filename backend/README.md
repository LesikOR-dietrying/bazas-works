# BAZA backend

FastAPI application factory: `app.main:create_app`. Python 3.14, PostgreSQL 17.
The source repository root README describes setup, tests and Docker Compose.

Install `requirements-dev.lock` and the editable package for development.
Run `python -m alembic upgrade head`, then
`python -m uvicorn app.main:create_app --factory` from this directory.
Credentials must come from environment variables or the repository `.env`.

Alembic resources live in `app/migrations` and are included in the wheel.
The packaged application works with environment configuration; the root `.env`
lookup is only a convenience when running from the source checkout.
