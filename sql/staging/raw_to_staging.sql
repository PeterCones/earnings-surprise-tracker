INSERT INTO staging.estimates_cleaned (
symbol
, date
, hour
, quarter
, year
, eps_estimate
, eps_actual
, revenue_estimate
, revenue_actual
, has_both_eps
, has_both_revenue
)
SELECT 
e.symbol
, e.date
, e.hour
, e.quarter
, e.year
, NULLIF(e.eps_estimate, 0)
, NULLIF(e.eps_actual,0)
, NULLIF(e.revenue_estimate,0)
, NULLIF(e.revenue_actual,0)
, CASE 
    WHEN e.eps_estimate IS NOT NULL AND e.eps_actual IS NOT NULL THEN True 
    ELSE  False
END
, CASE 
    WHEN e.revenue_estimate IS NOT NULL AND e.revenue_actual IS NOT NULL THEN True 
    ELSE  False
END
 FROM raw.estimates e 
WHERE e.eps_estimate IS NOT NULL OR e.eps_actual IS NOT NULL
