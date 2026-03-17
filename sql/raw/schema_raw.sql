CREATE TABLE IF NOT EXISTS raw.estimates (
    symbol VARCHAR(20),
    date DATE,
    hour VARCHAR(5),
    quarter SMALLINT,
    year SMALLINT,
    eps_estimate NUMERIC(12,4),
    eps_actual NUMERIC(12,4),
    revenue_estimate BIGINT,
    revenue_actual BIGINT,
    ingested_at TIMESTAMP DEFAULT NOW()
)
