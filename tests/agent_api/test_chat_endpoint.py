from fastapi.testclient import TestClient
from src.agent_api.main import app

def test_health():
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_chat_not_implemented_yet():
    c = TestClient(app)
    r = c.post("/v1/chat", json={"question": "hi", "top_k": 3})
    assert r.status_code in (404, 501)
