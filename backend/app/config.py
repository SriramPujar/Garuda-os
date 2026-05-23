import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file at startup
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Garuda Dharma OS"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///d:/P/OS/backend/app/data/garuda_dharma.db"
    
    # Spotify API Credentials
    SPOTIFY_CLIENT_ID: Optional[str] = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    # Ollama settings (Local LLM)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct") # Excellent multilingual/Sanskrit model
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    
    # Vector DB settings (Qdrant client local or server)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_PREFER_GRPC: bool = False
    
    # JWT Auth settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dharmic-secret-key-for-local-first-usage")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days for local-first comfort
    
    class Config:
        case_sensitive = True

settings = Settings()
