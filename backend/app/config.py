from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default: SQLite (zero-install, great for dev/demo)
    # Override in .env with a PostgreSQL URL for production:
    #   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/crm_hcp
    database_url: str = "sqlite+aiosqlite:///./crm_hcp.db"
    groq_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
