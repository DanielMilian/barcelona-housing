import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.limits import limiter


@pytest.fixture
def limited():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


def test_pipeline_runs_has_tighter_limit(client, limited, monkeypatch):
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: [])
    codes = [client.get("/pipeline/runs").status_code for _ in range(11)]
    assert codes[:10] == [200] * 10
    assert codes[10] == 429


def test_default_limit_applies(client, limited):
    codes = [client.get("/districts").status_code for _ in range(61)]
    assert codes[:60] == [200] * 60
    assert codes[60] == 429


def test_bad_keys_are_limited_too(limited):
    anon = TestClient(main.app)
    codes = [
        anon.get("/districts", headers={"X-API-Key": f"guess{i}"}).status_code
        for i in range(61)
    ]
    assert set(codes[:60]) == {401}
    assert codes[60] == 429


def test_health_is_exempt(client, limited):
    assert {client.get("/health").status_code for _ in range(65)} == {200}
