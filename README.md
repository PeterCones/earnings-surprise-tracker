# Earnings Surprise Tracker

Data pipeline that ingests earnings announcements from Finnhub, loads them into PostgreSQL, and will eventually transform them with dbt to surface EPS surprises and post-earnings price reactions.

**Stack:** Python · PostgreSQL · Airflow · dbt · Docker Compose

> **Status:** Early development. The ingestion script and database schema are working.
> Airflow orchestration and dbt models are scaffolded but not yet implemented.

---

## What works today

- **Docker Compose stack** — spins up Airflow (CeleryExecutor with Redis) and a dedicated project Postgres database
- **Ingestion script** (`ingestion/ingestion.py`) — pulls earnings calendar data from the Finnhub API and upserts it into `raw.estimates`
- **Database schema** — `raw` and `staging` schemas created via `sql/setup.sql`; the `raw.estimates` table is defined in `sql/raw/schema_raw.sql`

## What's next

- [ ] Wire ingestion into an Airflow DAG (`dags/`)
- [ ] Add EPS actuals and price reaction data sources
- [ ] Build dbt staging, intermediate, and analytics models
- [ ] Add dbt tests and documentation

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Finnhub](https://finnhub.io/) API key (free tier is fine)

### 1. Clone and configure

```bash
git clone <this-repo> && cd earnings-surprise-tracker
cp env.example .env
```

Edit `.env` and set at minimum:

```
finnhub_api_key=<your-key>
DB_NAME=earnings_tracker
DB_USER=earnings
DB_PASS=earnings
DB_HOST=localhost
DB_PORT=5433
```

### 2. Start the stack

```bash
docker compose up -d
```

This brings up:

| Service | Access |
|---|---|
| Airflow API server | `localhost:8083` |
| Project database | `localhost:5433` (user: `earnings` / pw: `earnings`) |
| Flower (opt-in) | `docker compose --profile flower up` &rarr; `localhost:5555` |

### 3. Initialise the database

Connect to the project database and run the setup scripts:

```bash
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/setup.sql
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/raw/schema_raw.sql
```

### 4. Run the ingestion script

```bash
python ingestion/ingestion.py
```

This pulls the current week's earnings calendar from Finnhub and loads rows into `raw.estimates`.

---

## Project Structure

```
.
├── ingestion/
│   └── ingestion.py              # Finnhub earnings calendar → raw.estimates
├── sql/
│   ├── setup.sql                 # Creates raw and staging schemas
│   └── raw/
│       └── schema_raw.sql        # raw.estimates table definition
├── dags/                         # Airflow DAGs (empty — not yet implemented)
├── dbt_project/
│   └── models/
│       ├── staging/              # Planned: light cleaning of raw tables
│       ├── intermediate/         # Planned: joins and enrichment
│       └── analytics/            # Planned: earnings_surprises, price_reactions
├── config/                       # Airflow config (auto-generated)
├── logs/                         # Airflow logs (auto-generated)
├── plugins/                      # Airflow plugins (empty)
├── scripts/                      # Utility scripts (empty)
├── docker-compose.yml
├── requirements.txt
└── env.example
```

---

## `raw.estimates` schema

| Column | Type | Notes |
|---|---|---|
| `symbol` | `VARCHAR(20)` | Ticker symbol |
| `date` | `DATE` | Earnings announcement date |
| `hour` | `VARCHAR(5)` | Before/after market |
| `quarter` | `SMALLINT` | Fiscal quarter |
| `year` | `SMALLINT` | Fiscal year |
| `eps_estimate` | `NUMERIC(12,4)` | Consensus EPS estimate |
| `eps_actual` | `NUMERIC(12,4)` | Reported EPS (backfilled) |
| `revenue_estimate` | `BIGINT` | Consensus revenue estimate |
| `revenue_actual` | `BIGINT` | Reported revenue (backfilled) |
| `ingested_at` | `TIMESTAMP` | Row insertion time |

---

## API Limits

| Source | Free tier | Used for |
|---|---|---|
| Finnhub | 60 calls/min | Earnings calendar |