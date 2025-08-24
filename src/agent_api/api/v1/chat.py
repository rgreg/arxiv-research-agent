# src/agent_api/api/v1/chat.py
from fastapi import APIRouter, HTTPException
from src.agent_api.models.chat import ChatRequest, ChatResponse
from src.agent_api.core.rag_service import RAGService
from src.agent_api.core.config import settings

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.project or not settings.bq_table:
        raise HTTPException(status_code=500, detail="Server misconfigured: GCP_PROJECT / BQ_TABLE missing.")
    rag = RAGService()
    res = await rag.answer(req.question, k=req.k or 5)
    return ChatResponse(**res)
