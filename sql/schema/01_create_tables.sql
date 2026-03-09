-- =============================================================
-- Project: Credit Risk Analysis
-- Script:  01_create_tables.sql
-- Purpose: Define the raw loans table schema
-- Author:  [Your Name]
-- =============================================================

DROP TABLE IF EXISTS loans_raw;

CREATE TABLE loans_raw (
    loan_id                   SERIAL PRIMARY KEY,
    serious_delinquency       SMALLINT,
    revolving_utilization     NUMERIC(10, 4),
    age                       SMALLINT,
    times_30_59_days_late     SMALLINT,
    debt_ratio                NUMERIC(10, 4),
    monthly_income            NUMERIC(12, 2),
    open_credit_lines         SMALLINT,
    times_90_days_late        SMALLINT,
    real_estate_loans         SMALLINT,
    times_60_89_days_late     SMALLINT,
    number_of_dependents      SMALLINT
);