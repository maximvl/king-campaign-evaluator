from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FastAPI + SQLAlchemy starter"
    database_url: str = "sqlite:///./app.db"
    echo_sql: bool = False
    evaluation_batch_size: int = Field(default=100, ge=1)


settings = Settings()
