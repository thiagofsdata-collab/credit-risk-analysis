-- =============================================================
-- Project: Credit Risk Analysis
-- Query:   02_delinquency_risk_profile.sql
-- Purpose: Analyze how past delinquency behavior predicts default
-- Business Question: Does delinquency history reliably predict
--                    future default? At what threshold?
-- =============================================================

WITH delinquency_buckets AS (
    SELECT
        CASE
            WHEN total_delinquency_events = 0  THEN '0_clean'
            WHEN total_delinquency_events = 1  THEN '1_event'
            WHEN total_delinquency_events = 2  THEN '2_events'
            WHEN total_delinquency_events <= 5 THEN '3_to_5_events'
            ELSE                                    '6_plus_events'
        END AS delinquency_bucket,
        serious_delinquency,
        monthly_income,
        debt_ratio,
        revolving_utilization,
        age_group
    FROM loans_clean
),

bucket_stats AS (
    SELECT
        delinquency_bucket,
        COUNT(*)                                    AS total_borrowers,
        SUM(serious_delinquency)                    AS total_defaults,
        ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2)    AS default_rate_pct,
        ROUND(AVG(monthly_income)::NUMERIC, 2)               AS avg_income,
        ROUND(AVG(debt_ratio)::NUMERIC, 4)                   AS avg_debt_ratio,
        ROUND(AVG(revolving_utilization)::NUMERIC * 100, 2)  AS avg_utilization_pct
    FROM delinquency_buckets
    GROUP BY delinquency_bucket
),

final AS (
    SELECT
        *,
        ROUND(
            default_rate_pct - AVG(default_rate_pct) OVER ()::NUMERIC, 2
        ) AS pct_points_vs_portfolio_avg,

        SUM(total_borrowers) OVER (
            ORDER BY default_rate_pct
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_borrowers
    FROM bucket_stats
)

SELECT *
FROM final
ORDER BY default_rate_pct ASC;