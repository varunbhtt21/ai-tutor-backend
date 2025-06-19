"""
Configuration management for AI Tutor Backend
"""

from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "AI Tutor Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "ai_tutor_db"
    database_user: str = "postgres"
    database_password: str = "postgres"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 1000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:8501", "http://localhost:3000"]
    
    # Code Sandbox
    code_sandbox_url: str = "http://localhost:8080"
    code_sandbox_timeout: int = 30
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("database_url", pre=True)
    def assemble_db_connection(cls, v, values):
        if isinstance(v, str) and v:
            return v
        # Fallback to component-based URL if not provided
        return (
            f"postgresql://{values.get('database_user')}:"
            f"{values.get('database_password')}@"
            f"{values.get('database_host')}:{values.get('database_port')}/"
            f"{values.get('database_name')}"
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 