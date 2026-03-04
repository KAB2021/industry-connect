from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str
    TEST_DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    POLL_INTERVAL_SECONDS: int = 60
    POLL_SOURCE_URL: str = ""
    MAX_UPLOAD_BYTES: int = 10485760  # 10 MB
    TOKEN_THRESHOLD: int = 4000


settings = Settings()
