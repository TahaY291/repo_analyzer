from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    environment: str = "development"
    cors_origins: list[str] = []
    allowed_hosts: list[str] = ["*"]
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    database_url: str
    redis_url: str

    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_pass: str
    sender_email: str

    access_token_secret: str
    refresh_token_secret: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


settings = Settings()