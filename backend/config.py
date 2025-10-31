import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Oracle DB Config
    ORACLE_HOST: str
    ORACLE_PORT: int = 1521
    ORACLE_DB_NAME: str
    ORACLE_USER: str
    ORACLE_PASSWORD: str

    # Gemini API Config
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # FastAPI Config
    FASTAPI_ENV: str = "development"
    FASTAPI_LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
