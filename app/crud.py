from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def get_player(db: Session, player_id: str) -> models.Player | None:
    return db.get(models.Player, player_id)


def list_players(
    db: Session, skip: int = 0, limit: int = 100, country: str | None = None
) -> list[models.Player]:
    stmt = select(models.Player).order_by(models.Player.player_id).offset(skip).limit(limit)
    if country is not None:
        stmt = select(models.Player).where(models.Player.country == country).order_by(
            models.Player.player_id
        ).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())
