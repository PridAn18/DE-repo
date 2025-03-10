from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType
import time

import logging
logging.basicConfig(level=logging.ERROR)

def insert_data(session, **kwargs):

    user_id = kwargs.get('id')
    first_name = kwargs.get('first_name')
    last_name = kwargs.get('last_name')
    gender = kwargs.get('gender')
    address = kwargs.get('address')
    postcode = kwargs.get('post_code')
    email = kwargs.get('email')
    username = kwargs.get('username')
    dob = kwargs.get('dob')
    registered_date = kwargs.get('registered_date')
    phone = kwargs.get('phone')
    picture = kwargs.get('picture')

    try:
        session.execute("""
            INSERT INTO spark_streams.created_users(id, first_name, last_name, gender, address, 
                post_code, email, username, dob, registered_date, phone, picture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, first_name, last_name, gender, address,
              postcode, email, username, dob, registered_date, phone, picture))
        logging.info(f"Data inserted for {first_name} {last_name}")

    except Exception as e:
        logging.error(f'could not insert data due to {e}')


def create_spark_connection():
    s_conn = None
    host = "clickhouse"
    port = "8123"
    user = "admin"
    password = "admin"
    database = "default"


    s_conn = (SparkSession
    .builder
    .appName("PoC-ClickHouse")
    .config("spark.jars", "/home/anton1/.m2/clickhouse-spark-runtime-3.5_2.13-0.8.1.jar, /home/anton1/.m2/clickhouse-jdbc-0.6.3.jar, /home/anton1/.m2/spark-sql-kafka-0-10_2.13-3.4.1.jar")
    .config("spark.sql.catalog.clickhouse.host", host)
    .config("spark.sql.catalog.clickhouse.protocol", "http")
    .config("spark.sql.catalog.clickhouse.http_port", port)  
    .config("spark.sql.catalog.clickhouse.user", user)
    .config("spark.sql.catalog.clickhouse.password", password)
    .config("spark.sql.catalog.clickhouse.database", database)
    .config("spark.driver.bindAddress", "0.0.0.0")
    .getOrCreate() # Создаем SparkSession
    )
    return s_conn

def connect_to_kafka(spark_conn):
    spark_df = None
    spark_df = spark_conn.readStream \
        .format('kafka') \
        .option('kafka.bootstrap.servers', 'broker:9092') \
        .option('subscribe', 'users_created') \
        .option('startingOffsets', 'earliest') \
        .load()
    return spark_df


def create_selection_df_from_kafka(spark_df):
    if spark_df is None:
        print("Ошибка: spark_df is None. Проверьте функцию чтения из Kafka.")
        return None
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("first_name", StringType(), False),
        StructField("last_name", StringType(), False),
        StructField("gender", StringType(), False),
        StructField("address", StringType(), False),
        StructField("post_code", StringType(), False),
        StructField("email", StringType(), False),
        StructField("username", StringType(), False),
        StructField("registered_date", StringType(), False),
        StructField("phone", StringType(), False),
        StructField("picture", StringType(), False)
    ])

    sel = spark_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col('value'), schema).alias('data')).select("data.*")

    return sel


def write_to_clickhouse(batch_df, batch_id):
    try:
        batch_df.write \
            .format("jdbc") \
            .option('url', f'jdbc:clickhouse://clickhouse:8123/default?ssl=false&user=admin&password=admin') \
            .option('driver', 'com.clickhouse.jdbc.ClickHouseDriver') \
            .option('dbtable', 'created_users') \
            .mode('append') \
            .save()
    except Exception as e:
        print(f"Ошибка при выполнении записи в ClickHouse: {e}")



if __name__ == "__main__":
    # Создание Spark Session
    spark_conn = create_spark_connection()

    if spark_conn is not None:
        # Создание подключения к Kafka с Spark Session
        spark_df = connect_to_kafka(spark_conn)
        selection_df = create_selection_df_from_kafka(spark_df)

        while True:
            try:
                # Запись данных в ClickHouse с использованием пакетной записи
                query = selection_df.writeStream \
                .foreachBatch(write_to_clickhouse) \
                .outputMode("append") \
                .start() \
                .awaitTermination() 
                break  # Если запись выполнена успешно, выходим из цикла
            except Exception as e:
                print(f"Ошибка при выполнении записи в ClickHouse: {e}. Повторная попытка через 15 секунд...")
                time.sleep(15)  # Ждем 15 секунд перед повторной попыткой
