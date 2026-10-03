select
	district_code,
	year,
	max(value) filter (where measure = 'index')			as rent_index,
	max(value) filter (where measure = 'annual_variation_pct')	as rent_annual_variation_pct,
from {{ ref('stg_ine_rent_index')}}
group by district_code, year


