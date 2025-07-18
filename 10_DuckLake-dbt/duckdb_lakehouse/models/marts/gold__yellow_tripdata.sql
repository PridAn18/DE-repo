{{ config(materialized='view') }}

SELECT
    VendorID,
    PULocationID,
    payment_type,
    COUNT(*) AS trip_count,
    AVG(trip_distance) AS avg_trip_distance,
    SUM(fare_amount) AS total_fare,
    SUM(tip_amount) AS total_tip

FROM {{ ref('silver__yellow_tripdata') }}
GROUP BY VendorID, PULocationID, payment_type
ORDER BY total_fare DESC
