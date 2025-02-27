# 01_ClickHouse-dbt

# Проект dbt для ClickHouse

## Описание проекта

Этот проект предназначен для работы с ClickHouse и dbt (data build tool). Он включает создание моделей для обработки данных и применение тестов для обеспечения качества данных.

## Стек технологий

- **ClickHouse**: Система управления базами данных, оптимизированная для аналитических запросов.
- **dbt**: Инструмент для трансформации данных, который позволяет создавать модели, управлять версиями и тестировать данные.
- **Kaggle**: Платформа для анализа данных, откуда были загружены наборы данных.

## Установка и настройка

1. **Установите ClickHouse**:
   - Следуйте [официальной документации ClickHouse](https://clickhouse.com/docs/en/install/) для установки ClickHouse на вашей локальной машине.

2. **Установите dbt**:
   - Убедитесь, что у вас установлен Python. Затем выполните:
     

```bash
python3 -m venv venv
source venv/bin/activate
```
```bash
python -m pip install dbt-core dbt-clickhouse
```

2. **Создайте новый dbt project**:
    - Укажите название проекта, базу данных:
```bash
dbt init
```

3. **Настройте соединение с ClickHouse**:
   - Создайте файл profiles.yml в директории ~/.dbt/ и добавьте следующее содержимое, заменив параметры на свои:
     
```yaml
inf:
  target: dev
  outputs:
    dev:
      type: clickhouse
      host: localhost # Или ваш IP-адрес
      port: 9000       # Порт, который слушает ClickHouse
      user: default    # Имя пользователя ClickHouse
```     

4. **Загрузите данные из Kaggle**:

   - Загрузите необходимые наборы данных из Kaggle и импортируйте их в ClickHouse. Вы можете использовать утилиты командной строки ClickHouse или SQL-запросы для загрузки данных.

  ```bash
  curl -L -o ~/Downloads/global-inflation-rate-1960-present.zip\
  https://www.kaggle.com/api/v1/datasets/download/fredericksalazar/global-inflation-rate-1960-present
  ```

## Структура проекта

- **data/**
  - Папка с csv файлом для загрузки и DDL для таблицы в ClickHouse.

- **macros/**
  - Макрос для генерации времени загрузки.

- **models/**
  - **stg_inflation.sql**: Модель для загрузки и трансформации данных по инфляции.
  - **stg_countries.sql**: Модель для загрузки и трансформации данных по странам.
  - **dwh_inflation.sql**: Финальная модель для анализа данных по инфляции.
  - **dwh_countries.sql**: Финальная модель для анализа данных по странам.

- **tests/**
  - Тесты, связанные с моделями, которые проверяют качество загруженных данных и отсутствие дубликатов.

## Использование макросов

В проекте используется макрос add_load_datetime для генерации времени загрузки. 

## dbt-utils

Добавьте зависимость в ваш файл packages.yml:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
```
Затем выполните команду:

```bash
dbt deps
```
## Запуск проекта

1. Запустите команду для сборки моделей staging:
   
```bash
dbt run --select tag:staging
```   


2. Запустите тесты для проверки качества данных staging:
   
```bash
dbt test --select tag:staging
```   

3. Запустите команду для сборки моделей dwh:

```bash
dbt run --select tag:dwh
```   


