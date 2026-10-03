select year, month, count(*) as n
from {{ ref('stg_ine_cpi')}}
group by 1, 2 
having count(*) > 1
