with latest as (
	select payload
	from {{ source('raw', 'ine_raw')}}
	where source_label = 'income_adrh'
	order by extract_date desc
	limit 1
),

series as (
	select s ->> 'Nombre' as series_name, s -> 'Data' as points
	from latest, jsonb_array_elements(payload -> 'series') as s		
),

parsed as (
	select
		split_part(series_name, '. ', 1) as geography,
		split_part(series_name, '. ', 3) as indicator,
		points
	from series
)

select
	case when geography  ~ '^Barcelona district \d+$' then 'district' else 'municipality' end as geo_level,
   	case when geography ~ '^Barcelona district \d+$' then '08019' || substring(geography from '\d+$') end as district_code,
	indicator,
	(p ->> 'Anyo')::int		as year,
	(p ->> 'FK_Periodo')::int	as period_id,
	(p ->> 'Valor'):: numeric	as value
from parsed, jsonb_array_elements(points) as p
