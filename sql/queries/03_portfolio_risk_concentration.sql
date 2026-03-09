-- =============================================================
-- Project: Credit Risk Analysis
-- Query:   03_portfolio_risk_concentration.sql
-- Purpose: Identify where default risk is concentrated
--          using cumulative window functions
-- Business Question: What share of total defaults comes from
--                    the highest-risk segments?
-- Note:    Avoids nested window functions by pre-computing
--          portfolio totals in a dedicated CTE
-- =============================================================

WITH income_risk AS (
    SELECT
        income_band,
        age_group,
        COUNT(*)                                        AS total_borrowers,
        SUM(serious_delinquency)                        AS total_defaults,
        ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2) AS default_rate_pct
    FROM loans_clean
    GROUP BY income_band, age_group
),

-- Pre-compute portfolio totals separately to avoid nesting window functions
portfolio_totals AS (
    SELECT
        SUM(total_defaults)    AS grand_total_defaults,
        SUM(total_borrowers)   AS grand_total_borrowers
    FROM income_risk
),

concentration AS (
    SELECT
        r.income_band,
        r.age_group,
        r.total_borrowers,
        r.total_defaults,
        r.default_rate_pct,

        ROUND(
            r.total_defaults * 100.0 / p.grand_total_defaults, 2
        ) AS pct_of_total_defaults,

        ROUND(
            r.total_borrowers * 100.0 / p.grand_total_borrowers, 2
        ) AS pct_of_total_borrowers,

        -- Cumulative default share from highest to lowest risk
        ROUND(
            SUM(r.total_defaults * 100.0 / p.grand_total_defaults) OVER (
                ORDER BY r.default_rate_pct DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )::NUMERIC, 2
        ) AS cumulative_default_share_pct

    FROM income_risk r
    CROSS JOIN portfolio_totals p
)

SELECT *
FROM concentration
ORDER BY default_rate_pct DESC;