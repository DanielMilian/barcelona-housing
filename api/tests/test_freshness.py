from app.main import FRESHNESS_TABLES

def test_freshness_ok(client):
    r = client.get("/meta/freshness")
    assert r.status_code == 200
    assert set(r.json()) == set(FRESHNESS_TABLES)

def test_freshness_mart_value(client):
    mart = client.get("/meta/freshness").json()["mart_district_affordability"]
    assert mart == {"min_year": 2015, "max_year": 2023, "row_count": 90}

def test_freshness_no_empty_tables(client):
    for name, v in client.get("/meta/freshness").json().items():
        assert v["row_count"] > 0, name
        assert v["max_year"] is not None, name


