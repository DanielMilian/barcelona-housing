import logging
import os
import httpx
from enum import Enum
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import District, Affordability, Freshness, DagRun
from .auth import require_api_key

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Barcelona housing API")

MIN_YEAR, MAX_YEAR = 2015, 2023
AUTH = [Depends(require_api_key)]


@app.get("/districts", response_model=list[District], dependencies=AUTH)
def list_district(db: Session = Depends(get_db)):
    rows = db.execute(
            text("""SELECT district_code, district_number, district_name 
                 FROM analytics.dim_district 
                 ORDER BY district_number""")
            ).mappings().all()
    return [dict(r) for r in rows]

@app.get("/districts/{district_number}", response_model=District, dependencies=AUTH)
def get_district(district_number: int, db: Session = Depends(get_db)):
    row = db.execute(
            text(
                """
                SELECT district_code, district_number, district_name
                FROM analytics.dim_district
                WHERE district_number = :n
                """
                ),
            {"n": district_number},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"District {district_number} not found")
    return dict(row)

# Affordability
AFFORD_COLS = ", ".join(f"m.{c}" for c in Affordability.model_fields)

class SortBy(str, Enum):
    rent_to_income_ratio = "rent_to_income_ratio"
    income_eur = "income_eur"
    rent_eur_month = "rent_eur_month"
    rent_eur_m2_median = "rent_eur_m2_median"
    income_index_real = "income_index_real"
    rent_index_real = "rent_index_real"

class Order(str, Enum):
    asc = "asc"
    desc = "desc"

@app.get("/districts/{district_number}/affordability", response_model=list[Affordability], dependencies=AUTH)
def district_affordability(
        district_number: int,
        year_from: int = Query(MIN_YEAR, ge=MIN_YEAR, le=MAX_YEAR),
        year_to: int = Query(MAX_YEAR, ge=MIN_YEAR, le=MAX_YEAR),
        db: Session = Depends(get_db),
        ):
    if year_from > year_to:
        raise HTTPException(status_code=422, detail="year_from must be <= year_to")

    exists = db.execute(
            text("""SELECT 1 FROM analytics.dim_district
                 WHERE district_number = :n"""),
            {"n": district_number},
            ).first()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"District {district_number} not found")

    rows = db.execute(
            text(f"""
            SELECT {AFFORD_COLS}
            FROM analytics.mart_district_affordability m
            JOIN analytics.dim_district d ON d.district_code = m.district_code
            WHERE d.district_number = :n AND m.year BETWEEN :a AND :b
            ORDER BY m.year
            """),
            {"n": district_number, "a": year_from, "b": year_to},
            ).mappings().all()
    return [dict(r) for r in rows]

@app.get("/affordability", response_model=list[Affordability], dependencies=AUTH)
def affordability_by_year(
        year: int = Query(..., ge=MIN_YEAR, le=MAX_YEAR),
        sort_by: SortBy = SortBy.rent_to_income_ratio,
        order: Order = Order.desc,
        db: Session = Depends(get_db),
        ):
    rows = db.execute(
            text(f"""
            SELECT {AFFORD_COLS}
            FROM analytics.mart_district_affordability m
            WHERE m.year = :y
            ORDER BY m.{sort_by.value} {order.value} NULLS LAST
            """),
            {"y": year},
            ).mappings().all()
    return [dict(r) for r in rows]

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("select 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}

FRESHNESS_TABLES = (
        "fct_cpi_annual",
        "fct_income_district",
        "fct_rent_index",
        "fct_rent_serpavi",
        "mart_district_affordability",
        )


@app.get("/meta/freshness", response_model=Freshness, dependencies=AUTH)
def freshness(db: Session = Depends(get_db)):
    out = {}
    for t in FRESHNESS_TABLES:
        row = db.execute(text(
                          f"select min(year) as min_year, max(year) as max_year, count(*) as row_count "
                          f"from analytics.{t}"
        )).one()
        out[t] = {"min_year": row.min_year, "max_year": row.max_year, "row_count": row.row_count}
    runs = fetch_dag_runs(1, state="success", timeout=2.0)
    return {
            "tables": out,
            "pipeline": {
                "airflow_reachable": runs is not None,
                "last_successful_run": runs[0] if runs else None,
                }
            }


AIRFLOW_URL = os.environ.get("AIRFLOW_API_URL", "http://airflow-webserver:8080")
AIRFLOW_AUTH = (os.environ.get("AIRFLOW_API_USER", ""), os.environ.get("AIRFLOW_API_PASSWORD", ""))
DAG_ID = "housing_pipeline"



def fetch_dag_runs(limit: int, state:str | None = None, timeout: float = 5.0) -> list[dict] | None:
    params = {"limit": limit, "order_by": "-execution_date"}
    if state:
        params["state"] = state
    try:
        r = httpx.get(
                f"{AIRFLOW_URL}/api/v1/dags/{DAG_ID}/dagRuns",
                params=params, auth=AIRFLOW_AUTH, timeout=timeout,
                )
        r.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("airflow call failed: %s", e)
        return None
    return [
            {
                "run_id": d["dag_run_id"],
                "state": d["state"],
                "run_type": d["run_type"],
                "start_date": d["start_date"],
                "end_date": d["end_date"],
                }
            for d in r.json()["dag_runs"]
            ]

@app.get("/pipeline/runs", response_model=list[DagRun], dependencies=AUTH)
def pipeline_runs(limit: int = Query(5, ge=1, le=50)):
    runs = fetch_dag_runs(limit)
    if runs is None:
        raise HTTPException(status_code=502, detail="airflow unavailable")
    return runs
