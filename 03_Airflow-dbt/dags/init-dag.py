from airflow import DAG
from airflow.providers.clickhouse.hooks.clickhouse import ClickHouseHook
from airflow.operators.python import PythonOperator

from datetime import datetime
import pandas as pd


with DAG(dag_id='clickhouse_load_csv', start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False) as dag:

    def preprocess_csv(**kwargs):
        df = pd.read_csv('/opt/airflow/data/10000 Sales Records.csv')
        df = df.rename(columns={
            'Item Type': 'Item_Type',
            'Sales Channel': 'Sales_Channel',
            'Order Priority': 'Order_Priority',
            'Order Date': 'Order_Date',
            'Order ID': 'Order_ID',
            'Ship Date': 'Ship_Date',
            'Units Sold': 'Units_Sold',
            'Unit Price': 'Unit_Price',
            'Unit Cost': 'Unit_Cost',
            'Total Revenue': 'Total_Revenue',
            'Total Cost': 'Total_Cost',
            'Total Profit': 'Total_Profit'
        })
        df.to_csv('/opt/airflow/data/10000 Sales Records.csv', index=False)
        return '/opt/airflow/data/10000 Sales Records.csv'

    def load_to_clickhouse(**kwargs):
        ti = kwargs['ti']
        csv_path = ti.xcom_pull(task_ids='preprocess_csv')

        hook = ClickHouseHook(
            host='localhost', # Хост ClickHouse
            port=9000, # Порт ClickHouse (по умолчанию 9000 для native, 8123 для HTTP)
            user='admin', # Имя пользователя
            password='admin', # Пароль
            database='default', # База данных (если отличается от default)
        )

        with open(csv_path, 'r') as file:
            hook.run(f"INSERT INTO sales FORMAT CSVWithNames", data=file) # Использование run с data


    preprocess_task = PythonOperator(
        task_id='preprocess_csv',
        python_callable=preprocess_csv,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id='load_to_clickhouse',
        python_callable=load_to_clickhouse,
        provide_context=True,
    )

    preprocess_task >> load_task

    