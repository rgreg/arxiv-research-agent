# src/agent_api/models/chat.py
from pydantic import BaseModel
from typing import List, Any, Optional

class ChatRequest(BaseModel):
    question: str
    k: Optional[int] = 5

class ChatResponse(BaseModel):
    answer: str
    citations: List[str]
    matches: List[Any]
