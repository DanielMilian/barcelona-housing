with latest as (
	select payload
	from {{ source('raw', 'ine_raw')}}
	where source_label = 'cpi_province'
	order by extract_date desc
	limit 1
),

series as (
	select s -> 'Data' as points
	from latest, jsonb_array_elements(payload -> 'series') as s
)

select
	(p ->> 'Anyo')::int		as year,
	(p ->> 'FK_Periodo')::int	as month,
	(p ->> 'Valor')::numeric	as cpi_index
from series, jsonb_array_elements(points) as p
