from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models
from app.config import settings
from app.database import SessionLocal, engine
from app.routers import evaluations, players
from app.seed import seed_players


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_players(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(players.router)
    app.include_router(evaluations.router)
    return app


app = create_app()
