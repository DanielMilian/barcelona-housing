import httpx
import app.main as main

class FakeResp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                    "err",
                    request=httpx.Request("GET", "http://x"),
                    response=httpx.Response(self.status_code),
                    )
    def json(self):
        return self._payload

def test_runs_trims_fields(client, monkeypatch):
    payload = {"dag_runs": [{
        "dag_run_id": "r1", "state": "success", "run_type": "manual",
        "start_date": "2026-10-10T21:53:19+00:00", "end_date": "2026-10-10T21:53:51+00:00",
        "conf": {"secret": 1}, "note": "x",
        }]}
    monkeypatch.setattr(main.httpx, "get", lambda *a, **k: FakeResp(payload))
    r = client.get("/pipeline/runs?limit=1")
    assert r.status_code == 200
    assert r.json() == [{
        "run_id": "r1", "state": "success", "run_type": "manual",
        "start_date": "2026-10-10T21:53:19+00:00", "end_date": "2026-10-10T21:53:51+00:00",

        }]

def test_runs_airflow_down(client, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(main.httpx, "get", boom)
    r = client.get("/pipeline/runs")
    assert r.status_code == 502
    assert r.json() == {"detail": "airflow unavailable"}

def test_runs_limit_validation(client):
    assert client.get("/pipeline/runs?limit=0").status_code == 422
    assert client.get("/pipeline/runs?limit=51").status_code == 422

