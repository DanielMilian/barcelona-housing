with base as (
	select
		i.district_code,
		i.year,
		i.value			as income_eur,
		r.rent_eur_month_median	as rent_eur_month,
		r.rent_eur_m2_median,
		r.lease_count,
		ri.rent_index		as ine_rent_index,
		c.cpi_avg
	from {{ ref('fct_income_district')}} i
	join {{ ref('fct_rent_serpavi')}} r
		on r.district_code = i.district_code and r.year = i.year
	join {{ ref('fct_rent_index')}} ri
		on ri.district_code = i.district_code and ri.year = i.year
	join {{ ref('fct_cpi_annual')}} c
		on c.year = i.year
	where i.indicator = 'Average household net income'
		and i.year between 2015 and 2023
),

with_2015 as (
	select 
		*,
		max(income_eur)		filter (where year = 2015) over (partition by district_code) as income_2015,
		max(rent_eur_month)	filter (where year = 2015) over (partition by district_code) as rent_2015,
		max(cpi_avg)		filter (where year = 2015) over (partition by district_code) as cpi_2015
	from base
)

select
	w.district_code,
	d.district_name,
	w.year,
	w.income_eur,
	w.rent_eur_month,
	w.rent_eur_m2_median,
	w.lease_count,
	round(w.rent_eur_month * 12 / w.income_eur, 4)					as rent_to_income_ratio,
	w.ine_rent_index,
	round(w.cpi_avg / w.cpi_2015 * 100, 2)						as cpi_index_2015_100,
	round(w.income_eur / w.income_2015 * 100, 2)					as income_index_nominal,
	round(w.rent_eur_month / w.rent_2015 * 100, 2)					as rent_index_nominal,
	round((w.income_eur / w.income_2015) / (w.cpi_avg / w.cpi_2015) * 100, 2)	as income_index_real,
	round(w.rent_eur_month / w.rent_2015 / (w.cpi_avg / w.cpi_2015)* 100, 2)	as rent_index_real,
	round(w.ine_rent_index / (w.cpi_avg / w.cpi_2015), 2)				as ine_rent_index_real
from with_2015 w
join {{ ref('dim_district')}} d on d.district_code = w.district_code


