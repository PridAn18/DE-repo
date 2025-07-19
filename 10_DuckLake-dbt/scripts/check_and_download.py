import re
import requests
from datetime import datetime
import boto3
import os

# Константы
S3_BUCKET = "lake"
S3_PREFIX = "yellow_tripdata/"
FILENAME_TEMPLATE = "yellow_tripdata_{year}-{month:02}.parquet"
S3_ENDPOINT_URL = "http://localhost:9000" 

def get_latest_s3_date():
    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
    )
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
    dates = []
    for obj in response.get('Contents', []):
        match = re.search(r'yellow_tripdata_(\d{4})-(\d{2})\.parquet', obj['Key'])
        if match:
            dates.append((int(match.group(1)), int(match.group(2))))
    if not dates:
        return None
    return max(dates)

def get_latest_available_on_web():
    today = datetime.today()

    
    lag_months = 2
    year = today.year
    month = today.month - lag_months

    while month <= 0:
        month += 12
        year -= 1

    return (year, month)

def file_exists(url: str) -> bool:
    r = requests.head(url)
    return r.status_code == 200

def run():
    s3_latest = get_latest_s3_date()
    print("Последняя дата в S3:", s3_latest)
    
    web_latest = get_latest_available_on_web()
    print("Доступная дата на сайте:", web_latest)

    if s3_latest == web_latest:
        print("Нет новых файлов для загрузки.")
        return

    year, month = web_latest
    filename = FILENAME_TEMPLATE.format(year=year, month=month)
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"

    # Проверка наличия файла на сервере
    if not file_exists(url):
        print(f"Файл ещё не выложен на сайт: {url}")
        return

    print(f"Скачиваем {url}...")
    r = requests.get(url)
    r.raise_for_status()

    with open(f"/tmp/{filename}", "wb") as f:
        f.write(r.content)

    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
    )

    key = f"{S3_PREFIX}year={year}/month={month:02}/{filename}"
    s3.upload_file(f"/tmp/{filename}", S3_BUCKET, key)
    print(f"Загружено в S3: {key}")
if __name__ == "__main__":
    run()
