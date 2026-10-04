# Business modules

Add each module with its implementation phase, not empty CRUD scaffolding:

- Phase 2 (implemented): auth, users
- Phase 3 (implemented): projects, tasks
- Phase 4 (implemented): components, setups, firmware
- Phase 5 (implemented): tests
- Phase 6 (implemented): files, comments, search
- Phase 7 (implemented): dashboard

A typical module has `router.py`, `schemas.py`, `models.py`, `service.py`.
HTTP routing delegates to a service; the service validates permissions and
business invariants and controls a SQLAlchemy transaction. Shared models are
imported explicitly in app/migrations/env.py as modules are added. No generic repository base.
