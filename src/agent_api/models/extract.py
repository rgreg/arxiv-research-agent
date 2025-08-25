from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ExtractRequest(BaseModel):
    id: Optional[str] = Field(None, description="Doc id in BigQuery table (id column)")
    text: Optional[str] = Field(None, description="Raw text to analyze if id not provided")
    title: Optional[str] = None

class ExtractResponse(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]

class SummarizeRequest(BaseModel):
    id: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    max_tokens: int = 256

class SummarizeResponse(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    summary: str
