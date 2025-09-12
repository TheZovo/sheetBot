from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    bot_token: str = os.getenv("BOT_TOKEN")
    spreadsheet_id: str = os.getenv("SPREADSHEET_ID")
    google_credentials: str = "credentials.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()