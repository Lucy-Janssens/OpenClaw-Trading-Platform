from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://appuser:securepass@localhost:5432/appdb"
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET: str = ""
    TESTNET: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
