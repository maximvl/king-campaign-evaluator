# Agents

Project: FastAPI + SQLAlchemy (SQLite) starter.

## Workflow

- Stack: FastAPI, SQLAlchemy 2.0 (typed `Mapped` models), Pydantic v2, SQLite.
- Config: `app/config.py` via `pydantic-settings` (`DATABASE_URL`, `.env` supported).
- DB: engine/session in `app/database.py`; models in `app/models.py`; validation in `app/schemas.py`; DB logic in `app/crud.py`; routes in `app/routers/`.
- App entry: `app/main.py` (`create_app()` factory, `lifespan` runs `Base.metadata.create_all`).

## Commands

- Install: `pip install -e ".[test]"`
- Run: `uvicorn app.main:app --reload`
- Test: `pytest -q`

## Rules

1. Keep routes thin: routers -> `crud.py` -> models. No SQL in routers.
2. All DB access via `get_db` dependency (`app/database.py`).
3. Schemas: `ItemCreate` / `ItemUpdate` / `ItemRead` pattern; `from_attributes=True` on read models.
4. SQLite dev default must keep `check_same_thread=False`; preserve for other DBs without it.
5. Tests use in-memory SQLite + dependency override (see `tests/test_items.py`). Add/extend tests for new endpoints.

## 6. README decision log (mandatory)

Whenever you make a significant decision — new dependency, schema/model change, new router/module, config change, test strategy change, migration choice — you MUST append an entry to `README.md` under `## Decisions`:

Format:

```markdown
- YYYY-MM-DD: <decision> — <why / alternatives considered>.
```

Keep it to 1-2 lines per entry. Do not skip this, even for small refactors that change structure or behavior.
