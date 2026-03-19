from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from ingestion.earnings_calendar import fetch_calendar
from ingestion.earnings_calendar import insert_calendar

with DAG(
    dag_id="daily_fetch",
    schedule="30 21 * * 1-5",
    start_date=datetime(2026, 3, 18),
    catchup=False
) as dag:

    fetch = PythonOperator(
        task_id="fetch_finnhub_calendar",
        python_callable=fetch_calendar
    )

    insert = PythonOperator(
        task_id="insert_to_raw",
        python_callable=insert_calendar
    )

    fetch >> insert