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