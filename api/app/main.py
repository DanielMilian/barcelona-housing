from enum import Enum
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import District, Affordability

app = FastAPI(title="Barcelona housing API")

@app.get("/districts", response_model=list[District])
def list_district(db: Session = Depends(get_db)):
    rows = db.execute(
            text("""SELECT district_code, district_number, district_name 
                 FROM analytics.dim_district 
                 ORDER BY district_number""")
            ).mappings().all()
    return [dict(r) for r in rows]

@app.get("/districts/{district_number}", response_model=District)
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

@app.get("/districts/{district_number}/affordability", response_model=list[Affordability])
def district_affordability(
        district_number: int,
        year_from: int = Query(2015, ge=2015, le=2023),
        year_to: int = Query(2023, ge=2015, le=2023),
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

@app.get("/affordability", response_model=list[Affordability])
def affordability_by_year(
        year: int = Query(..., ge=2015, le=2023),
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


@app.get("/meta/freshness")
def freshness(db: Session = Depends(get_db)):
    out = {}
    for t in FRESHNESS_TABLES:
        row = db.execute(text(
                          f"select min(year) as min_year, max(year) as max_year, count(*) as row_count "
                          f"from analytics.{t}"
        )).one()
        out[t] = {"min_year": row.min_year, "max_year": row.max_year, "row_count": row.row_count}
    return out
