from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ORB — Online Raithu Bazaar API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/orb_db"

    JWT_SECRET_KEY: SecretStr = Field(
        default=SecretStr("CHANGE_THIS_IN_DEVELOPMENT_MINIMUM_32_BYTES")
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    CORS_ORIGINS: str = "http://localhost:5173"

    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE_MB: int = Field(default=5, gt=0)

    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_RECYCLE_SECONDS: int = Field(default=1800, gt=0)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        """Accept explicit booleans while tolerating legacy environment labels."""
        if isinstance(value, str) and value.strip().lower() in {
            "development",
            "dev",
            "test",
            "staging",
            "production",
            "prod",
            "release",
        }:
            # Environment labels are not a request to enable debug; only true/false
            # should control this flag. This keeps production-like values fail-safe.
            return False
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if (
                self.JWT_SECRET_KEY.get_secret_value()
                == "CHANGE_THIS_IN_DEVELOPMENT_MINIMUM_32_BYTES"
            ):
                raise ValueError(
                    "JWT_SECRET_KEY must be configured outside its development placeholder in production."
                )
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production.")
            if len(self.JWT_SECRET_KEY.get_secret_value()) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must contain at least 32 characters in production."
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
