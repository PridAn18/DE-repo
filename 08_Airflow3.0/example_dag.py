# Используем asset-based подход Airflow 3 SDK
from airflow.sdk import asset
from airflow.utils.log.logging_mixin import LoggingMixin  # встроенный логгер Airflow

# Стандартные библиотеки
import uuid
import sqlite3
from datetime import datetime, timezone

# Инициализация логгера Airflow — best practice для логирования в пайплайне
log = LoggingMixin().log

@asset(schedule="@daily")
def get_data() -> dict:
    import requests

    res = requests.get("https://randomuser.me/api/")
    res = res.json()
    return res['results'][0]  # результат передаётся в XCom автоматически

# Резделяем логу для проведения теста
def do_format_data(res: dict) -> dict:
    location = res['location']
    return {
        'id': str(uuid.uuid4()),  # уникальный ID пользователя
        'first_name': res['name']['first'],
        'last_name': res['name']['last'],
        'gender': res['gender'],
        'address': f"{location['street']['number']} {location['street']['name']}, "
                   f"{location['city']}, {location['state']}, {location['country']}",
        'post_code': location['postcode'],
        'email': res['email'],
        'username': res['login']['username'],
        'dob': res['dob']['date'],
        'registered_date': res['registered']['date'],
        'phone': res['phone'],
        'picture': res['picture']['medium']
    }
# format_data — обрабатывает результат get_data
# передача данных через XCom (явно указано dag_id и task_id)
# data lineage через зависимость schedule=[get_data]
@asset(schedule=[get_data])
def format_data(context: dict) -> dict:
    # Получаем результат предыдущего asset через XCom
    res = context["ti"].xcom_pull(
        dag_id="get_data",
        task_ids="get_data",
        key="return_value",
        include_prior_dates=True
    )

    if res is None:
        raise ValueError("XCom от get_data не получен")

    return do_format_data(res)

# enrich_and_save — обогащает данные и сохраняет их в SQLite
# - запись в локальную SQLite БД (альтернатива сохранению в файл)

@asset(schedule=[format_data])
def enrich_and_save(context: dict):
    # Получаем данные от format_data через XCom
    user = context["ti"].xcom_pull(
        dag_id="format_data",
        task_ids="format_data",
        key="return_value",
        include_prior_dates=True
    )

    if user is None:
        raise ValueError("XCom от format_data не получен.")

    # Расчёт возраста пользователя
    dob = datetime.fromisoformat(user["dob"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    user["age"] = int((now - dob).days / 365.25)

    log.info(f"Пользователь: {user['first_name']} {user['last_name']}, возраст: {user['age']}")

    # сохранение в локальную БД
    conn = sqlite3.connect('/tmp/users.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            email TEXT,
            age INTEGER,
            dob TEXT,
            created_at TEXT
        )
    """)

    # Вставка данных пользователя
    cursor.execute("""
        INSERT INTO users (id, first_name, last_name, gender, email, age, dob, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["id"],
        user["first_name"],
        user["last_name"],
        user["gender"],
        user["email"],
        user["age"],
        user["dob"],
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()

    log.info(f"Пользователь сохранён в БД SQLite: {user['email']}")
