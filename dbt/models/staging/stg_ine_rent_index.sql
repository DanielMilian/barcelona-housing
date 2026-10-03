with latest as (
	select payload
	from {{ source('raw', 'ine_raw')}}
	where source_label = 'rent_index_districts'
	order by extract_date desc
	limit 1
),

series as (
	select s ->> 'Nombre' as series_name, s -> 'Data' as points
	from latest, jsonb_array_elements(payload -> 'series') as s
),

parsed as (
	select
		'08019'  || substring(split_part(series_name, '. ', 1) from '\d+$') as district_code,
		split_part(series_name, '. ', 2) as measure_raw,
		split_part(series_name, '. ', 3) as breakdown,
		points
	from series
	)

select
	district_code,
	case measure_raw
		when 'Index'		then 'index'
		when 'Annual variation'	then 'annual_variation_pct'
	end as measure,
	breakdown,
	(p ->> 'Anyo')::int		as year,
	(p ->> 'FK_Periodo')::int	as period_id,
	(p ->> 'Valor')::numeric	as value
from parsed, jsonb_array_elements(points) as p
