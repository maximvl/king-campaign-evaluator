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

curl localhost:8000/players/p-42
```

- Docs: `http://127.0.0.1:8000/docs`
- Tests: `pytest -q`
- Reset DB: stop server, `rm app.db`, restart (dev DB reseeds on boot).

Players (read-only, seeded, 6 records — see `app/seed.py`):

```bash
curl localhost:8000/players | head -c 300
curl "localhost:8000/players?country=ES"
curl localhost:8000/players/p-42
```

Layout: `app/main.py` (app factory), `app/database.py` (engine/session/`get_db`),
`app/models.py`, `app/schemas.py`, `app/crud.py`, `app/seed.py`,
`app/routers/players.py`.

## Decisions

- 2026-10-11: Chose FastAPI + SQLAlchemy 2.0 typed models + SQLite via `DATABASE_URL` — zero-config local dev, file DB, swappable via env.
- 2026-10-11: Used `create_app()` factory with `lifespan` running `Base.metadata.create_all` — simple init without migrations for starter stage.
- 2026-10-11: Split `models.py` / `schemas.py` / `crud.py` / `routers/` — keeps routes thin and models testable.
- 2026-10-11: Added `agents.md` with mandatory README decision-log rule — keeps architectural rationale visible.
- 2026-10-11: Added `Player(player_id PK, country, level, last_active_at)` from sample records — natural string PK matches `playerId`, camelCase API via Pydantic aliases.
- 2026-10-11: Added `app/seed.py` with the 6 sample players, idempotent `seed_players()` run on startup and in tests — same source of truth for dev DB and test DB.
- 2026-10-11: Cut player writes (`POST/PATCH/DELETE`, `PlayerCreate/PlayerUpdate`, write crud) — players are read-only (`GET /players`, `GET /players/{id}`); seed is the only writer.
- 2026-10-11: Fixed duplicate `lifespan` in `app/main.py` shadowing the seeding one — single lifespan now runs `create_all` + `seed_players` on boot.
- 2026-10-11: Removed dummy `Item` model, schemas, crud, router, and tests — players are the only domain left.
- 2026-10-11: Added `CampaignMatch(campaign_id, player_id)` composite PK with `minimum_level`, `countries` JSON allowlist (empty = no restriction), `matches`, plus `evaluate_match`/`save_match` in `crud.py` — no REST yet, service-level only.
- 2026-10-11: Dropped FK from `CampaignMatch.player_id` — plain string, no referential link to `players`.
- 2026-10-11: Switched `CampaignMatch` to surrogate `id` PK with `UniqueConstraint(campaign_id, player_id)` and index on `campaign_id` — combo still unique, lookups by campaign are indexed.
- 2026-10-11: Made `campaign_id` required in `list_matches` — matches are always listed per campaign.
