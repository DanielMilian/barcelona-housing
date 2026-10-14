import pytest
import app.main as main


@pytest.fixture(autouse=True)
def no_airflow(monkeypatch):
    # default: Airflow unreachable, so these tests never touch the network
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: None)


def test_freshness_ok(client):
    r = client.get("/meta/freshness")
    assert r.status_code == 200
    assert set(r.json()["tables"]) == set(main.FRESHNESS_TABLES)


def test_freshness_mart_value(client):
    mart = client.get("/meta/freshness").json()["tables"]["mart_district_affordability"]
    assert mart == {"min_year": 2015, "max_year": 2023, "row_count": 90}


def test_freshness_no_empty_tables(client):
    for name, v in client.get("/meta/freshness").json()["tables"].items():
        assert v["row_count"] > 0, name
        assert v["max_year"] is not None, name


def test_freshness_pipeline_ok(client, monkeypatch):
    run = {"run_id": "r1", "state": "success", "run_type": "manual",
           "start_date": "s", "end_date": "e"}
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: [run])
    p = client.get("/meta/freshness").json()["pipeline"]
    assert p == {"airflow_reachable": True, "last_successful_run": run}


def test_freshness_airflow_down(client):
    r = client.get("/meta/freshness")
    assert r.status_code == 200
    assert r.json()["pipeline"] == {"airflow_reachable": False, "last_successful_run": None}
