import re
import requests
from datetime import datetime
import boto3
from trino.dbapi import connect

S3_BUCKET = "datalake"

RAW_PREFIX = "raw/yellow_tripdata/"
STAGING_LOCATION = f"s3://{S3_BUCKET}/staging/yellow_tripdata"

FILENAME_TEMPLATE = "yellow_tripdata_{year}-{month:02}.parquet"
S3_ENDPOINT_URL = "http://localhost:9000"
AWS_KEY = "minio"
AWS_SECRET = "minio123"

TRINO_HOST = "localhost"
TRINO_PORT = 8080
TRINO_USER = "etl"

TRINO_ICEBERG_CATALOG = "iceberg"
TRINO_HIVE_CATALOG = "hive"
TRINO_HIVE_SCHEMA = "default"

SCHEMAS = ["staging", "silver", "gold"]

def trino_connection(catalog=TRINO_ICEBERG_CATALOG, schema="default"):
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=catalog,
        schema=schema
    )

def get_latest_s3_date():
    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
    )
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=RAW_PREFIX)
    dates = []
    for obj in response.get('Contents', []):
        match = re.search(r'yellow_tripdata_(\d{4})-(\d{2})\.parquet', obj['Key'])
        if match:
            dates.append((int(match.group(1)), int(match.group(2))))
    return max(dates) if dates else None

def get_latest_available_on_web(lag_months=2):
    today = datetime.today()
    year = today.year
    month = today.month - lag_months
    while month <= 0:
        month += 12
        year -= 1
    return (year, month)

def file_exists(url: str) -> bool:
    r = requests.head(url)
    return r.status_code == 200

def ensure_schemas_exist():
    conn = trino_connection()
    cur = conn.cursor()
    for schema in SCHEMAS:
        print(f"Проверяем наличие схемы iceberg.{schema}...")
        cur.execute(f"""
            CREATE SCHEMA IF NOT EXISTS {TRINO_ICEBERG_CATALOG}.{schema}
            WITH (location = 's3://{S3_BUCKET}/{schema}')
        """)
    cur.close()
    conn.close()

def ensure_staging_table_exists():
    conn = trino_connection(schema="staging")
    cur = conn.cursor()
    print("Проверяем наличие таблицы iceberg.staging.yellow_tripdata...")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS yellow_tripdata (
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
            location = '{STAGING_LOCATION}'
        )
    """)
    cur.close()
    conn.close()

def insert_new_data(year, month):
    s3_prefix_path = f"{RAW_PREFIX}year={year}/month={month:02}/"
    s3a_uri_for_hive = f"s3a://{S3_BUCKET}/{s3_prefix_path}"
    tmp_table = f"tmp_parquet_{year}_{month}"

    conn = trino_connection(schema="staging")
    cur = conn.cursor()
    try:
        cur.execute(f"DROP TABLE IF EXISTS {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}")
        cur.execute(f"""
            CREATE TABLE {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table} (
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
                cbd_congestion_fee DOUBLE
            )
            WITH (
                external_location = '{s3a_uri_for_hive}',
                format = 'PARQUET'
            )
        """)
        cur.execute(f"""
            INSERT INTO {TRINO_ICEBERG_CATALOG}.staging.yellow_tripdata
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
                {year} AS year,
                {month} AS month
            FROM {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}
        """)
        print(f"INSERT {year}-{month} в Iceberg.staging.yellow_tripdata выполнен.")
    finally:
        cur.execute(f"DROP TABLE IF EXISTS {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}")
        cur.close()
        conn.close()

def run():
    ensure_schemas_exist()
    ensure_staging_table_exists()

    s3_latest = get_latest_s3_date()
    print("Последняя дата в RAW S3:", s3_latest)

    web_latest = get_latest_available_on_web()
    print("Доступная дата на сайте:", web_latest)

    if s3_latest == web_latest:
        print("Нет новых файлов для загрузки.")
        return

    year, month = web_latest
    filename = FILENAME_TEMPLATE.format(year=year, month=month)
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"

    if not file_exists(url):
        print(f"Файл ещё не выложен: {url}")
        return

    print(f"Скачиваем {url}...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    local_path = f"/tmp/{filename}"
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
    )
    key = f"{RAW_PREFIX}year={year}/month={month:02}/{filename}"
    s3.upload_file(local_path, S3_BUCKET, key)
    print(f"Загружено в RAW S3: {key}")

    insert_new_data(year, month)

if __name__ == "__main__":
    run()