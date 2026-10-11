from datetime import datetime

from sqlalchemy.orm import Session

from app import models

# Seed records (source of truth for dev DB + tests).
SEED_PLAYERS: list[dict] = [
    {"playerId": "p-42", "country": "ES", "level": 18, "lastActiveAt": "2026-08-21T09:00:00Z"},
    {"playerId": "p-77", "country": "SE", "level": 6, "lastActiveAt": "2026-08-17T12:15:00Z"},
    {"playerId": "p-88", "country": "ES", "level": 10, "lastActiveAt": "2026-08-20T20:30:00Z"},
    {"playerId": "p-99", "country": "SE", "level": 11, "lastActiveAt": "2026-08-22T08:45:00Z"},
    {"playerId": "p-101", "country": "FR", "level": 20, "lastActiveAt": "2026-08-22T14:10:00Z"},
    {"playerId": "p-102", "country": "DE", "level": 9, "lastActiveAt": "2026-08-19T16:25:00Z"},
]


def _parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_players(db: Session) -> int:
    """Insert seed players if missing. Returns number inserted."""
    inserted = 0
    for row in SEED_PLAYERS:
        if db.get(models.Player, row["playerId"]) is None:
            db.add(
                models.Player(
                    player_id=row["playerId"],
                    country=row["country"],
                    level=row["level"],
                    last_active_at=_parse_dt(row["lastActiveAt"]),
                )
            )
            inserted += 1
    if inserted:
        db.commit()
    return inserted
