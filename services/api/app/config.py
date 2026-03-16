from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://appuser:securepass@localhost:5432/appdb"
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET: str = ""
    TESTNET: bool = True
    LLM_PROVIDER: str = "openai" # or "gemini", "anthropic"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    DISCORD_WEBHOOK_URL: str = ""
    STRATEGY_PROFILE: str = "balanced"  # conservative | balanced | aggressive

    class Config:
        env_file = ".env"

settings = Settings()
