SELECT DISTINCT country_code, country_name 
FROM {{ source('global_inflation_countries', 'global_inflation_countries')}}