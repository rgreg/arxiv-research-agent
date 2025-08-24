# arxiv-research-agent (GCP-only)

GCP-native arXiv Research Agent with Vertex AI (Gemini, Text Embeddings, Vector Search) and Cloud Run.

## Modules
1) Env setup & data ingestion (GCS + Workbench)
2) Processing & embeddings (Vertex text-embedding-004)
3) Vertex AI Vector Search indexing
4) RAG core logic (embed → search → Gemini)
5) FastAPI on Cloud Run

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GCP_PROJECT=your-project
export GCP_REGION=us-central1
export VERTEX_LOCATION=us-central1
export GCS_BUCKET=your-bucket
export GEMINI_MODEL=gemini-1.5-flash
export EMBED_MODEL=text-embedding-004
uvicorn src.agent_api.main:app --reload --port 8000
# open http://127.0.0.1:8000/healthz
