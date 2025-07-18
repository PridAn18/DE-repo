{{ config(materialized='table') }}

SELECT
    VendorID,
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    RatecodeID,
    store_and_fwd_flag,
    PULocationID,
    DOLocationID,
    payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    congestion_surcharge,
    Airport_fee,
    cbd_congestion_fee,
    month,
    year,

    -- Расчёт длительности поездки
    ROUND(
        EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) / 60.0,
        2
    ) AS trip_duration_minutes,

    -- Категория тарифа
    CASE
        WHEN fare_amount > 50 THEN 'High'
        WHEN fare_amount > 20 THEN 'Medium'
        ELSE 'Low'
    END AS fare_category,

    -- Преобразованная дата поездки
    DATE(tpep_pickup_datetime) AS trip_date

FROM {{ ref('bronze__yellow_tripdata') }}
WHERE trip_distance > 0 AND fare_amount > 0