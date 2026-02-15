"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings pulled from environment variables."""

    # App
    app_name: str = "LeadGen Intelligence Pipeline"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""  # service_role key for backend
    supabase_anon_key: str = ""

    # Scraping
    max_concurrent_scrapes: int = 3
    scrape_delay_min: float = 2.0
    scrape_delay_max: float = 5.0
    headless_browser: bool = True
    enable_demo_fallback: bool = False

    # Google Maps
    google_maps_api_key: Optional[str] = None

    # CORS
    cors_origins: str = "*"

    # Railway
    railway_environment: Optional[str] = None

    @property
    def is_production(self) -> bool:
        return self.railway_environment is not None or not self.debug

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
