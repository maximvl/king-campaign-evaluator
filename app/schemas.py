from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    player_id: str = Field(alias="playerId")
    country: str = Field(min_length=2, max_length=2)
    level: int = Field(ge=0)
    last_active_at: datetime = Field(alias="lastActiveAt")


class CampaignMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    campaign_id: str = Field(alias="campaignId")
    player_id: str = Field(alias="playerId")
    minimum_level: int = Field(ge=0, alias="minimumLevel")
    countries: list[str] = Field(default_factory=list)
    matches: bool
