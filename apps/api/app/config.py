from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra="ignore")

    # Database
    database_url: str

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Cloudflare R2
    r2_endpoint_url: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str = "claimsmart-bills"

    # Firebase Admin SDK
    firebase_project_id: str
    firebase_client_email: str
    firebase_private_key: str

    # App
    app_env: str = "development"
    internal_api_secret: str = "change-me"


settings = Settings()
