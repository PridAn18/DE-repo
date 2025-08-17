# Iceberg Lakehouse Showcase

## Описание проекта
Демонстрационный проект Lakehouse-архитектуры на базе **Apache Iceberg**, **Trino** и **MinIO**.  
Цель — показать ключевые возможности Iceberg: time travel, schema evolution, snapshot management, инкрементальная загрузка и аналитические запросы.

Архитектура реализована в формате локального окружения с использованием **Docker Compose** и включает:
- **Trino** — SQL-движок для запросов к Iceberg
- **Hive Metastore** — каталог для регистрации таблиц Iceberg
- **MinIO** — S3-совместимое объектное хранилище для данных и метаданных Iceberg
- **PostgreSQL** — база Hive Metastore


## Основные возможности
- **RAW > STAGING > SILVER > GOLD** слойность хранения
- **Time Travel** — запрос данных на определённый момент времени
- **Список снапшотов** — историческая информация о состоянии таблицы
- **Schema Evolution** — безопасное добавление и удаление колонок
- **Инкрементальные загрузки** — дозагрузка новых партиций
- **DBT-модели** — создание GOLD-слоёв

## Setup

```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Launch

```bash
make start-trino
```

- **Trino** на порту 8080

- **Hive** Metastore на порту 9083

- **MinIO** (API: 9000, Console: 9001)

Заполнение слоёв:

```bash
python3 scripts/check_and_download.py

python3 scripts/silver_merge.py

cd dbt

dbt run --select gold.top_routes
```

Инкрементальная архивная подгрузка:

```bash
python3 scripts/archive_staging.py
```

## Trino

```bash
docker exec -it trino trino \
    --server http://localhost:8080 \
    --catalog iceberg \
    --schema staging 
```

Запросы с Iceberg features в iceberg/trino-cli-demo.sql