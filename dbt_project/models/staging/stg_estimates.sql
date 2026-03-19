{{config(materialized = 'view')}}

SELECT * FROM {{ source('staging', 'estimates_cleaned') }}