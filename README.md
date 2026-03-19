# Earnings Surprise Tracker

> *The market moves on surprises. This pipeline captures them.*

Every quarter, thousands of companies report earnings. When actual EPS blows past estimates — or falls short — prices react violently. This project builds the data infrastructure to capture those moments: ingesting raw earnings data, cleaning it, and surfacing the surprises that drive post-earnings price action.

**Stack:** Python · PostgreSQL · Airflow · dbt · Docker Compose

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Data Sources                          │
│                 Finnhub API  (earnings calendar)              │
└──────────────────────────────┬───────────────────────────────┘
                               │  HTTP / JSON
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Orchestration  (Airflow 3.1.8)               │
│                                                               │
│  weekly_fetch  (weekdays 21:30)                               │
│    fetch_finnhub_calendar  →  insert_to_raw                   │
│                                                               │
│  daily_fetch  (Sundays 22:00)                                 │
│    fetch_finnhub_actuals  →  insert_to_raw                    │
└──────────────────────────────┬───────────────────────────────┘
                               │  psycopg2 upserts
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  PostgreSQL  (earnings_tracker)                │
│                                                               │
│  raw.estimates                 ← live                         │
│  staging.estimates_cleaned     ← live                         │
│                                                               │
│  dbt  staging/stg_estimates    ← live                         │
│  dbt  analytics/an_eps_surprise← live                         │
│                                                               │
│  dbt  intermediate/            ← coming                       │
│  dbt  analytics/price_reactions← coming                       │
└──────────────────────────────────────────────────────────────┘
```

---

## What's Live

### Airflow Pipeline

A production-grade Airflow stack (CeleryExecutor + Redis) runs in Docker. Two DAGs run on schedule, both feeding the same raw layer.

**`weekly_fetch`** — fires weeknights at 21:30
- **Tasks:** `fetch_finnhub_calendar` → `insert_to_raw` (XCom handoff)
- Pulls the 7-day earnings calendar from Finnhub and upserts into `raw.estimates`
- **Conflict handling:** on duplicate `(symbol, date, quarter, year)`, backfills `eps_actual` and `revenue_actual` as they become available post-announcement

**`daily_fetch`** — fires Sundays at 22:00
- **Tasks:** `fetch_finnhub_actuals` → `insert_to_raw` (XCom handoff)
- Fetches actuals for the logical execution date and upserts into `raw.estimates`
- Backfills any rows that landed before the company reported

---

### Raw Layer — `raw.estimates`

The append-friendly landing zone for everything Finnhub sends. Stores estimates alongside actuals as they flow in.

| Column | Type | Notes |
|---|---|---|
| `symbol` | `VARCHAR(20)` | Ticker |
| `date` | `DATE` | Announcement date |
| `hour` | `VARCHAR(5)` | BMO / AMC |
| `quarter` | `SMALLINT` | Fiscal quarter |
| `year` | `SMALLINT` | Fiscal year |
| `eps_estimate` | `NUMERIC(12,4)` | Consensus EPS |
| `eps_actual` | `NUMERIC(12,4)` | Reported EPS |
| `revenue_estimate` | `BIGINT` | Consensus revenue |
| `revenue_actual` | `BIGINT` | Reported revenue |
| `ingested_at` | `TIMESTAMP` | Row insertion time |

---

### Staging Layer — `staging.estimates_cleaned`

The first transformation pass: Finnhub uses `0` as a sentinel for missing values — these become NULLs. Two boolean flags tell you instantly whether a row is ready for surprise calculations.

```sql
has_both_eps     = eps_estimate IS NOT NULL AND eps_actual IS NOT NULL
has_both_revenue = revenue_estimate IS NOT NULL AND revenue_actual IS NOT NULL
```

Only rows with at least one EPS value survive the cut.

---

### dbt Models

The analytics layer is built with dbt and runs on top of the staging schema.

```
models/
├── staging/
│   └── stg_estimates.sql          — typed view over staging.estimates_cleaned
│
└── analytics/
    └── an_eps_surprise.sql        — materialized EPS surprise table
         eps_surprise_pct = (eps_actual - eps_estimate) / ABS(eps_estimate)
```

**`stg_estimates`** is a view that serves as the clean semantic reference for all downstream models. dbt tests enforce non-null keys and composite uniqueness on `(symbol, date, quarter, year)`.

**`an_eps_surprise`** is a materialized table containing only rows where both EPS values are present. It renames columns to business terminology (`symbol → ticker`, `date → report_date`, etc.) and computes the signed surprise percentage.

| Column | Description |
|---|---|
| `ticker` | Stock symbol |
| `report_date` | Earnings announcement date |
| `report_hour` | BMO / AMC |
| `fiscal_quarter` | Fiscal quarter (1–4) |
| `fiscal_year` | Fiscal year |
| `eps_estimate` | Consensus EPS estimate |
| `eps_actual` | Reported EPS |
| `eps_surprise_pct` | `(actual − estimate) / ABS(estimate)` |

dbt tests cover: `not_null` on all key columns, composite uniqueness, ensuring analytical integrity across runs.

---

## What's Being Built

```
intermediate/
  └─ int_earnings_with_context.sql   — enrichment, joins, derived fields

analytics/
  └─ price_reactions.sql             — % move from close before → close after
```

Once price data is integrated, you'll be able to query: *"Which stocks beat EPS by >10% this quarter? What did they do the next day?"*

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Finnhub](https://finnhub.io/) API key (free tier works)

### 1. Clone and configure

```bash
git clone <this-repo> && cd earnings-surprise-tracker
cp env.example .env
```

Edit `.env` with your credentials:

```env
finnhub_api_key=your_key_here

DB_NAME=earnings_tracker
DB_USER=earnings
DB_PASS=earnings
DB_HOST=postgres-project
DB_PORT=5432
```

### 2. Start the stack

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Airflow UI | [localhost:8083](http://localhost:8083) — `admin` / `admin` |
| Project DB | `localhost:5433` — `earnings` / `earnings` |
| Flower (Celery monitor) | `docker compose --profile flower up` → [localhost:5555](http://localhost:5555) |

### 3. Initialise the database

```bash
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/setup.sql
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/raw/schema_raw.sql
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/staging/schema_staging.sql
```

### 4. Run the pipeline

Trigger the DAGs from the Airflow UI, or promote raw data to staging manually:

```bash
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/staging/raw_to_staging.sql
```

### 5. Run dbt

```bash
cd dbt_project
dbt run          # build all models
dbt test         # run data quality tests
```

---

## Project Structure

```
.
├── dags/
│   ├── dag_earnings_calendar.py  # weekly_fetch DAG (live)
│   └── dag_earnings_actuals.py   # daily_fetch DAG (live)
│
├── ingestion/
│   ├── earnings_calendar.py      # Airflow task functions (fetch + insert calendar)
│   └── earnings_actuals.py       # Airflow task functions (fetch + insert actuals)
│
├── sql/
│   ├── setup.sql                 # Create raw + staging schemas
│   ├── raw/
│   │   └── schema_raw.sql        # raw.estimates DDL
│   └── staging/
│       ├── schema_staging.sql    # staging.estimates_cleaned DDL
│       └── raw_to_staging.sql    # Transformation SQL (raw → staging)
│
├── dbt_project/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   ├── sources.yml           # Source definitions
│       │   ├── stg_schema.yml        # Tests + docs
│       │   └── stg_estimates.sql     # Staging view (live)
│       ├── intermediate/             # ← coming
│       └── analytics/
│           ├── an_schema.yml         # Tests + docs
│           └── an_eps_surprise.sql   # EPS surprise table (live)
│
├── docker-compose.yml
├── requirements.txt
└── env.example
```

---

## API Limits

| Source | Free tier | Used for |
|---|---|---|
| Finnhub | 60 req/min | Earnings calendar + actuals |

The ingestion scripts respect this limit. A paid tier unlocks bulk historical pulls.

---

## Roadmap

- [x] Docker Compose stack (Airflow + CeleryExecutor + Redis + PostgreSQL)
- [x] Raw schema and ingestion upsert logic
- [x] Staging transformation (null cleaning, completeness flags)
- [x] Airflow DAG for weekly earnings calendar
- [x] EPS actuals backfill ingestion (`daily_fetch` DAG, Sundays 22:00)
- [x] dbt staging model (`stg_estimates`) with data quality tests
- [x] dbt analytics model (`an_eps_surprise`) with EPS surprise percentage
- [ ] dbt intermediate models (enrichment, joins)
- [ ] `price_reactions` model (requires price data source)
- [ ] Alerting on large surprise events
