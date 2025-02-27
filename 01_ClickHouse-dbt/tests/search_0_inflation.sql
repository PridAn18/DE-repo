-- the search for zero inflation, as the dataset
-- shows the absence of inflation data

select
    country_code,
    inflation_rate
from {{ ref('stg_inflation') }}
where inflation_rate = 0