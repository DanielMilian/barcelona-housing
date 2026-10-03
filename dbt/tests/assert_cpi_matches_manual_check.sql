select year, cpi_avg
from {{ ref('fct_cpi_annual')}}
where (year = 2015 and cpi_avg <> 79.185)
	or (year = 2023 and cpi_avg <> 94.897)
