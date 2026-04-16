from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    # App
    app_env: str = "development"
    internal_api_secret: str = "change-me"


settings = Settings()
