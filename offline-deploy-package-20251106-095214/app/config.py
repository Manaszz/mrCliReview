"""
Application Configuration

Environment-based settings for code review system.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    VERSION: str = "2.0.0"
    API_TITLE: str = "AI Code Review System"
    API_DESCRIPTION: str = "Multi-agent code review system with Cline and Qwen Code CLI"
    LOG_LEVEL: str = "INFO"
    
    # Model API (OpenAI-compatible)
    MODEL_API_URL: str = "https://api.example.com/v1"
    MODEL_API_KEY: str
    
    # Model Names
    DEEPSEEK_MODEL_NAME: str = "deepseek-v3.1-terminus"
    QWEN3_MODEL_NAME: str = "qwen3-coder-32b"
    
    # CLI Configuration
    DEFAULT_CLI_AGENT: str = "CLINE"  # CLINE or QWEN_CODE
    CLINE_PARALLEL_TASKS: int = 5
    QWEN_PARALLEL_TASKS: int = 3
    REVIEW_TIMEOUT: int = 300  # seconds
    
    # GitLab Configuration
    GITLAB_URL: str = "https://gitlab.example.com"
    GITLAB_TOKEN: str
    
    # Paths
    WORK_DIR: str = "/tmp/review"
    PROMPTS_PATH: str = "prompts"
    DEFAULT_RULES_PATH: str = "rules/java-spring-boot"
    
    # Default Language
    DEFAULT_LANGUAGE: str = "java"
    
    # Optional: Confluence Rules
    CONFLUENCE_RULES_ENABLED: bool = False
    CONFLUENCE_URL: Optional[str] = None
    CONFLUENCE_API_TOKEN: Optional[str] = None
    
    # Optional: MCP RAG
    MCP_RAG_ENABLED: bool = False
    MCP_SERVER_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
