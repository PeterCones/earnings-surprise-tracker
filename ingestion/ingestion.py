import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

api_key = os.getenv('finnhub_api_key')

response = requests.get(
    "https://finnhub.io/api/v1/calendar/earnings",
    params={
        "from": "2026-03-10",
        "to": "2026-03-15",
        "token": api_key
    }
)

data = response.json()
df = pd.DataFrame(data)

df.to_csv("output.csv", index=False)

