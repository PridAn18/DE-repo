import sys
from trino.dbapi import connect

TRINO_HOST = "localhost"
TRINO_PORT = 8080
TRINO_USER = "etl"
CATALOG = "iceberg"
STAGING_SCHEMA = "staging"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA = "gold"
TABLE_NAME = "yellow_tripdata"

EXPECTED_COLUMNS = [
    "vendorid", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "ratecodeid", "store_and_fwd_flag",
    "pulocationid", "dolocationid", "payment_type", "fare_amount", "extra",
    "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "total_amount", "congestion_surcharge", "airport_fee", "cbd_congestion_fee",
    "year", "month"
]

def trino_connection(catalog=CATALOG, schema="default"):
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=catalog,
        schema=schema
    )

def get_columns_from_table(catalog, schema, table):
    conn = trino_connection(catalog=catalog, schema=schema)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT lower(column_name)
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{table}'
        ORDER BY ordinal_position
    """)
    cols = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return cols

def ensure_gold_schema_exists():
    conn = trino_connection(schema=GOLD_SCHEMA)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE SCHEMA IF NOT EXISTS iceberg.gold
        WITH (location = 's3a://datalake/gold')
        
    """)
    cur.close()
    conn.close()

def ensure_silver_table_exists():
    conn = trino_connection(schema=SILVER_SCHEMA)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            VendorID INTEGER,
            tpep_pickup_datetime TIMESTAMP,
            tpep_dropoff_datetime TIMESTAMP,
            passenger_count DOUBLE,
            trip_distance DOUBLE,
            RatecodeID DOUBLE,
            store_and_fwd_flag VARCHAR,
            PULocationID INTEGER,
            DOLocationID INTEGER,
            payment_type DOUBLE,
            fare_amount DOUBLE,
            extra DOUBLE,
            mta_tax DOUBLE,
            tip_amount DOUBLE,
            tolls_amount DOUBLE,
            improvement_surcharge DOUBLE,
            total_amount DOUBLE,
            congestion_surcharge DOUBLE,
            Airport_fee DOUBLE,
            cbd_congestion_fee DOUBLE,
            year INT,
            month INT
        )
        WITH (
            format = 'PARQUET',
            partitioning = ARRAY['year', 'month'],
            location = 's3://datalake/silver/yellow_tripdata'
        )
    """)
    cur.close()
    conn.close()

def merge_staging_to_silver():
    conn = trino_connection(schema=SILVER_SCHEMA)
    cur = conn.cursor()

    cur.execute(f"""
        SELECT DISTINCT year, month
        FROM {CATALOG}.{STAGING_SCHEMA}.{TABLE_NAME}
        EXCEPT
        SELECT DISTINCT year, month
        FROM {CATALOG}.{SILVER_SCHEMA}.{TABLE_NAME}
        ORDER BY year, month
    """)
    missing_months = cur.fetchall()

    if not missing_months:
        print("Новых месяцев для загрузки нет.")
        cur.close()
        conn.close()
        return

    print(f"Найдено {len(missing_months)} новых месяцев: {missing_months}")

    for year_val, month_val in missing_months:
        print(f"Обработка {year_val}-{str(month_val).zfill(2)}...")

        cur.execute(f"""
            MERGE INTO {TABLE_NAME} AS silver
            USING (
                SELECT *
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (
                               PARTITION BY vendorid, tpep_pickup_datetime, tpep_dropoff_datetime
                               ORDER BY tpep_pickup_datetime DESC
                           ) AS rn
                    FROM {CATALOG}.{STAGING_SCHEMA}.{TABLE_NAME}
                    WHERE year = {year_val} AND month = {month_val}
                ) t
                WHERE rn = 1
            ) AS staging
            ON silver.vendorid = staging.vendorid
               AND silver.tpep_pickup_datetime = staging.tpep_pickup_datetime
               AND silver.tpep_dropoff_datetime = staging.tpep_dropoff_datetime
            WHEN NOT MATCHED THEN
                INSERT (
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
                    year,
                    month
                )
                VALUES (
                    staging.VendorID,
                    staging.tpep_pickup_datetime,
                    staging.tpep_dropoff_datetime,
                    staging.passenger_count,
                    staging.trip_distance,
                    staging.RatecodeID,
                    staging.store_and_fwd_flag,
                    staging.PULocationID,
                    staging.DOLocationID,
                    staging.payment_type,
                    staging.fare_amount,
                    staging.extra,
                    staging.mta_tax,
                    staging.tip_amount,
                    staging.tolls_amount,
                    staging.improvement_surcharge,
                    staging.total_amount,
                    staging.congestion_surcharge,
                    staging.Airport_fee,
                    staging.cbd_congestion_fee,
                    staging.year,
                    staging.month
                )
        """)
        print(f"{year_val}-{str(month_val).zfill(2)} загружен в silver.")

    cur.close()
    conn.close()
def run():
    staging_cols = get_columns_from_table(CATALOG, STAGING_SCHEMA, TABLE_NAME)
    if staging_cols != EXPECTED_COLUMNS:
        print("Схема STAGING не соответствует эталонной. MERGE не выполнен.")
        print("Колонки в STAGING:", staging_cols)
        sys.exit(1)

    ensure_silver_table_exists()
    merge_staging_to_silver()

if __name__ == "__main__":
    run()