from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_item(db: Session, data: schemas.ItemCreate) -> models.Item:
    item = models.Item(name=data.name, description=data.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: int) -> models.Item | None:
    return db.get(models.Item, item_id)


def list_items(db: Session, skip: int = 0, limit: int = 100) -> list[models.Item]:
    stmt = select(models.Item).order_by(models.Item.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_item(db: Session, item: models.Item, data: schemas.ItemUpdate) -> models.Item:
    patch = data.model_dump(exclude_unset=True)
    for field, value in patch.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: models.Item) -> None:
    db.delete(item)
    db.commit()


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
