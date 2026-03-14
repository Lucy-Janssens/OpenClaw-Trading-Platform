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
    # In CI, we might have 0 trades if migrations just ran.
    # Just check structure of first trade if any exist.
    if len(data["trades"]) > 0:
        t = data["trades"][0]
        assert "pair" in t
        assert "side" in t
        assert "reasoning" in t


def test_markets():
    r = client.get("/markets")
    assert r.status_code == 200
    data = r.json()
    assert "markets" in data
    # We always return at least an entry for BTC/USDT if ticker fetch works, 
    # but in CI it might fail due to restricted location (returning empty list).
    assert isinstance(data["markets"], list)
