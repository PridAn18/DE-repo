{{ config(materialized='table') }}

with cleaned as (
    select
        vendorid,
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        passenger_count,
        trip_distance,
        pulocationid,
        dolocationid,
        fare_amount,
        tip_amount,
        total_amount,
        regexp_extract(store_and_fwd_flag, '^[YN]$', 0) as store_flag_clean
    from {{ source('silver', 'yellow_tripdata') }}
    where trip_distance > 0.5
      and total_amount > 0
      and passenger_count >= 1
),

agg as (
    select
        pulocationid,
        dolocationid,
        count(*) as trip_count,
        avg(total_amount) as avg_total_amount,
        avg(tip_amount) as avg_tip_amount,
        avg(total_amount + tip_amount) as avg_total_with_tips
    from cleaned
    group by pulocationid, dolocationid
),

ranked as (
    select
        *,
        rank() over (
            order by avg_total_with_tips desc
        ) as rnk
    from agg
)

select
    pulocationid,
    dolocationid,
    trip_count,
    round(avg_total_amount, 2) as avg_total_amount,
    round(avg_tip_amount, 2) as avg_tip_amount,
    round(avg_total_with_tips, 2) as avg_total_with_tips,
    rnk
from ranked
where rnk <= 10
order by rnk