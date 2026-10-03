select district_code
from (
	select district_code from {{ ref('stg_serpavi') }}
	union
	select district_code from {{ ref('stg_ine_income')}} where geo_level = 'district'
	union
	select district_code from {{ ref('stg_ine_rent_index')}}
) d
where district_code not in (select district_code from {{ ref('dim_district')}})
