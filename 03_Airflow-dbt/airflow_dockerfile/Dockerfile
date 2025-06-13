FROM apache/airflow:latest

COPY requirements.txt /

# Установка зависимостей один раз, под пользователем root
USER root
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk 

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    pip install apache-airflow-providers-clickhouse clickhouse-driver && \ 
    pip install dbt-core dbt-clickhouse # Установка dbt, если нужно


# Переключаемся на пользователя airflow после установки всех зависимостей
USER airflow

# [Опционально] Копирование других файлов, например, DAGs
COPY dags /opt/airflow/dags