# Earnings Surprise Tracker

End-to-end data pipeline tracking earnings announcements, EPS surprises, and post-earnings stock price reactions.

**Stack:** Python · Airflow · PostgreSQL · dbt · Docker Compose

---

## Getting Started

### 1. Clone and configure

```bash
cp env.example .env
# Edit .env and add your Finnhub and FMP API keys
```

### 2. Spin up the stack

```bash
docker compose up -d
```

Wait ~30 seconds for Airflow to initialise, then open:
- **Airflow UI:** http://localhost:8080 (admin / admin)
- **Project DB:** localhost:5433

### 3. Run the hello world DAG

In the Airflow UI, find `dag_hello_world`, unpause it, and trigger it manually.
All three tasks should go green — this confirms Airflow can reach the DB and your API keys are set.

### 4. Trigger the calendar DAG

Unpause and manually trigger `dag_earnings_calendar` to pull the next week of earnings announcements.

---

## Project Structure

```
.
├── dags/                         # Airflow DAG definitions
├── dbt_project/
│   └── models/
│       ├── staging/              # Views — light cleaning of raw tables
│       ├── intermediate/         # Views — joins and enrichment
│       └── analytics/            # Tables — earnings_surprises, price_reactions
├── ingestion/                    # API clients and DB helpers
├── logs/                         # Airflow logs (auto-generated)
├── plugins/                      # Airflow plugins
├── scripts/                      # DB initialisation scripts
├── docker-compose.yml
└── env.example
```

---

## DAG Schedule

| DAG | Schedule | What it does |
|---|---|---|
| `dag_earnings_calendar` | Sunday 22:00 UTC | Pulls next week of earnings from Finnhub |
| `dag_earnings_actuals` | Mon–Fri 21:30 UTC | Fetches EPS actuals from FMP for today's reporters |
| `dag_price_reaction` | Mon–Fri 22:30 UTC | Fetches price snapshots for post-earnings window |

---

## dbt

Run dbt from the `dbt_project/` directory (against the exposed port 5433):

```bash
cd dbt_project
dbt run
dbt test
```

---

## API Limits

| Source | Free tier | Used for |
|---|---|---|
| Finnhub | 60 calls/min | Earnings calendar, price candles |
| FMP | 250 calls/day | EPS actuals |