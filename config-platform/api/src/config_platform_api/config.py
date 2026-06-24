from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONFIG_API_", env_file=".env", extra="ignore")

    app_name: str = "Config Platform API"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    connections_file: Path = Path("data/connections.json")
    migrations_file: Path = Path("data/migrations.json")
    verification_ttl_seconds: int = 900
    use_mock_introspection: bool = False


def get_settings() -> Settings:
    return Settings()
