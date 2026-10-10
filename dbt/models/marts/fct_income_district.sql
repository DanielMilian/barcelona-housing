select
    district_code,
    year,
    max(value) filter (where indicator = 'Average household net income')          as income_eur,
    max(value) filter (where indicator = 'Average income by unit of consumption') as income_cu_mean_eur,
    max(value) filter (where indicator = 'Median income by unit of consumption')  as income_cu_median_eur
from {{ ref('stg_ine_income') }}
where geo_level = 'district'
group by 1, 2
