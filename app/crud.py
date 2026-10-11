from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def get_player(db: Session, player_id: str) -> models.Player | None:
    return db.get(models.Player, player_id)


def get_players_by_ids(db: Session, player_ids: list[str]) -> list[models.Player]:
    if not player_ids:
        return []
    stmt = select(models.Player).where(models.Player.player_id.in_(player_ids))
    return list(db.scalars(stmt).all())


def list_players(
    db: Session, skip: int = 0, limit: int = 100, country: str | None = None
) -> list[models.Player]:
    stmt = select(models.Player).order_by(models.Player.player_id).offset(skip).limit(limit)
    if country is not None:
        stmt = select(models.Player).where(models.Player.country == country).order_by(
            models.Player.player_id
        ).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def evaluate_match(
    player: models.Player, minimum_level: int, countries: list[str]
) -> bool:
    if player.level < minimum_level:
        return False
    if countries and player.country not in countries:
        return False
    return True


def save_match(
    db: Session,
    *,
    campaign_id: str,
    player: models.Player,
    evaluation_id: str,
    minimum_level: int,
    countries: list[str],
) -> models.CampaignMatch:
    """Evaluate conditions against a player and upsert the result."""
    result = evaluate_match(player, minimum_level, countries)
    record = get_match(db, campaign_id, player.player_id, evaluation_id)
    if record is None:
        record = models.CampaignMatch(
            campaign_id=campaign_id,
            player_id=player.player_id,
            evaluation_id=evaluation_id,
        )
        db.add(record)
    record.minimum_level = minimum_level
    record.countries = list(countries)
    record.matches = result
    db.commit()
    db.refresh(record)
    return record


def get_match(
    db: Session, campaign_id: str, player_id: str, evaluation_id: str
) -> models.CampaignMatch | None:
    stmt = (
        select(models.CampaignMatch)
        .where(models.CampaignMatch.campaign_id == campaign_id)
        .where(models.CampaignMatch.player_id == player_id)
        .where(models.CampaignMatch.evaluation_id == evaluation_id)
    )
    return db.scalars(stmt).one_or_none()


def evaluation_exists(db: Session, evaluation_id: str) -> bool:
    stmt = select(models.CampaignMatch.id).where(
        models.CampaignMatch.evaluation_id == evaluation_id
    )
    return db.scalars(stmt.limit(1)).first() is not None


def list_evaluation_matches(
    db: Session, evaluation_id: str, skip: int = 0, limit: int = 500
) -> list[models.CampaignMatch]:
    stmt = (
        select(models.CampaignMatch)
        .where(models.CampaignMatch.evaluation_id == evaluation_id)
        .order_by(models.CampaignMatch.player_id)
    )
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())


def list_matches(
    db: Session,
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    matches_only: bool = False,
) -> list[models.CampaignMatch]:
    stmt = (
        select(models.CampaignMatch)
        .where(models.CampaignMatch.campaign_id == campaign_id)
        .order_by(models.CampaignMatch.player_id)
    )
    if matches_only:
        stmt = stmt.where(models.CampaignMatch.matches.is_(True))
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())
