SELECT country_code, country_name, {{ add_load_datetime() }}
FROM {{ ref('stg_countries') }}