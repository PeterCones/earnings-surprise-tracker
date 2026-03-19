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

# finnhub variables
url = "https://finnhub.io/api/v1/calendar/earnings"
params={
        "from": "2026-03-10",
        "to": "2026-03-15",
        "token": api_key
    }

# Establish connection to db
try:
    conn = pg2.connect(
        database=db_name,
        user=user,
        password=pswd,
        host=host,
        port=port
    )
    cur = conn.cursor()
    print("Database connected successfully")
except Exception as db_e:
    print(f"Database connection failed: {db_e}")
    exit()
try:
    response = requests.get(url, params=params)
    print("API connected successfully")
except Exception as api_e:
    print(f"API connection failed: {api_e}")

data = response.json()
earnings = data.get("earningsCalendar", [])
count = 0
for earning in earnings:
    print(f"ingesting {count}")
    count += 1
    symbol = earning["symbol"]
    date = earning["date"]
    hour = earning["hour"]
    quarter = earning["quarter"]
    year = earning["year"]
    eps_estimate = earning["epsEstimate"]
    eps_actual = earning["epsActual"]
    revenue_estimate = earning["revenueEstimate"]
    revenue_actual = earning["revenueActual"]
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