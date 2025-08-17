SELECT * FROM staging.yellow_tripdata FOR VERSION AS OF 1048319503975208358 LIMIT 10; -- time travel - данные в снапшоте

SELECT * FROM staging."yellow_tripdata$history"; -- снапшоты

ALTER TABLE staging.yellow_tripdata ADD COLUMN trip_duration_minutes double; -- schema evolution

