import app.main as main

RUN = {"run_id": "r1", "state": "success", "run_type": "manual",
       "start_date": "s", "end_date": None}


def test_pipeline_runs_shape(client, monkeypatch):
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: [RUN])
    r = client.get("/pipeline/runs?limit=1")
    assert r.status_code == 200
    assert r.json() == [RUN]


def test_pipeline_runs_airflow_down_is_502(client, monkeypatch):
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: None)
    assert client.get("/pipeline/runs").status_code == 502


def test_openapi_documents_models(client):
    paths = client.get("/openapi.json").json()["paths"]
    ok = paths["/meta/freshness"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert ok["$ref"].endswith("/Freshness")


def test_year_bounds_follow_constants(client):
    assert client.get(f"/affordability?year={main.MIN_YEAR}").status_code == 200
    assert client.get(f"/affordability?year={main.MAX_YEAR}").status_code == 200
    assert client.get(f"/affordability?year={main.MIN_YEAR - 1}").status_code == 422
    assert client.get(f"/affordability?year={main.MAX_YEAR + 1}").status_code == 422
