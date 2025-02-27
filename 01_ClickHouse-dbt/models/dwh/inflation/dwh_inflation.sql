SELECT 
    country_code, 
    region, 
    sub_region, 
    intermediate_region, 
    indicator_code, 
    indicator_name, 
    year, 
    inflation_rate,
    {{ add_load_datetime() }}
FROM 
    {{ ref('stg_inflation') }}