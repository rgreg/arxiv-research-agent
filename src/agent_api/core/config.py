# src/agent_api/core/config.py
import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    project: str = Field(default_factory=lambda: os.environ.get("GCP_PROJECT", "skillful-flow-470023-c0"))
    location: str = Field(default_factory=lambda: os.environ.get("GCP_REGION", "us-central1"))
    bq_table: str = Field(default_factory=lambda: os.environ.get("BQ_TABLE", "skillful-flow-470023-c.arxiv_demo.chunks"))  
    gemini_model: str = Field(default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite"))
    max_context_chunks: int = int(os.environ.get("MAX_CONTEXT_CHUNKS", "5"))
    max_chunk_chars: int = int(os.environ.get("MAX_CHUNK_CHARS", "1200"))

settings = Settings()


