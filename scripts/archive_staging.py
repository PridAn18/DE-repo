import re
import requests
from datetime import datetime
import boto3
from trino.dbapi import connect

# --- Константы ---
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

STAGING_TABLE = "yellow_tripdata"

def trino_connection(catalog=TRINO_ICEBERG_CATALOG, schema="default"):
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=catalog,
        schema=schema
    )

def get_oldest_s3_date():
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
    return min(dates) if dates else None

def get_previous_month(year, month):
    month -= 1
    if month <= 0:
        month += 12
        year -= 1
    return (year, month)

def file_exists(url: str) -> bool:
    r = requests.head(url)
    return r.status_code == 200

def download_to_raw(year, month, filename):
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"
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

def insert_into_staging_if_schema_matches(year, month, filename):
    conn = trino_connection(schema="staging")
    cur = conn.cursor()
    
    cur.execute(f"SHOW COLUMNS FROM {TRINO_ICEBERG_CATALOG}.staging.{STAGING_TABLE}")
    staging_cols = [row[0].lower() for row in cur.fetchall()]

    
    tmp_table = f"tmp_parquet_{year}_{month}"
    s3a_uri = f"s3a://{S3_BUCKET}/{RAW_PREFIX}year={year}/month={month:02}/"

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
        external_location = '{s3a_uri}',
        format = 'PARQUET'
    )
    """)

    
    cur.execute(f"SHOW COLUMNS FROM {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}")
    tmp_cols = [row[0].lower() for row in cur.fetchall()]

    if staging_cols == tmp_cols + ["year", "month"]:
        print("Схема совпадает — выполняем вставку в STAGING...")
        cur.execute(f"""
            INSERT INTO {TRINO_ICEBERG_CATALOG}.staging.{STAGING_TABLE}
            SELECT *, {year} AS year, {month} AS month
            FROM {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}
        """)
    else:
        print("ВНИМАНИЕ: схема не совпадает, пропускаем вставку (нужен алерт в Airflow)")

    cur.execute(f"DROP TABLE IF EXISTS {TRINO_HIVE_CATALOG}.{TRINO_HIVE_SCHEMA}.{tmp_table}")
    cur.close()
    conn.close()

def run():
    oldest = get_oldest_s3_date()
    if not oldest:
        print("RAW пуст — нечего догружать")
        return
    year, month = get_previous_month(*oldest)
    filename = FILENAME_TEMPLATE.format(year=year, month=month)
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"

    if not file_exists(url):
        print(f"Файл {filename} отсутствует на сайте")
        return

    download_to_raw(year, month, filename)
    insert_into_staging_if_schema_matches(year, month, filename)

if __name__ == "__main__":
    run()