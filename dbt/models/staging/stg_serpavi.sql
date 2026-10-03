select
	district_code,
	case metric
		when 'BI_ALVHEPCO' 	then 'lease_count'
		when 'ALQM2_LV'		then 'rent_eur_per_m2_month'
		when 'ALQTBID12'	then 'rent_eur_month'
		when 'SLVM2'		then 'surface_m2'
	end as measure,
	case statistic
		when 'M' 	then 'median'
		when '25'	then 'p25'
		when '75'	then 'p75'
	end as statistic,
	housing_type,
	year,
	value
from {{ source('raw', 'serpavi_long') }}
