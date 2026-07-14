from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Supabase (if needed for API calls outside of DB)
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_publishable_key: str = Field(..., alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_secret_key: str = Field(..., alias="SUPABASE_SECRET_KEY")
    supabase_jwks_url: str = Field(..., alias="SUPABASE_JWKS_URL")
    
    # Gemini
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    
    # Authentication
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Firebase
    firebase_credentials_file: Optional[str] = Field(default=None, alias="FIREBASE_CREDENTIALS_FILE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
