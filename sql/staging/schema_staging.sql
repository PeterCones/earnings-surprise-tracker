CREATE TABLE IF NOT EXISTS staging.estimates_cleaned (
    symbol VARCHAR(20),
    date DATE,
    hour VARCHAR(5),
    quarter SMALLINT,
    year SMALLINT,
    eps_estimate NUMERIC(12,4),
    eps_actual NUMERIC(12,4),
    revenue_estimate BIGINT,
    revenue_actual BIGINT,
    transformed_at TIMESTAMP DEFAULT NOW(),
    has_both_eps BOOLEAN,
    has_both_revenue BOOLEAN
)