from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from ingestion.earnings_actuals import fetch_actuals
from ingestion.earnings_actuals import insert_actuals

with DAG(
    dag_id="weekly_fetch",
    schedule="0 22 * * 0",
    start_date=datetime(2026, 3, 18),
    catchup=False
) as dag:

    fetch = PythonOperator(
        task_id="fetch_finnhub_actuals",
        python_callable=fetch_actuals
    )

    insert = PythonOperator(
        task_id="insert_to_raw",
        python_callable=insert_actuals
    ) 
    
    fetch >> insert