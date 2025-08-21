import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Search API Configuration
    serpapi_key: Optional[str] = None
    bing_api_key: Optional[str] = None
    google_search_api_key: Optional[str] = None
    
    # Redis Configuration
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # Application Configuration
    log_level: str = "INFO"
    max_concurrent_requests: int = 5
    cache_ttl_minutes: int = 30
    rate_limit_per_domain: int = 2
    
    # User Agent
    user_agent: str = "Mozilla/5.0 (compatible; AI-Crawler/1.0; +https://yourdomain.com/bot)"
    
    # Timeout Settings
    request_timeout: int = 30
    search_timeout: int = 10
    
    # Cache Settings
    whitelist_cache_ttl_hours: int = 24
    product_cache_ttl_minutes: int = 60
    
    # Search Settings
    max_pages_per_domain: int = 5
    max_search_results: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_llm_api_key() -> Optional[str]:
    """Get the first available LLM API key."""
    return (
        settings.openai_api_key or 
        settings.anthropic_api_key or 
        settings.google_api_key
    )


def get_search_api_key() -> Optional[str]:
    """Get the first available search API key."""
    return (
        settings.serpapi_key or 
        settings.bing_api_key or 
        settings.google_search_api_key
    )
