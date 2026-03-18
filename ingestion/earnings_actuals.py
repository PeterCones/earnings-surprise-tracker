import requests
import pandas as pd
import numpy as np
import psycopg2 as pg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

api_key = os.getenv('finnhub_api_key')
db_name = os.getenv("DB_NAME")
db_name = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
pswd = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
url = "https://finnhub.io/api/v1/calendar/earnings"

def fetch_actuals(**context):
    logical_date = context['logical_date']
    params = {
        "from": logical_date.strftime('%Y-%m-%d'),
        "to": logical_date.strftime('%Y-%m-%d'),
        "token": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as api_e:
        print(f"API connection failed: {api_e}")
        data = {"earningsCalendar": []}

    context['ti'].xcom_push(key='actuals_data', value=data)
        
def insert_actuals(**context):
    
    # pull from XCom
    payload = context['ti'].xcom_pull(
    task_ids='fetch_finnhub_actuals',
    key='actuals_data'
    ) or {}
    earnings = payload.get('earningsCalendar') or []
    
    #Establish conn to db
    try:
        conn = pg2.connect(
            database=db_name,
            user=user,
            password=pswd,
            host=host,
            port=port
        )
    except Exception as db_e:
        print(f"Database connection failed: {db_e}")
        exit()
    cur = conn.cursor()
    print("Database connected successfully")
    
    # insert into db
    count = 0
    for earning in earnings:
        print(f"ingesting {count}")
        count += 1
        symbol = earning.get("symbol")
        date = earning.get("date")
        hour = earning.get("hour")
        quarter = earning.get("quarter")
        year = earning.get("year")
        eps_estimate = earning.get("epsEstimate")
        eps_actual = earning.get("epsActual")
        revenue_estimate = earning.get("revenueEstimate")
        revenue_actual = earning.get("revenueActual")
        cur.execute(
            """
            INSERT INTO raw.estimates (symbol, date,hour,quarter,year,eps_estimate,eps_actual,revenue_estimate,revenue_actual)
            VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date, quarter, year) DO UPDATE SET 
            eps_actual=EXCLUDED.eps_actual,
            revenue_actual=EXCLUDED.revenue_actual
            """,
            (symbol, date, hour, quarter, year, eps_estimate, eps_actual, revenue_estimate, revenue_actual),
            )

    conn.commit()     
    cur.close()
    conn.close()