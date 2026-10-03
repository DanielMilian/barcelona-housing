select y
from generate_series(2015, 2023) as y
where y not in (select year from {{ ref('fct_cpi_annual')}})
