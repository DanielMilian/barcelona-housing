from pydantic import BaseModel

class District(BaseModel):
    district_code: str
    district_number: int
    district_name: str


class Affordability(BaseModel):
    district_code: str
    district_name: str
    year: int
    income_eur: float | None
    rent_eur_month: float | None
    rent_eur_m2_median: float | None
    lease_count: int | None
    rent_to_income_ratio: float | None
    income_median_to_mean: float | None
    income_median_adj_eur_est: float | None
    rent_to_income_ratio_median_adj_est: float | None
    ine_rent_index: float | None
    cpi_index_2015_100: float | None
    income_index_nominal: float | None
    rent_index_nominal: float | None
    income_index_real: float | None
    rent_index_real: float | None
    ine_rent_index_real: float | None

class TableFreshness(BaseModel):
    min_year: int | None
    max_year: int | None
    row_count: int

class DagRun(BaseModel):
    run_id: str
    state: str
    run_type: str
    start_date: str | None
    end_date: str | None

class PipelineStatus(BaseModel):
    airflow_reachable: bool
    last_successful_run: DagRun | None

class Freshness(BaseModel):
    tables: dict[str, TableFreshness]
    pipeline: PipelineStatus
