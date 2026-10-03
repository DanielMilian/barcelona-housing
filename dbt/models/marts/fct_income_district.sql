select district_code, indicator, year, value
from {{ ref('stg_ine_income')}}
where geo_level = 'district'
