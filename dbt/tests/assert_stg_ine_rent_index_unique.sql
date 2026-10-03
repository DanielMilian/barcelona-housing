select district_code, measure, year, count(*) as n
from {{ ref('stg_ine_rent_index')}}
group by 1, 2, 3
having count(*) > 1
