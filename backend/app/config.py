import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "AI Video Generation Platform"
    API_V1_STR: str = "/api/v1"

    # SECURITY: SECRET_KEY must be set via environment variable.
    # Never commit a real value here. Generate with:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = Field(
        default="CHANGE_ME_SET_VIA_ENV_VAR_IN_PRODUCTION",
        description="HS256 JWT signing secret — must be overridden via SECRET_KEY env var"
    )

    # Access tokens expire after 60 minutes; use refresh tokens for long sessions.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour (was 7 days — security fix)

    # CORS: comma-separated list of allowed origins.
    # Example env: ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Static file directory — configurable so containers don't use a dev machine path
    STATIC_DIR: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
        description="Absolute path to the static files directory"
    )

    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "aivideo"
    DATABASE_URL: Optional[str] = None

    # Redis & Celery Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Object Storage (MinIO / S3)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ai-video-assets"

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    @property
    def broker_url(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def result_backend(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
