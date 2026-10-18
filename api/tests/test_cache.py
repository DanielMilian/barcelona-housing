from sqlalchemy import event

import app.main as main
from app.db import engine


def _count_queries():
    calls = []

    def count(conn, cursor, statement, *a):
        calls.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    return calls, lambda: event.remove(engine, "before_cursor_execute", count)


def test_second_call_skips_db(client):
    calls, stop = _count_queries()
    try:
        client.get("/meta/freshness")
        first = len(calls)
        client.get("/meta/freshness")
    finally:
        stop()
    assert first >= 1
    assert len(calls) == first


def test_table_stats_expire(client, monkeypatch):
    monkeypatch.setattr(main, "TABLES_TTL", 0)
    calls, stop = _count_queries()
    try:
        client.get("/meta/freshness")
        first = len(calls)
        client.get("/meta/freshness")
    finally:
        stop()
    assert len(calls) > first


def test_airflow_result_is_cached(client, monkeypatch):
    n = []
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: n.append(1) or [])
    client.get("/meta/freshness")
    client.get("/meta/freshness")
    assert len(n) == 1


def test_airflow_failure_is_not_cached_long(client, monkeypatch):
    n = []
    monkeypatch.setattr(main, "AIRFLOW_FAIL_TTL", 0)
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: n.append(1) or None)
    client.get("/meta/freshness")
    client.get("/meta/freshness")
    assert len(n) == 2


def test_pipeline_runs_is_never_cached(client, monkeypatch):
    n = []
    monkeypatch.setattr(main, "fetch_dag_runs", lambda *a, **k: n.append(1) or [])
    client.get("/pipeline/runs")
    client.get("/pipeline/runs")
    assert len(n) == 2
