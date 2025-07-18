select
    1
from "lakehouse"."main"."silver__yellow_tripdata"

where not(fare_amount > 0)

  
  
      
    