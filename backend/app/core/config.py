from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "The Nexus Station"
    API_V1_STR: str = "/api/v1"
    
    # Security Constraints
    MAX_DRAFT_SIZE_BYTES: int = 100 * 1024  # 100KB Limit for Drafts
    DEBUG_PROMPTS: bool = False
    OPENROUTER_API_KEY: str = ""
    
    # CORS (For Local React Dev)
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Lp Live-Patch (GitHub)
    LP_VERSIONS_URL: str = "https://raw.githubusercontent.com/TheLightFramework/The-Lp-System/refs/heads/main/Lp_versions.json"
    LP_PROFILE: str = "full_stack"   # e.g. "seed_only", "safety_only", "full_stack"
    LP_CACHE_DIR: str = ".lp_cache"
    LP_HTTP_TIMEOUT_SECONDS: float = 6.0

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()