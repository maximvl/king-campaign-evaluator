from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import create_app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

models.Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = create_app()
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_item_crud():
    created = client.post("/items", json={"name": "widget"}).json()
    assert created["name"] == "widget"
    item_id = created["id"]

    assert client.get(f"/items/{item_id}").json()["id"] == item_id
    assert len(client.get("/items").json()) >= 1

    updated = client.patch(f"/items/{item_id}", json={"description": "a useful widget"}).json()
    assert updated["description"] == "a useful widget"

    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404
