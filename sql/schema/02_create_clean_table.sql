-- =============================================================
-- Project: Credit Risk Analysis
-- Script:  02_create_clean_table.sql
-- Purpose: Create cleaned loans table from raw data
--          Handles nulls, flags outliers, enforces valid ranges
-- Strategy: Layered CTEs — each layer consumes cleaned columns
--           from the previous one, avoiding redundant expressions
-- =============================================================

DROP TABLE IF EXISTS loans_clean;

CREATE TABLE loans_clean AS

-- ── Layer 1: Compute median for income imputation ─────────────
WITH median_income AS (
    SELECT PERCENTILE_CONT(0.5)
           WITHIN GROUP (ORDER BY monthly_income) AS median_val
    FROM loans_raw
    WHERE monthly_income IS NOT NULL
),

-- ── Layer 2: Apply all cleaning rules once ────────────────────
--    Every transformation happens here and only here.
--    Downstream layers consume these clean columns directly.
cleaned AS (
    SELECT
        loan_id,
        serious_delinquency,

        -- Revolving utilization clamped to valid range [0, 1]
        LEAST(GREATEST(revolving_utilization, 0), 1)
            AS revolving_utilization,

        -- Age already filtered by WHERE below, no extra CASE needed
        age,

        times_30_59_days_late,
        times_60_89_days_late,
        times_90_days_late,

        -- Income: impute nulls with median once, reuse alias downstream
        COALESCE(monthly_income, (SELECT median_val FROM median_income))
            AS monthly_income,

        -- Debt ratio capped at 10 to limit outlier distortion
        LEAST(debt_ratio, 10)
            AS debt_ratio,

        open_credit_lines,
        real_estate_loans,

        -- Dependents: impute nulls with 0 (mode)
        COALESCE(number_of_dependents, 0)
            AS number_of_dependents

    FROM loans_raw
    WHERE age BETWEEN 18 AND 100
),

-- ── Layer 3: Derive business features from clean columns ──────
--    All CASE expressions now reference simple column names,
--    not repeated expressions. Clean and readable.
enriched AS (
    SELECT
        *,

        -- Age segmentation
        CASE
            WHEN age < 30               THEN 'under_30'
            WHEN age BETWEEN 30 AND 44  THEN '30_to_44'
            WHEN age BETWEEN 45 AND 59  THEN '45_to_59'
            ELSE                             '60_plus'
        END AS age_group,

        -- Income segmentation (uses already-imputed monthly_income)
        CASE
            WHEN monthly_income < 3000               THEN 'low'
            WHEN monthly_income BETWEEN 3000 AND 6999 THEN 'medium'
            WHEN monthly_income BETWEEN 7000 AND 11999 THEN 'high'
            ELSE                                          'very_high'
        END AS income_band,

        -- Utilization risk band (uses already-clamped revolving_utilization)
        CASE
            WHEN revolving_utilization < 0.3  THEN 'low'
            WHEN revolving_utilization < 0.6  THEN 'medium'
            WHEN revolving_utilization < 0.9  THEN 'high'
            ELSE                                   'critical'
        END AS utilization_band,

        -- Total delinquency events across all severity levels
        (times_30_59_days_late + times_60_89_days_late + times_90_days_late)
            AS total_delinquency_events

    FROM cleaned
)

-- ── Final SELECT: materialize everything into loans_clean ─────
SELECT * FROM enriched;

-- Indexes for query performance on most-used filter columns
CREATE INDEX idx_loans_clean_age_group
    ON loans_clean(age_group);

CREATE INDEX idx_loans_clean_income_band
    ON loans_clean(income_band);

CREATE INDEX idx_loans_clean_delinquency
    ON loans_clean(serious_delinquency);