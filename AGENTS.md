# Working on BAZA

- Read ARCHITECTURE.md, docs/DATABASE.md and docs/ROADMAP.md before changing a module.
- Keep one modular FastAPI application, one React app and one PostgreSQL database.
- Preserve `Setup -> SetupComponent -> Component`, `Setup -> Test` and
  `Setup -> FirmwareRevision`; never copy component records into a setup.
- Routes handle HTTP, services own business rules and transactions. Use SQLAlchemy
  directly from services; add repositories only for genuinely reused complex queries.
- Every schema change requires a reviewed Alembic migration. No startup create_all.
- Use UUID keys, timezone-aware timestamps, real foreign keys and named constraints.
- JSONB is for specifications, conditions and result summaries, not relationships.
- Authorization belongs on the backend and applies to search, files and related records.
- No fake users, successful writes, metrics or sample data in the application shell.
  Unimplemented work must have an explicit TODO and a roadmap phase.
- Secrets come from the environment; never commit .env or storage contents.
- Python functions have type annotations; TypeScript is strict; avoid any.
- Keep files focused. Explain new dependencies and significant architecture changes.
- Run backend tests/Ruff/package build and frontend tests/ESLint/build after a phase.
  Validate Compose. Report skipped/unavailable checks honestly.
- Changes to destructive UI actions require confirmation in the product.
- Do not move to later phases to bypass a failing check in the current phase.
