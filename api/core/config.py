"""
Configuration settings for Dusty API
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    app_name: str = "Dusty"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./dusty.db"

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # External APIs
    google_places_api_key: str = ""
    yelp_api_key: str = ""
    mapbox_token: str = ""

    # Instagram scraping
    instagram_session_id: str = ""

    # Redis (optional, for caching)
    redis_url: str = ""

    # Scraping settings
    scrape_interval_hours: int = 6
    max_concurrent_scrapes: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
