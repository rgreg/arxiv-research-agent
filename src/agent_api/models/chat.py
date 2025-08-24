from pydantic import BaseModel, Field
from typing import List

class ChatRequest(BaseModel):
question: str = Field(..., min_length=3)
top_k: int = 5

class ChatResponse(BaseModel):
answer: str = "Not implemented"
citations: List[str] = []
