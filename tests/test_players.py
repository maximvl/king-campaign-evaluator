from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import get_db
from app.main import create_app
from app.seed import SEED_PLAYERS, seed_players

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

models.Base.metadata.create_all(bind=engine)
with TestingSessionLocal() as db:
    seed_players(db)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = create_app()
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_seed_loaded():
    players = client.get("/players").json()
    assert len(players) >= len(SEED_PLAYERS)
    by_id = {p["playerId"]: p for p in players}
    assert by_id["p-42"]["country"] == "ES"
    assert by_id["p-42"]["level"] == 18
    assert by_id["p-101"]["level"] == 20


def test_get_player():
    fetched = client.get("/players/p-42").json()
    assert fetched["playerId"] == "p-42"
    assert fetched["country"] == "ES"
    assert fetched["level"] == 18


def test_get_player_not_found():
    assert client.get("/players/p-404").status_code == 404


def test_country_filter():
    es_players = client.get("/players", params={"country": "ES"}).json()
    assert {p["playerId"] for p in es_players} >= {"p-42", "p-88"}
    assert all(p["country"] == "ES" for p in es_players)


def test_players_read_only():
    payload = {
        "playerId": "p-200",
        "country": "ES",
        "level": 1,
        "lastActiveAt": "2026-08-23T10:00:00Z",
    }
    assert client.post("/players", json=payload).status_code == 405
    assert client.patch("/players/p-42", json={"level": 5}).status_code == 405
    assert client.delete("/players/p-42").status_code == 405
