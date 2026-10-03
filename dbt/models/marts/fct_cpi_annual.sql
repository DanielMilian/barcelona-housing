select
	year,
	count(*)			as months_available,
	round(avg(cpi_index), 3)	as cpi_avg
from {{ ref('stg_ine_cpi')}}
group by year
having count(*) = 12

