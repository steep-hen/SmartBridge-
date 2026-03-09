"""
Configuration management for AI Financial Advisor backend.

Loads environment variables from .env file and provides type-validated
configuration through Pydantic settings.

Usage:
    from backend.config import settings
    db_url = settings.database_url
"""

import logging
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Raises:
        ValidationError: If required environment variables are missing
                        or invalid types.
    
    Environment Variables:
        DATABASE_URL: PostgreSQL connection string
        APP_ENV: Application environment (development, staging, production)
        SECRET_KEY: Secret key for API authentication (min 32 chars)
        GEMINI_API_KEY: Google Gemini API key (optional, for AI advice)
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    # Application Configuration
    debug: bool = True
    environment: str = "development"
    app_env: str = "development"  # Alias for environment
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Database Configuration
    # Use SQLite for development (no external DB needed)
    # For production, use: postgresql://user:password@host:5432/dbname
    database_url: str = (
        "sqlite:///./smartbridge_dev.db"
    )
    postgres_url: Optional[str] = None  # Alias for database_url

    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    
    # AI Configuration
    gemini_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file

    def __init__(self, **data):
        """Initialize settings and validate on startup."""
        super().__init__(**data)
        # Sync app_env with environment if not explicitly set
        if self.app_env == "development" and self.environment != "development":
            self.app_env = self.environment
        self._setup_logging()

    @property
    def db_url(self) -> str:
        """
        Get database URL with fallback support.
        
        Returns:
            str: PostgreSQL connection URL
        """
        return self.postgres_url or self.database_url
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        env = (self.app_env or self.environment).lower()
        return env in ("development", "dev", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        env = (self.app_env or self.environment).lower()
        return env in ("production", "prod")
    
    @property
    def has_gemini_api_key(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.gemini_api_key and len(self.gemini_api_key) > 0)

    def _setup_logging(self) -> None:
        """Configure logging at module level based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Singleton instance of settings
settings = Settings()

if settings.debug:
    logger = logging.getLogger(__name__)
    logger.debug(f"Loaded settings from environment (env={settings.environment})")
