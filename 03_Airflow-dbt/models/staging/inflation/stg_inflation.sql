SELECT country_code, region, sub_region, intermediate_region, indicator_code, indicator_name, year, inflation_rate
FROM {{ source('global_inflation_countries', 'global_inflation_countries')}}
WHERE inflation_rate != 0