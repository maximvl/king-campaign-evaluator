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
    """Whether a player matched an evaluation's rules.

    One row per (evaluation, player). Campaign and rules live on the
    `Evaluation` run row — this table stores only the outcome.
    """

    __tablename__ = "campaign_matches"
    __table_args__ = (UniqueConstraint("evaluation_id", "player_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    matches: Mapped[bool] = mapped_column(nullable=False, index=True)


class Evaluation(Base):
    """An async campaign-evaluation run with progress tracking."""

    __tablename__ = "evaluations"

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    evaluation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    minimum_level: Mapped[int] = mapped_column(nullable=False)
    countries: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PENDING, index=True)
    total: Mapped[int] = mapped_column(nullable=False, default=0)
    processed: Mapped[int] = mapped_column(nullable=False, default=0)
    matched: Mapped[int] = mapped_column(nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
