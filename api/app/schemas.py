from pydantic import BaseModel

class District(BaseModel):
    district_code: str
    district_number: int
    district_name: str
