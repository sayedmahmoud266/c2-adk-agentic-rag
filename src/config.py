"""Central configuration using pydantic-settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    litellm_model: str = "openai/gpt-4o"
    litellm_api_base: str = ""      # custom base URL (LMStudio, Ollama proxy, OpenRouter, etc.)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_api_base: str = "http://localhost:11434"

    # ChromaDB path (embeddings handled internally)
    chromadb_path: str = "data/chromadb"

    # RAG
    top_k_results: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50

    # App
    app_name: str = "HR Assistant"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me-in-production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
