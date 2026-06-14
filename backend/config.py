"""
Configuration management and validation for VishwaGuru application.
Centralizes environment variable handling and provides startup validation.
"""

import os
import sys
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """
    Application configuration class with validation.
    Loads and validates all required environment variables.
    """
    
    # API Keys
    gemini_api_key: str
    telegram_bot_token: str
    
    # Database
    database_url: str
    
    # Application Settings
    environment: str
    debug: bool
    cors_origins: list[str]
    
    # File Upload Settings
    max_upload_size_mb: int
    allowed_file_types: list[str]
    
    # Rate Limiting
    rate_limit_enabled: bool
    max_requests_per_minute: int
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables with validation.
        Raises ValueError if required variables are missing.
        """
        errors = []
        
        # Required variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            errors.append("GEMINI_API_KEY is required")
        
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        # Database with default
        database_url = os.getenv(
            "DATABASE_URL", 
            "sqlite:///./data/issues.db"
        )
        
        # Ensure data directory exists for SQLite
        if database_url.startswith("sqlite"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Optional settings with defaults
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # CORS settings
        cors_origins_str = os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:3000"
        )
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # File upload settings
        max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
        allowed_file_types_str = os.getenv(
            "ALLOWED_FILE_TYPES",
            "image/jpeg,image/png,image/jpg,video/mp4"
        )
        allowed_file_types = [ft.strip() for ft in allowed_file_types_str.split(",")]
        
        # Rate limiting
        rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
        
        # If there are errors, raise with all missing variables
        if errors:
            error_message = "Missing required environment variables:\n" + "\n".join(f"  - {err}" for err in errors)
            error_message += "\n\nPlease create a .env file with required variables. See .env.example for reference."
            raise ValueError(error_message)
        
        return cls(
            gemini_api_key=gemini_api_key,
            telegram_bot_token=telegram_bot_token,
            database_url=database_url,
            environment=environment,
            debug=debug,
            cors_origins=cors_origins,
            max_upload_size_mb=max_upload_size_mb,
            allowed_file_types=allowed_file_types,
            rate_limit_enabled=rate_limit_enabled,
            max_requests_per_minute=max_requests_per_minute,
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_database_type(self) -> str:
        """Get the type of database being used."""
        if self.database_url.startswith("postgresql"):
            return "postgresql"
        elif self.database_url.startswith("sqlite"):
            return "sqlite"
        else:
            return "unknown"
    
    def validate_api_keys(self) -> dict[str, bool]:
        """
        Validate that API keys are properly formatted.
        Returns dict with validation status for each key.
        """
        validations = {
            "gemini_api_key": len(self.gemini_api_key) > 20,
            "telegram_bot_token": ":" in self.telegram_bot_token and len(self.telegram_bot_token) > 40,
        }
        return validations
    
    def __repr__(self) -> str:
        """Safe representation hiding sensitive data."""
        return (
            f"Config(\n"
            f"  environment={self.environment},\n"
            f"  database={self.get_database_type()},\n"
            f"  debug={self.debug},\n"
            f"  gemini_api_key={'*' * 10 if self.gemini_api_key else 'NOT SET'},\n"
            f"  telegram_bot_token={'*' * 10 if self.telegram_bot_token else 'NOT SET'}\n"
            f")"
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.
    This ensures configuration is loaded only once.
    """
    global _config
    if _config is None:
        try:
            _config = Config.from_env()
        except ValueError as e:
            print(f"\n❌ Configuration Error:\n{e}\n", file=sys.stderr)
            sys.exit(1)
    return _config


def validate_startup_config() -> bool:
    """
    Validate configuration at startup.
    Returns True if valid, prints errors and returns False otherwise.
    """
    try:
        config = get_config()
        
        print("\n✅ Configuration loaded successfully!")
        print(f"   Environment: {config.environment}")
        print(f"   Database: {config.get_database_type()}")
        print(f"   Debug Mode: {config.debug}")
        
        # Validate API keys format
        validations = config.validate_api_keys()
        
        if not all(validations.values()):
            print("\n⚠️  Warning: Some API keys may be incorrectly formatted:")
            for key, is_valid in validations.items():
                if not is_valid:
                    print(f"   - {key}: Invalid format")
            return False
        
        print("   API Keys: ✓ Valid format")
        print()
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration validation failed: {e}\n", file=sys.stderr)
        return False


# Convenience function to get specific config values
def get_gemini_api_key() -> str:
    """Get Gemini API key from config."""
    return get_config().gemini_api_key


def get_telegram_bot_token() -> str:
    """Get Telegram bot token from config."""
    return get_config().telegram_bot_token


def get_database_url() -> str:
    """Get database URL from config."""
    return get_config().database_url
