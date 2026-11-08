import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field  # type: ignore


class Settings(BaseSettings):
    """
    CurriculumAI Studio application settings.
    Supports environment variable overrides and sensible defaults for both
    local standalone execution and production Docker/Kubernetes deployment.
    """
    PROJECT_NAME: str = "CurriculumAI Studio"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "NBA/AICTE-Compliant Curriculum Generation & LaTeX Compilation Studio"
    
    # Security & JWT
    SECRET_KEY: str = Field(
        default=os.getenv("SECRET_KEY", "curriculumai_super_secret_jwt_key_2026_change_in_production"),
        description="HMAC secret key for JWT token signing"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8501",
        "*"
    ]
    
    # Database
    DATABASE_URL: str = Field(
        default=os.getenv("DATABASE_URL", "sqlite:///./curriculumai.db"),
        description="PostgreSQL or SQLite connection string"
    )
    
    # Local & Cloud LLM Providers
    DEFAULT_LLM_PROVIDER: str = Field(default=os.getenv("DEFAULT_LLM_PROVIDER", "ollama"))
    
    # Ollama Local Inference
    OLLAMA_BASE_URL: str = Field(default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    OLLAMA_MODEL: str = Field(default=os.getenv("OLLAMA_MODEL", "qwen2.5:32b"))
    
    # Cloud API Providers
    OPENAI_API_KEY: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY", None))
    OPENAI_MODEL: str = Field(default=os.getenv("OPENAI_MODEL", "gpt-4o"))
    
    ANTHROPIC_API_KEY: Optional[str] = Field(default=os.getenv("ANTHROPIC_API_KEY", None))
    ANTHROPIC_MODEL: str = Field(default=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"))
    
    GEMINI_API_KEY: Optional[str] = Field(default=os.getenv("GEMINI_API_KEY", None))
    GEMINI_MODEL: str = Field(default=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"))
    
    GROQ_API_KEY: Optional[str] = Field(default=os.getenv("GROQ_API_KEY", None))
    GROQ_MODEL: str = Field(default=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    
    # RAG & Embeddings
    CHROMA_PERSIST_DIR: str = Field(default=os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma_db"))
    EMBEDDING_MODEL_NAME: str = Field(default=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3"))
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 5
    
    # LaTeX Compiler
    LATEX_COMPILER_BIN: str = Field(default=os.getenv("LATEX_COMPILER_BIN", "pdflatex"))
    LATEX_TIMEOUT_SECONDS: int = 60
    LATEX_MAX_PASSES: int = 2
    UPLOAD_DIR: str = Field(default=os.getenv("UPLOAD_DIR", "./storage/uploads"))
    EXPORT_DIR: str = Field(default=os.getenv("EXPORT_DIR", "./storage/exports"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
