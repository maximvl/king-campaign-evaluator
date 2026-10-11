from datetime import datetime

from sqlalchemy import DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    level: Mapped[int] = mapped_column(nullable=False, index=True)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class CampaignMatch(Base):
    """Whether a player satisfies a campaign's conditions.

    One row per (campaign, player). `countries` is an allowlist —
    empty means no country restriction.
    """

    __tablename__ = "campaign_matches"
    __table_args__ = (UniqueConstraint("campaign_id", "player_id", "evaluation_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    evaluation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    minimum_level: Mapped[int] = mapped_column(nullable=False)
    countries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    matches: Mapped[bool] = mapped_column(nullable=False, index=True)
