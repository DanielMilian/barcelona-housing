select district_code, count(*) as n
from {{ ref('mart_district_affordability')}}
group by 1
having count(*) <> 9

union all

select 'district_count', count(distinct district_code)
from {{ ref('mart_district_affordability')}}
having count(distinct district_code) <> 10
