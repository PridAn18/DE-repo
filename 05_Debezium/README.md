План проекта:
Поднять Kafka через KRaft, 
Реализовать CDC стриминг Kafka Connect используя Debezium и ClickHouseSinkConnector

Поднимаем инфраструктуру
```bash
docker compose up -d
```

Инфраструктура состоит из postgreSQL, Kafka, Debezium для чтения изменений с PostgreSQL и отправки в Kafka

Заходим в контейнер с PostgreSQL

```bash
docker exec -it f020cd316c12 /bin/sh
```

Заходим в PostgreSQL и создаём таблицу 

```psql
psql -U docker -d exampledb -W
Password: docker
```

```SQL
CREATE TABLE student (id primary key, name varchar)
ALTER TABLE public.student REPLICA IDENTITY full
```

Отправим запрос на создание PostgreSQL коннектора, однако лучше использовать логическую репликацию в PostgreSQL и плагин 'pgoutput' для отслеживания только изменений, а не полных снимков таблицы, и создания топика dbserver1.public.student

Создадим таблицу для сырых данных 
```ClickHouse
CREATE TABLE raw_cdc_student (
    raw String
) ENGINE = MergeTree()
ORDER BY tuple();
```
```Bash
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "docker",
    "database.password": "docker",
    "database.dbname": "exampledb",
    "database.server.name": "dbserver1",
    "table.whitelist": "public.student",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false"
  }
}' http://localhost:8083/connectors
```

Зарегистрируем ClickHouseSinkConnector 
```bash 
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "clickhouse-sink",
  "config": {
    "connector.class": "com.clickhouse.kafka.connect.ClickHouseSinkConnector",
    "tasks.max": "1",
    "topics": "dbserver1.public.student",
    
    "hostname": "clickhouse",
    "clickhouse.port": "8123",
    "clickhouse.protocol": "http",
    "clickhouse.database": "default",
    "clickhouse.table.name": "raw_cdc_student",
    "clickhouse.user": "admin",
    "clickhouse.password": "admin",

    "clickhouse.fields": "raw",
    "clickhouse.fields.mapping": "raw=value",

    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false"
  }
}' http://localhost:8083/connectors
```

Теперь при изменении, вставке, удалении данных в Postgres данные попадут в ClickHouse