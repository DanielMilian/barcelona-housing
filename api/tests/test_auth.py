import pytest
from fastapi.testclient import TestClient

import app.main as main

PROTECTED = [
    "/districts",
    "/districts/1",
    "/affordability?year=2023",
    "/meta/freshness",
    "/pipeline/runs",
]


@pytest.fixture(scope="module")
def anon():
    return TestClient(main.app)


@pytest.mark.parametrize("path", PROTECTED)
def test_no_key_is_401(anon, path):
    assert anon.get(path).status_code == 401


def test_wrong_key_is_401(anon):
    assert anon.get("/districts", headers={"X-API-Key": "nope"}).status_code == 401


def test_unconfigured_key_fails_closed(anon, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    assert anon.get("/districts", headers={"X-API-Key": "x"}).status_code == 503


def test_health_is_open(anon):
    assert anon.get("/health").status_code == 200
