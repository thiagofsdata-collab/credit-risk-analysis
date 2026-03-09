-- =============================================================
-- Project: Credit Risk Analysis
-- Query:   01_default_rate_by_segment.sql
-- Purpose: Calculate default rates across borrower segments
--          Uses window functions to rank segments by risk
-- Business Question: Which borrower segments carry the highest
--                    default risk?
-- =============================================================

WITH segment_stats AS (
    SELECT
        age_group,
        income_band,
        utilization_band,
        COUNT(*)                                         AS total_borrowers,
        SUM(serious_delinquency)                         AS total_defaults,
        ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2)         AS default_rate_pct,
        ROUND(AVG(monthly_income)::NUMERIC, 2)                    AS avg_income,
        ROUND(AVG(revolving_utilization)::NUMERIC * 100, 2)       AS avg_utilization_pct,
        ROUND(AVG(debt_ratio)::NUMERIC, 4)                        AS avg_debt_ratio
    FROM loans_clean
    GROUP BY age_group, income_band, utilization_band
),

ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY age_group
            ORDER BY default_rate_pct DESC
        ) AS risk_rank_within_age_group,

        ROUND(
            PERCENT_RANK() OVER (
                ORDER BY default_rate_pct
            )::NUMERIC * 100, 1
        ) AS risk_percentile

    FROM segment_stats
    WHERE total_borrowers >= 100
)

SELECT *
FROM ranked
ORDER BY default_rate_pct DESC;