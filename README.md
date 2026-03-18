# Earnings Surprise Tracker

> *The market moves on surprises. This pipeline captures them.*

Every quarter, thousands of companies report earnings. When the actual EPS blows past estimates — or falls short — prices react violently. This project builds the data infrastructure to capture those moments: ingesting raw earnings data, cleaning it, and surfacing the surprises that drive post-earnings price action.

**Stack:** Python · PostgreSQL · Airflow · dbt · Docker Compose

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Data Sources                        │
│              Finnhub API (earnings calendar)             │
└─────────────────────────┬───────────────────────────────┘
                          │  HTTP / JSON
                          ▼
┌─────────────────────────────────────────────────────────┐
│               Orchestration (Airflow 3.1.8)              │
│                                                          │
│  weekly_fetch (weekdays 9:30 PM)                         │
│    fetch_finnhub_calendar → insert_to_raw                │
│                                                          │
│  daily_fetch (Sundays 10 PM)           ← in progress     │
│    fetch_finnhub_actuals → insert_to_raw                 │
└─────────────────────────┬───────────────────────────────┘
                          │  psycopg2 upserts
                          ▼
┌─────────────────────────────────────────────────────────┐
│               PostgreSQL (earnings_tracker)              │
│                                                          │
│  raw.estimates            ← live                         │
│  staging.estimates_cleaned ← live                        │
│                                                          │
│  dbt staging models       ← coming                       │
│  dbt intermediate models  ← coming                       │
│  dbt analytics models     ← coming                       │
│    └─ earnings_surprises                                 │
│    └─ price_reactions                                    │
└─────────────────────────────────────────────────────────┘
```

---

## What's Live

### Airflow Pipeline

A production-grade Airflow stack (CeleryExecutor + Redis) runs in Docker. Every weekday evening at 9:30 PM, a DAG hits the Finnhub API, pulls the current earnings calendar, and upserts rows into the raw layer. No manual steps. No notebooks. Just a pipeline that runs.

- **DAG:** `weekly_fetch` — fires weeknights at 21:30
- **Tasks:** `fetch_finnhub_calendar` → `insert_to_raw` (XCom handoff between tasks)
- **Conflict handling:** on duplicate `(symbol, date, quarter, year)`, backfills `eps_actual` and `revenue_actual` as they become available post-announcement

### Raw Layer

`raw.estimates` is the append-friendly landing zone for everything Finnhub sends. It stores estimates alongside actuals as they flow in — the foundation for all downstream surprise calculations.

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

### Staging Layer

`staging.estimates_cleaned` is the first transformation pass: zeroes become NULLs (Finnhub uses `0` as a sentinel for missing values), and two boolean flags tell you instantly whether a row has enough data to compute a surprise.

```sql
has_both_eps     = eps_estimate IS NOT NULL AND eps_actual IS NOT NULL
has_both_revenue = revenue_estimate IS NOT NULL AND revenue_actual IS NOT NULL
```

Only rows with at least one EPS value survive the cut. Clean data only.

---

## What's Being Built

### EPS Actuals Ingestion

A second ingestion path (`earnings_actuals.py`) is being wired up to backfill actuals for past announcements — so the pipeline can catch up on any rows that landed before the company reported. The DAG scaffold is in place (`daily_fetch`, Sundays at 22:00).

### dbt Analytics Models

This is where it gets interesting. Three layers are planned:

```
staging/
  └─ stg_estimates.sql        — typed, renamed, null-safe

intermediate/
  └─ int_earnings_with_context.sql   — enrichment, joins

analytics/
  └─ earnings_surprises.sql   — the money model
       eps_surprise_pct = (eps_actual - eps_estimate) / ABS(eps_estimate)
  └─ price_reactions.sql      — % move from close before → close after
```

Once these exist, you'll be able to query: *"Which stocks beat EPS by >10% this quarter? What did they do the next day?"*

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

Set your key and database credentials in `.env`:

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

Trigger the DAG from the Airflow UI, or run the ingestion script directly:

```bash
python ingestion/ingestion.py
```

To promote raw data into the staging layer:

```bash
psql -h localhost -p 5433 -U earnings -d earnings_tracker -f sql/staging/raw_to_staging.sql
```

---

## Project Structure

```
.
├── ingestion/
│   ├── ingestion.py              # Standalone fetch + upsert script
│   ├── earnings_calendar.py      # Airflow task functions (fetch + insert)
│   └── earnings_actuals.py       # ← in progress: backfill actuals
│
├── dags/
│   ├── dag_earnings_calendar.py  # weekly_fetch DAG (live)
│   └── dag_earnings_actuals.py   # daily_fetch DAG (scaffolded)
│
├── sql/
│   ├── setup.sql                 # Create raw + staging schemas
│   ├── raw/
│   │   └── schema_raw.sql        # raw.estimates DDL
│   └── staging/
│       ├── schema_staging.sql    # staging.estimates_cleaned DDL
│       └── raw_to_staging.sql    # Transformation SQL
│
├── dbt_project/
│   └── models/
│       ├── staging/              # ← coming
│       ├── intermediate/         # ← coming
│       └── analytics/            # ← coming
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

The ingestion scripts respect this limit. At scale, a paid tier unlocks bulk historical pulls.

---

## Roadmap

- [x] Docker Compose stack (Airflow + CeleryExecutor + Redis + PostgreSQL)
- [x] Raw schema and ingestion upsert logic
- [x] Staging transformation (null cleaning, completeness flags)
- [x] Airflow DAG for weekly earnings calendar
- [ ] EPS actuals backfill ingestion
- [ ] dbt staging, intermediate, and analytics models
- [ ] `earnings_surprises` model with beat/miss classification
- [ ] `price_reactions` model (requires price data source)
- [ ] dbt tests and data quality checks
- [ ] Alerting on large surprise events
