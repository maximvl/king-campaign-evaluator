# king-campaign-evaluator
excercise

## Run from scratch

Requires Python `>=3.10` (see `pyproject.toml`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"

cp .env.example .env   # optional, default DATABASE_URL=sqlite:///./app.db
uvicorn app.main:app --reload --port 8000
```

Tables are auto-created on startup (`app/main.py` lifespan).

Verify:

```bash
curl localhost:8000/health
# {"status":"ok"}

curl -X POST localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"widget"}'
```

- Docs: `http://127.0.0.1:8000/docs`
- Tests: `pytest -q`
- Reset DB: stop server, `rm app.db`, restart.

Layout: `app/main.py` (app factory), `app/database.py` (engine/session/`get_db`),
`app/models.py`, `app/schemas.py`, `app/crud.py`, `app/routers/items.py`.

## Decisions

- 2026-10-11: Chose FastAPI + SQLAlchemy 2.0 typed models + SQLite via `DATABASE_URL` — zero-config local dev, file DB, swappable via env.
- 2026-10-11: Used `create_app()` factory with `lifespan` running `Base.metadata.create_all` — simple init without migrations for starter stage.
- 2026-10-11: Split `models.py` / `schemas.py` / `crud.py` / `routers/` — keeps routes thin and models testable.
- 2026-10-11: Added `agents.md` with mandatory README decision-log rule — keeps architectural rationale visible.
