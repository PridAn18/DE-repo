
# DuckLake: Аналитический пайплайн с DuckDB, dbt и S3 (MinIO)

Этот проект демонстрирует полный цикл аналитической обработки данных такси (Yellow Taxi NYC) с использованием:

* **MinIO (S3-совместимое хранилище)**
* **Python скриптов для ETL**
* **DuckDB как lakehouse хранилища**
* **dbt для трансформаций данных**
* **GitHub Actions с self-hosted runner для автоматизации**

---

### 1. Поднимаем локальное S3-хранилище (MinIO)

```bash
docker compose up -d
```

### 2. Создаём виртуальное окружение и устанавливаем зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Создаём S3-бакет вручную

Перейдите в браузер:

```
http://localhost:9001/browser
```

Войдите с данными:

* **Login**: `minioadmin`
* **Password**: `minioadmin`

Создайте бакет с именем:

```
lake
```

---

### 4. Запускаем скрипт для проверки и загрузки данных

Скрипт `check_and_download.py`:

* Проверяет наличие свежего `yellow_tripdata` на сайте NYC.
* Если в S3 данных нет или они устарели — загружает актуальный файл в бакет `lake`.

```bash
python check_and_download.py
```

---

### 5. Инициализируем DuckDB базу данных

```bash
duckdb ./lakehouse.duckdb
```

В CLI можно выйти с помощью:

```sql
.exit
```

В `profiles.yml` укажите путь до `lakehouse.duckdb`.

---

### 6. Устанавливаем зависимости dbt

```bash
dbt deps
```

### 7. Запускаем dbt модели

Сначала загрузка staging моделей с переменными `year` и `month`:

```bash
dbt run --select tag:staging --vars '{"year": "2025", "month": "05"}'
```

Затем последовательно:

```bash
dbt run --select tag:intermediate
dbt run --select tag:marts
```

---

### 8. Тестирование моделей

```bash
dbt test
```

---

### 9. CI/CD через GitHub Actions

Также можете настроить self-hosted runner и workflow `.github/workflows/update.yml`, который автоматически:

* Проверяет обновления на сайте
* Загружает данные в S3
* Обновляет модели dbt

---


