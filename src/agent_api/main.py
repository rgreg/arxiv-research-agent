from fastapi import FastAPI
from src.agent_api.api.v1.chat import router as chat_router

app = FastAPI(title="ArXiv Research Agent (GCP)")
app.include_router(chat_router, prefix="/v1")

@app.get("/healthz")
def healthz():
    return {"ok": True}

