select district_code, year
from {{ ref('mart_district_affordability')}}
where year = 2023 and (
	(district_code = '0801905' and rent_index_real not between 121.9 and 122.3)
	or (district_code = '0801904' and income_index_real not between 105.8 and 106.2)
	or (district_code = '0801902' and rent_to_income_ratio not between 0.233 and 0.236)
)
