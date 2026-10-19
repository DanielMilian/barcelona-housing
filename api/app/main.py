import logging
import os
import httpx
from enum import Enum
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import District, Affordability, Freshness, DagRun
from .auth import require_api_key
from .limits import limiter
from .cache import cache
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Barcelona housing API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
@limiter.exempt
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


TABLES_TTL = 300
AIRFLOW_OK_TTL = 20
AIRFLOW_FAIL_TTL = 5


def table_stats(db: Session) -> dict:
    out, hit = cache.get("tables")
    if hit:
        return out
    out = {}
    for t in FRESHNESS_TABLES:
        row = db.execute(text(
                          f"select min(year) as min_year, max(year) as max_year, count(*) as row_count "
                          f"from analytics.{t}"
        )).one()
        out[t] = {"min_year": row.min_year, "max_year": row.max_year, "row_count": row.row_count}
    cache.set("tables", out, TABLES_TTL)
    return out


def last_success_run():
    runs, hit = cache.get("airflow")
    if not hit:
        runs = fetch_dag_runs(1, state="success", timeout=2.0)
        # a failure is cached briefly so a recovered Airflow shows up fast
        cache.set("airflow", runs, AIRFLOW_OK_TTL if runs is not None else AIRFLOW_FAIL_TTL)
    return runs


@app.get("/meta/freshness", response_model=Freshness, dependencies=AUTH)
def freshness(db: Session = Depends(get_db)):
    tables = table_stats(db)
    runs = last_success_run()
    return {
            "tables": tables,
            "pipeline": {
                "airflow_reachable": runs is not None,
                "last_successful_run": runs[0] if runs else None,
                }
            }


AIRFLOW_URL = os.environ.get("AIRFLOW_API_URL", "http://airflow-webserver:8080")
AIRFLOW_AUTH = (os.environ.get("AIRFLOW_API_USER", ""), os.environ.get("AIRFLOW_API_PASSWORD", ""))
DAG_ID = "housing_pipeline"



def fetch_dag_runs(limit: int, state: str | None = None, timeout: float = 5.0) -> list[dict] | None:
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
    try:
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
    except (KeyError, TypeError, ValueError) as e:
        logger.warning("airflow response malformed: %r", e)
        return None


@app.get("/pipeline/runs", response_model=list[DagRun], dependencies=AUTH)
@limiter.limit("10/minute")
def pipeline_runs(request: Request, limit: int = Query(5, ge=1, le=50)):
    runs = fetch_dag_runs(limit)
    if runs is None:
        raise HTTPException(status_code=502, detail="airflow unavailable")
    return runs
