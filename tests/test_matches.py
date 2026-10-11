from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, models
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


def test_evaluate_match():
    with TestingSessionLocal() as db:
        p42 = crud.get_player(db, "p-42")  # ES, level 18
        assert p42 is not None
        assert crud.evaluate_match(p42, 10, ["ES", "SE"]) is True
        assert crud.evaluate_match(p42, 19, ["ES"]) is False  # level too low
        assert crud.evaluate_match(p42, 10, ["SE"]) is False  # wrong country
        assert crud.evaluate_match(p42, 10, []) is True  # no country restriction


def test_save_and_get_match():
    with TestingSessionLocal() as db:
        p88 = crud.get_player(db, "p-88")  # ES, level 10
        assert p88 is not None
        saved = crud.save_match(
            db,
            player=p88,
            evaluation_id="e-1",
            minimum_level=10,
            countries=["ES"],
        )
        assert saved.matches is True

        fetched = crud.get_match(db, "p-88", "e-1")
        assert fetched is not None
        assert fetched.matches is True

        # Re-evaluate with stricter conditions upserts in place.
        updated = crud.save_match(
            db,
            player=p88,
            evaluation_id="e-1",
            minimum_level=11,
            countries=["ES"],
        )
        assert updated.matches is False
        assert crud.get_match(db, "nope", "e-1") is None


def _make_run(db, evaluation_id, campaign_id="c-2"):
    if crud.get_evaluation(db, evaluation_id) is None:
        crud.create_evaluation(
            db,
            evaluation_id=evaluation_id,
            campaign_id=campaign_id,
            minimum_level=10,
            countries=[],
            total=3,
        )


def test_list_matches():
    with TestingSessionLocal() as db:
        _make_run(db, "e-list")
        for pid in ("p-42", "p-77", "p-88"):
            player = crud.get_player(db, pid)
            assert player is not None
            crud.save_match(
                db,
                player=player,
                evaluation_id="e-list",
                minimum_level=10,
                countries=[],
            )
        all_rows = crud.list_matches(db, campaign_id="c-2")
        assert len(all_rows) == 3
        matched = crud.list_matches(db, campaign_id="c-2", matches_only=True)
        assert {r.player_id for r in matched} >= {"p-42", "p-88"}
        assert all(r.matches for r in matched)
