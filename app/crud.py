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
    player: models.Player,
    evaluation_id: str,
    minimum_level: int,
    countries: list[str],
) -> models.CampaignMatch:
    """Evaluate conditions against a player and upsert the result."""
    result = evaluate_match(player, minimum_level, countries)
    record = get_match(db, player.player_id, evaluation_id)
    if record is None:
        record = models.CampaignMatch(
            player_id=player.player_id,
            evaluation_id=evaluation_id,
        )
        db.add(record)
    record.matches = result
    record.error = None
    db.commit()
    db.refresh(record)
    return record


def save_unknown(
    db: Session, *, player_id: str, evaluation_id: str, error: str
) -> models.CampaignMatch:
    """Record an unevaluatable player (e.g. unknown id) without failing the run."""
    record = get_match(db, player_id, evaluation_id)
    if record is None:
        record = models.CampaignMatch(
            player_id=player_id,
            evaluation_id=evaluation_id,
        )
        db.add(record)
    record.matches = False
    record.error = error
    db.commit()
    db.refresh(record)
    return record


def get_match(
    db: Session, player_id: str, evaluation_id: str
) -> models.CampaignMatch | None:
    stmt = (
        select(models.CampaignMatch)
        .where(models.CampaignMatch.player_id == player_id)
        .where(models.CampaignMatch.evaluation_id == evaluation_id)
    )
    return db.scalars(stmt).one_or_none()


def evaluation_exists(db: Session, evaluation_id: str) -> bool:
    return db.get(models.Evaluation, evaluation_id) is not None


def get_evaluation(db: Session, evaluation_id: str) -> models.Evaluation | None:
    return db.get(models.Evaluation, evaluation_id)


def create_evaluation(
    db: Session,
    *,
    evaluation_id: str,
    campaign_id: str,
    minimum_level: int,
    countries: list[str],
    total: int,
) -> models.Evaluation:
    run = models.Evaluation(
        evaluation_id=evaluation_id,
        campaign_id=campaign_id,
        minimum_level=minimum_level,
        countries=list(countries),
        status=models.Evaluation.PENDING,
        total=total,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_evaluation(db: Session, run: models.Evaluation, **fields) -> models.Evaluation:
    for field, value in fields.items():
        setattr(run, field, value)
    db.commit()
    db.refresh(run)
    return run


def execute_evaluation(
    db_factory,
    *,
    evaluation_id: str,
    campaign_id: str,
    minimum_level: int,
    countries: list[str],
    player_ids: list[str],
    batch_size: int,
) -> None:
    """Run an evaluation in a worker: fetch a batch, evaluate it, repeat.

    Uses its own session (never the request's). Progress is committed per
    batch; any failure marks the run failed instead of raising.
    """
    with db_factory() as db:
        run = get_evaluation(db, evaluation_id)
        if run is None:
            return
        update_evaluation(db, run, status=models.Evaluation.RUNNING)
        try:
            matched_total = 0
            for i in range(0, len(player_ids), batch_size):
                chunk = player_ids[i : i + batch_size]
                found = {p.player_id: p for p in get_players_by_ids(db, chunk)}
                for pid in chunk:
                    player = found.get(pid)
                    if player is None:
                        save_unknown(
                            db,
                            player_id=pid,
                            evaluation_id=evaluation_id,
                            error="player not found",
                        )
                        continue
                    record = save_match(
                        db,
                        player=player,
                        evaluation_id=evaluation_id,
                        minimum_level=minimum_level,
                        countries=countries,
                    )
                    if record.matches:
                        matched_total += 1
                update_evaluation(
                    db,
                    run,
                    processed=min(i + batch_size, len(player_ids)),
                    matched=matched_total,
                )
            update_evaluation(
                db,
                run,
                status=models.Evaluation.COMPLETED,
                processed=len(player_ids),
                matched=matched_total,
            )
        except Exception as exc:
            update_evaluation(
                db, run, status=models.Evaluation.FAILED, error=str(exc)[:500]
            )


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
        .join(
            models.Evaluation,
            models.CampaignMatch.evaluation_id == models.Evaluation.evaluation_id,
        )
        .where(models.Evaluation.campaign_id == campaign_id)
        .order_by(
            models.CampaignMatch.evaluation_id, models.CampaignMatch.player_id
        )
    )
    if matches_only:
        stmt = stmt.where(models.CampaignMatch.matches.is_(True))
    return list(db.scalars(stmt.offset(skip).limit(limit)).all())
