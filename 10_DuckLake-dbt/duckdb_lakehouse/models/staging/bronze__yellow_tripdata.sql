{{ config(materialized='table') }}

{% set year = var('year', '2025') %}
{% set month = var('month', '04') %}

SELECT *
FROM read_parquet(
  's3://lake/yellow_tripdata/year={{ year }}/month={{ month }}/yellow_tripdata_{{ year }}-{{ month }}.parquet'
)