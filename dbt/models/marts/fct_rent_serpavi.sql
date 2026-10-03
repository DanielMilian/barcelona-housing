select
	district_code,
	year,
	max(value) filter (where measure = 'rent_eur_month' and statistic = 'median')		as rent_eur_month_median,
	max(value) filter (where measure = 'rent_eur_per_m2_month' and statistic = 'median')	as rent_eur_m2_median,
	max(value) filter (where measure = 'lease_count')					as lease_count
from {{ ref('stg_serpavi')}}
where housing_type = 'VC'
group by district_code, year
