from fastapi import FastAPI

app = FastAPI(title="ArXiv Research Agent (GCP)")

@app.get("/healthz")
def healthz():
    return {"ok": True}

