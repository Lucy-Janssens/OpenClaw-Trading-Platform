from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "OpenClaw Trading API is live"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_trades():
    r = client.get("/trades")
    assert r.status_code == 200
    data = r.json()
    assert "trades" in data
    assert len(data["trades"]) == 2


def test_markets():
    r = client.get("/markets")
    assert r.status_code == 200
    data = r.json()
    assert "markets" in data
    assert len(data["markets"]) == 2
