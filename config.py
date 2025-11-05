"""
Centralized configuration management using pydantic-settings.
All settings load from environment variables or .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings with validation and defaults"""
    
    # Server
    BACKEND_HOST: str = Field(default="0.0.0.0")
    BACKEND_PORT: int = Field(default=44000)
    
    # Security
    API_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for API authentication"
    )
    
    # External Services
    CHROMADB_HOST: str = Field(default="localhost")
    CHROMADB_PORT: int = Field(default=8000)
    CHROMADB_PATH: str = Field(
        default="/Users/jason/Documents/Vault AI/projects/vault-agent-hub/rag-system/chroma_db"
    )
    OLLAMA_HOST: str = Field(default="localhost")
    OLLAMA_PORT: int = Field(default=40000)
    
    # Performance
    ENABLE_CACHING: bool = Field(default=True)
    CACHE_TTL_SECONDS: int = Field(default=3600, ge=60, le=86400)
    CACHE_MAX_SIZE: int = Field(default=100, ge=10, le=1000)
    CONNECTION_POOL_SIZE: int = Field(default=10, ge=5, le=50)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=120)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000)
    RATE_LIMIT_BURST: int = Field(default=10, ge=5, le=50)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default="addi_backend.log")
    
    # Tool Defaults
    RAG_DEFAULT_N_RESULTS: int = Field(default=3, ge=1, le=10)
    RAG_MIN_CONFIDENCE: float = Field(default=0.5, ge=0.0, le=1.0)
    ANALYTICS_CACHE_TTL: int = Field(default=300)
    
    # ElevenLabs Voice Settings
    ELEVENLABS_API_KEY: Optional[str] = Field(
        default=None,
        description="ElevenLabs API key (starts with 'xi_')"
    )
    ELEVENLABS_VOICE_ID: Optional[str] = Field(
        default=None,
        description="Voice ID for Addi (e.g., '21m00Tcm4TlvDq8ikWAM')"
    )
    ELEVENLABS_MODEL: str = Field(
        default="eleven_turbo_v2",
        description="ElevenLabs TTS model (turbo_v2 for speed, multilingual_v2 for quality)"
    )
    ELEVENLABS_STABILITY: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0-1)"
    )
    ELEVENLABS_SIMILARITY: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost (0-1)"
    )
    ELEVENLABS_STYLE: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Style exaggeration (0-1)"
    )
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

