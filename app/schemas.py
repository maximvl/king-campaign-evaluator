from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    player_id: str = Field(alias="playerId")
    country: str = Field(min_length=2, max_length=2)
    level: int = Field(ge=0)
    last_active_at: datetime = Field(alias="lastActiveAt")
