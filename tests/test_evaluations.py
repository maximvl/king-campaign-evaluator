from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, models
from app.database import get_db
from app.main import create_app
from app.seed import seed_players

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


def _payload(**overrides):
    body = {
        "evaluationId": "e-1",
        "rules": {
            "campaignId": "summer-boost",
            "minimumLevel": 10,
            "countries": ["ES", "SE"],
        },
        "playerIds": ["p-42", "p-77"],
    }
    body.update(overrides)
    return body


def test_start_evaluation():
    resp = client.post("/campaign-evaluations", json=_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["evaluationId"] == "e-1"
    assert body["campaignId"] == "summer-boost"
    assert body["rules"] == {"minimumLevel": 10, "countries": ["ES", "SE"]}
    by_id = {r["playerId"]: r for r in body["results"]}
    assert by_id["p-42"]["matches"] is True  # ES, level 18
    assert by_id["p-77"]["matches"] is False  # SE, level 6 < 10
    assert by_id["p-77"].get("error") is None


def test_evaluation_persists_matches():
    client.post("/campaign-evaluations", json=_payload(evaluationId="e-2"))
    with TestingSessionLocal() as db:
        assert crud.get_match(db, "summer-boost", "p-42", "e-2") is not None
        assert crud.get_match(db, "summer-boost", "p-42", "e-2").matches is True
        rows = crud.list_matches(db, campaign_id="summer-boost")
        assert {r.evaluation_id for r in rows} >= {"e-1", "e-2"}


def test_unknown_player_reported_not_failed():
    body = _payload(evaluationId="e-3", playerIds=["p-42", "p-404"])
    resp = client.post("/campaign-evaluations", json=body)
    assert resp.status_code == 201, resp.text
    by_id = {r["playerId"]: r for r in resp.json()["results"]}
    assert by_id["p-42"]["matches"] is True
    assert by_id["p-404"]["matches"] is False
    assert by_id["p-404"]["error"] == "player not found"


def test_empty_player_ids_rejected():
    resp = client.post("/campaign-evaluations", json=_payload(playerIds=[]))
    assert resp.status_code == 422


def test_batched_fetch_same_results(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "evaluation_batch_size", 1)
    resp = client.post(
        "/campaign-evaluations",
        json=_payload(
            evaluationId="e-batch",
            playerIds=["p-42", "p-77", "p-404", "p-42"],
        ),
    )
    assert resp.status_code == 201, resp.text
    results = resp.json()["results"]
    assert len(results) == 4  # request order kept, duplicates evaluated twice
    assert [r["playerId"] for r in results] == ["p-42", "p-77", "p-404", "p-42"]
    assert results[0]["matches"] is True
    assert results[1]["matches"] is False
    assert results[2]["error"] == "player not found"


def test_get_evaluation():
    client.post("/campaign-evaluations", json=_payload(evaluationId="e-get"))
    resp = client.get("/campaign-evaluations/e-get")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["evaluationId"] == "e-get"
    assert body["campaignId"] == "summer-boost"
    assert body["rules"] == {"minimumLevel": 10, "countries": ["ES", "SE"]}
    by_id = {r["playerId"]: r for r in body["results"]}
    assert by_id["p-42"]["matches"] is True
    assert by_id["p-77"]["matches"] is False


def test_get_evaluation_not_found():
    assert client.get("/campaign-evaluations/e-missing").status_code == 404
