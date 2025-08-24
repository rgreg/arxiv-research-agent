from fastapi import APIRouter, HTTPException
from src.agent_api.models.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
# Will be implemented in Modules 3-4
raise HTTPException(status_code=501, detail="RAG not implemented yet.")
