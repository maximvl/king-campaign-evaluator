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
    evaluation_id: str = Field(alias="evaluationId")
    minimum_level: int = Field(ge=0, alias="minimumLevel")
    countries: list[str] = Field(default_factory=list)
    matches: bool


class EvaluationRules(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    campaign_id: str = Field(min_length=1, max_length=50, alias="campaignId")
    minimum_level: int = Field(ge=0, alias="minimumLevel")
    countries: list[str] = Field(default_factory=list)


class CampaignEvaluationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    evaluation_id: str = Field(min_length=1, max_length=50, alias="evaluationId")
    rules: EvaluationRules
    player_ids: list[str] = Field(min_length=1, alias="playerIds")


class PlayerEvaluationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    player_id: str = Field(alias="playerId")
    matches: bool
    error: str | None = None


class CampaignEvaluationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    evaluation_id: str = Field(alias="evaluationId")
    campaign_id: str = Field(alias="campaignId")
    results: list[PlayerEvaluationResult]
