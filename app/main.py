from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models
from app.config import settings
from app.database import engine
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(items.router)
    return app


app = create_app()
