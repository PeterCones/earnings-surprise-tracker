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

def fetch_calendar():
    
    params = {
        "from": "2026-03-18",
        "to": "2026-03-18",
        "token": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        print("API connected successfully")
        print(f"Fetching Todays earnings: 2026-03-18")
    except Exception as api_e:
        print(f"API connection failed: {api_e}")

fetch_calendar()