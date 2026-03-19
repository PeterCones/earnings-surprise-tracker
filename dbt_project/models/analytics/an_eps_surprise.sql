{{config(materialized = 'table')}}

SELECT 
symbol ticker
, date report_date
, quarter fiscal_quarter
, year fiscal_year
, hour report_hour
, eps_estimate
, eps_actual
, (eps_actual - eps_estimate) / ABS(eps_estimate) eps_surprise_pct
FROM {{ref('stg_estimates')}}
where has_both_eps = True
