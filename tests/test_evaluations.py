import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.routers.evaluations as eval_router
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


@pytest.fixture(autouse=True)
def _bg_uses_test_db(monkeypatch):
    # Background tasks must not touch the real app.db.
    monkeypatch.setattr(eval_router, "SessionLocal", TestingSessionLocal)


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


def _wait_completed(evaluation_id: str, timeout: float = 10.0):
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/campaign-evaluations/{evaluation_id}").json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.05)
    raise AssertionError(f"{evaluation_id} did not complete in {timeout}s")


def test_start_evaluation():
    resp = client.post("/campaign-evaluations", json=_payload())
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["evaluationId"] == "e-1"
    assert body["campaignId"] == "summer-boost"
    assert body["rules"] == {"minimumLevel": 10, "countries": ["ES", "SE"]}
    assert body["status"] in ("pending", "running", "completed")
    assert body["progress"]["total"] == 2

    body = _wait_completed("e-1")
    assert body["status"] == "completed"
    assert body["progress"] == {"processed": 2, "total": 2}
    by_id = {r["playerId"]: r for r in body["results"]}
    assert by_id["p-42"]["matches"] is True  # ES, level 18
    assert by_id["p-77"]["matches"] is False  # SE, level 6 < 10
    assert by_id["p-77"].get("error") is None


def test_evaluation_persists_matches():
    client.post("/campaign-evaluations", json=_payload(evaluationId="e-2"))
    _wait_completed("e-2")
    with TestingSessionLocal() as db:
        assert crud.get_match(db, "summer-boost", "p-42", "e-2") is not None
        assert crud.get_match(db, "summer-boost", "p-42", "e-2").matches is True
        rows = crud.list_matches(db, campaign_id="summer-boost")
        assert {r.evaluation_id for r in rows} >= {"e-1", "e-2"}


def test_unknown_player_reported_not_failed():
    body = _payload(evaluationId="e-3", playerIds=["p-42", "p-404"])
    resp = client.post("/campaign-evaluations", json=body)
    assert resp.status_code == 202, resp.text
    body = _wait_completed("e-3")
    assert body["status"] == "completed"
    assert body["progress"] == {"processed": 2, "total": 2}
    # Unknown players are skipped: no stored row, batch still completes.
    by_id = {r["playerId"]: r for r in body["results"]}
    assert by_id["p-42"]["matches"] is True
    assert "p-404" not in by_id


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
    assert resp.status_code == 202, resp.text
    body = _wait_completed("e-batch")
    # Duplicates upsert the same row; unknown ids store nothing.
    assert body["progress"] == {"processed": 4, "total": 4}
    results = body["results"]
    assert [r["playerId"] for r in results] == ["p-42", "p-77"]
    assert results[0]["matches"] is True
    assert results[1]["matches"] is False


def test_get_evaluation():
    client.post("/campaign-evaluations", json=_payload(evaluationId="e-get"))
    resp = client.get("/campaign-evaluations/e-get")
    assert resp.status_code == 200, resp.text
    body = _wait_completed("e-get")
    assert body["evaluationId"] == "e-get"
    assert body["campaignId"] == "summer-boost"
    assert body["rules"] == {"minimumLevel": 10, "countries": ["ES", "SE"]}
    assert body["status"] == "completed"
    assert body["progress"] == {"processed": 2, "total": 2}
    by_id = {r["playerId"]: r for r in body["results"]}
    assert by_id["p-42"]["matches"] is True
    assert by_id["p-77"]["matches"] is False


def test_get_pending_evaluation():
    with TestingSessionLocal() as db:
        crud.create_evaluation(
            db,
            evaluation_id="e-pending",
            campaign_id="summer-boost",
            minimum_level=10,
            countries=["ES"],
            total=3,
        )
    body = client.get("/campaign-evaluations/e-pending").json()
    assert body["status"] == "pending"
    assert body["progress"] == {"processed": 0, "total": 3}
    assert body["results"] == []


def test_get_evaluation_not_found():
    assert client.get("/campaign-evaluations/e-missing").status_code == 404


def test_duplicate_evaluation_id_rejected():
    body = _payload(evaluationId="e-dup")
    assert client.post("/campaign-evaluations", json=body).status_code == 202
    dup = client.post("/campaign-evaluations", json=body)
    assert dup.status_code == 409
    assert dup.json()["detail"] == "Evaluation already exists"


def test_failed_run_marked(monkeypatch):
    with TestingSessionLocal() as db:
        crud.create_evaluation(
            db,
            evaluation_id="e-fail",
            campaign_id="summer-boost",
            minimum_level=10,
            countries=[],
            total=1,
        )

    def _boom(db, player_ids):
        raise RuntimeError("db gone")

    monkeypatch.setattr(crud, "get_players_by_ids", _boom)
    crud.execute_evaluation(
        TestingSessionLocal,
        evaluation_id="e-fail",
        campaign_id="summer-boost",
        minimum_level=10,
        countries=[],
        player_ids=["p-42"],
        batch_size=100,
    )
    with TestingSessionLocal() as db:
        run = crud.get_evaluation(db, "e-fail")
        assert run is not None
        assert run.status == "failed"
        assert "db gone" in (run.error or "")
