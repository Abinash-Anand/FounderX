from functools import lru_cache
from pathlib import Path
import json

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    port: int = 8000

    # Accept either a string or a list from environment variables
    cors_origins: str | list[str] = ["https://founder-mju672edf-abinash-anands-projects.vercel.app/"]

    mongodb_uri: str | None = None
    mongodb_database: str = "vc-brain"
    mongodb_pitch_deck_bucket: str = "pitch-decks"
    mongodb_memo_audio_bucket: str = "investment-memos"

    tavily_api_key: SecretStr | None = None
    elevenlabs_api_key: SecretStr | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    openai_api_key: SecretStr | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            value = value.strip()

            # Handle JSON array
            if value.startswith("["):
                return json.loads(value)

            # Handle comma-separated string
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return ["https://founder-mju672edf-abinash-anands-projects.vercel.app/"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
