Поднимаем s3

```bash
docker compose up -d
```

python3 -m venv venv

source venv/bin/activate

pip install duckdb

вручную или другим способом создать бакет lake и загрузить файл yellow_tripdata_2025-05.parquet

запускаем duckdb cli

`
duckdb ./lakehouse.duckdb

проверяем чтение из s3

INSTALL httpfs;
LOAD httpfs;

SET s3_region='us-east-1';
SET s3_endpoint='localhost:9000';
SET s3_access_key_id='minioadmin';
SET s3_secret_access_key='minioadmin';
SET s3_url_style='path';
SET s3_use_ssl=false;

SELECT * FROM 's3://lake/yellow_tripdata_2025-05.parquet' LIMIT 10;


dbt run --select tag:staging --vars '{"year": "2025", "month": "05"}' JINJA
