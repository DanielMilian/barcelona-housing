from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import District

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
