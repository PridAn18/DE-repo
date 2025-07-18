select
    1
from "lakehouse"."main"."silver__yellow_tripdata"

where not(tpep_dropoff_datetime >= tpep_pickup_datetime)
