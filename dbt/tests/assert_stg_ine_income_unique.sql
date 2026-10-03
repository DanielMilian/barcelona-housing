select geo_level, district_code, indicator, year, count(*) as n
from {{ ref('stg_ine_income')}}
group by 1, 2, 3, 4
having count(*) > 1
