from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    TELEGRAM_BOT_NAME: str 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()