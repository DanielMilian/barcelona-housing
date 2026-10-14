def test_list_districts(client):
    r = client.get("/districts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10
    assert [d["district_number"] for d in data] == list(range(1, 11))


def test_get_district(client):
    r = client.get("/districts/2")
    assert r.status_code == 200
    assert r.json() == {
        "district_code": "0801902",
        "district_number": 2,
        "district_name": "Eixample",
    }


def test_unknown_district_404(client):
    assert client.get("/districts/99").status_code == 404


def test_bad_district_422(client):
    assert client.get("/districts/abc").status_code == 422
