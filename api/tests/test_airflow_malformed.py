import pytest
import app.main as main


class FakeResp:
    def __init__(self, body=None, bad_json=False):
        self._body, self._bad = body, bad_json

    def raise_for_status(self):
        pass

    def json(self):
        if self._bad:
            raise ValueError("not json")
        return self._body


BAD = [
    FakeResp({}),                                      # KeyError: no dag_runs
    FakeResp([]),                                      # TypeError: list body
    FakeResp(None),                                    # TypeError: null body
    FakeResp({"dag_runs": [{"state": "success"}]}),    # KeyError: run missing fields
    FakeResp({"dag_runs": None}),                      # TypeError: iterating None
    FakeResp(bad_json=True),                           # ValueError: not JSON
]
IDS = ["no_key", "list_body", "null_body", "missing_fields", "runs_null", "bad_json"]


@pytest.mark.parametrize("resp", BAD, ids=IDS)
def test_pipeline_runs_malformed_body_is_502(client, monkeypatch, resp):
    monkeypatch.setattr(main.httpx, "get", lambda *a, **k: resp)
    assert client.get("/pipeline/runs").status_code == 502


@pytest.mark.parametrize("resp", BAD, ids=IDS)
def test_freshness_malformed_body_degrades(client, monkeypatch, resp):
    monkeypatch.setattr(main.httpx, "get", lambda *a, **k: resp)
    r = client.get("/meta/freshness")
    assert r.status_code == 200
    assert r.json()["pipeline"]["airflow_reachable"] is False


def test_valid_body_still_parses(client, monkeypatch):
    run = {"run_id": "r1", "state": "success", "run_type": "manual",
           "start_date": "s", "end_date": None}
    body = {"dag_runs": [{"dag_run_id": "r1", "state": "success", "run_type": "manual",
                          "start_date": "s", "end_date": None}]}
    monkeypatch.setattr(main.httpx, "get", lambda *a, **k: FakeResp(body))
    r = client.get("/pipeline/runs")
    assert r.status_code == 200
    assert r.json() == [run]
