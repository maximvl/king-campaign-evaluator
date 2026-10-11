from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class ItemRead(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    player_id: str = Field(alias="playerId")
    country: str = Field(min_length=2, max_length=2)
    level: int = Field(ge=0)
    last_active_at: datetime = Field(alias="lastActiveAt")
