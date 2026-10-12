import pytest


def test_eixample_2023_values(client):
    r = client.get("/districts/2/affordability", params={"year_from": 2023})
    assert r.status_code == 200
    (row,) = r.json()
    assert row["year"] == 2023
    assert row["income_eur"] == pytest.approx(51637.0)
    assert row["rent_eur_month"] == pytest.approx(1008.33)
    assert row["rent_eur_m2_median"] == pytest.approx(13.67)
    assert row["rent_to_income_ratio"] == pytest.approx(0.2343, abs=1e-4)


def test_row_counts(client):
    assert len(client.get("/districts/2/affordability").json()) == 9
    assert len(client.get("/districts/2/affordability", params={"year_from": 2022}).json()) == 2
    assert len(client.get("/affordability", params={"year": 2023}).json()) == 10


def test_ratio_matches_inputs(client):
    rows = client.get("/affordability", params={"year": 2023}).json()
    for r in rows:
        assert r["rent_to_income_ratio"] == pytest.approx(
            r["rent_eur_month"] * 12 / r["income_eur"], abs=1e-3
        )


def test_sorting(client):
    rows = client.get(
        "/affordability",
        params={"year": 2023, "sort_by": "rent_eur_month", "order": "asc"},
    ).json()
    values = [r["rent_eur_month"] for r in rows]
    assert values == sorted(values)


@pytest.mark.parametrize(
    "path,params,status",
    [
        ("/districts/99/affordability", {}, 404),
        ("/districts/2/affordability", {"year_from": 2023, "year_to": 2020}, 422),
        ("/affordability", {"year": 2030}, 422),
        ("/affordability", {}, 422),
        ("/affordability", {"year": 2023, "sort_by": "drop_table"}, 422),
    ],
)
def test_errors(client, path, params, status):
    assert client.get(path, params=params).status_code == status
