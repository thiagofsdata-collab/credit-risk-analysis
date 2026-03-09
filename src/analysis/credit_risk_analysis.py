"""
credit_risk_analysis.py
-----------------------
Extracts analytical results from PostgreSQL and computes
portfolio-level credit risk metrics using Pandas.
Outputs cleaned DataFrames ready for Plotly visualization.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ── 1. Connection ──────────────────────────────────────────────
load_dotenv("config/db_config.env")

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)

# ── 2. Load core dataset from clean table ─────────────────────
print("Loading loans_clean from PostgreSQL...")

df = pd.read_sql("SELECT * FROM loans_clean", engine)
print(f"  Rows loaded: {len(df):,}")
print(f"  Columns: {list(df.columns)}\n")

# ── 3. Portfolio-level summary ────────────────────────────────
print("=" * 50)
print("PORTFOLIO SUMMARY")
print("=" * 50)

total = len(df)
total_defaults = df["serious_delinquency"].sum()
default_rate = df["serious_delinquency"].mean() * 100

print(f"  Total borrowers   : {total:,}")
print(f"  Total defaults    : {total_defaults:,}")
print(f"  Portfolio default rate: {default_rate:.2f}%\n")

# ── 4. Default rate by segment (from SQL query 01) ────────────
print("=" * 50)
print("DEFAULT RATE BY SEGMENT")
print("=" * 50)

segment_query = text("""
    WITH segment_stats AS (
        SELECT
            age_group,
            income_band,
            utilization_band,
            COUNT(*)                                          AS total_borrowers,
            SUM(serious_delinquency)                          AS total_defaults,
            ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2) AS default_rate_pct,
            ROUND(AVG(monthly_income)::NUMERIC, 2)            AS avg_income,
            ROUND(AVG(revolving_utilization)::NUMERIC * 100, 2) AS avg_utilization_pct,
            ROUND(AVG(debt_ratio)::NUMERIC, 4)                AS avg_debt_ratio
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
        WHERE total_borrowers >= 50
    )
    SELECT * FROM ranked
    ORDER BY default_rate_pct DESC
""")

df_segments = pd.read_sql(segment_query, engine)
print(df_segments.head(10).to_string(index=False))

# ── 5. Delinquency risk profile (from SQL query 02) ───────────
print("\n" + "=" * 50)
print("DELINQUENCY RISK PROFILE")
print("=" * 50)

delinquency_query = text("""
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
            revolving_utilization
        FROM loans_clean
    ),
    bucket_stats AS (
        SELECT
            delinquency_bucket,
            COUNT(*)                                        AS total_borrowers,
            SUM(serious_delinquency)                        AS total_defaults,
            ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2) AS default_rate_pct,
            ROUND(AVG(monthly_income)::NUMERIC, 2)          AS avg_income,
            ROUND(AVG(debt_ratio)::NUMERIC, 4)              AS avg_debt_ratio,
            ROUND(AVG(revolving_utilization)::NUMERIC * 100, 2) AS avg_utilization_pct
        FROM delinquency_buckets
        GROUP BY delinquency_bucket
    )
    SELECT
        *,
        ROUND(
            (default_rate_pct - AVG(default_rate_pct) OVER ())::NUMERIC, 2
        ) AS pct_points_vs_portfolio_avg
    FROM bucket_stats
    ORDER BY default_rate_pct ASC
""")

df_delinquency = pd.read_sql(delinquency_query, engine)
print(df_delinquency.to_string(index=False))

# ── 6. Portfolio concentration (from SQL query 03) ────────────
print("\n" + "=" * 50)
print("PORTFOLIO RISK CONCENTRATION")
print("=" * 50)

concentration_query = text("""
    WITH income_risk AS (
        SELECT
            income_band,
            age_group,
            COUNT(*)                                          AS total_borrowers,
            SUM(serious_delinquency)                          AS total_defaults,
            ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2) AS default_rate_pct
        FROM loans_clean
        GROUP BY income_band, age_group
    ),
    portfolio_totals AS (
        SELECT
            SUM(total_defaults)  AS grand_total_defaults,
            SUM(total_borrowers) AS grand_total_borrowers
        FROM income_risk
    ),
    concentration AS (
        SELECT
            r.income_band,
            r.age_group,
            r.total_borrowers,
            r.total_defaults,
            r.default_rate_pct,
            ROUND(r.total_defaults * 100.0 / p.grand_total_defaults, 2)
                AS pct_of_total_defaults,
            ROUND(r.total_borrowers * 100.0 / p.grand_total_borrowers, 2)
                AS pct_of_total_borrowers,
            ROUND(
                SUM(r.total_defaults * 100.0 / p.grand_total_defaults) OVER (
                    ORDER BY r.default_rate_pct DESC
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )::NUMERIC, 2
            ) AS cumulative_default_share_pct
        FROM income_risk r
        CROSS JOIN portfolio_totals p
    )
    SELECT * FROM concentration
    ORDER BY default_rate_pct DESC
""")


# ── Heatmap-specific query (no utilization_band grouping) ─────
heatmap_query = text("""
    SELECT
        age_group,
        income_band,
        COUNT(*)                                          AS total_borrowers,
        ROUND(AVG(serious_delinquency)::NUMERIC * 100, 2) AS default_rate_pct
    FROM loans_clean
    GROUP BY age_group, income_band
    ORDER BY age_group, income_band
""")

df_heatmap = pd.read_sql(heatmap_query, engine)
df_heatmap.to_csv("data/processed/heatmap.csv", index=False)
print("  Saved: data/processed/heatmap.csv")



df_concentration = pd.read_sql(concentration_query, engine)
print(df_concentration.to_string(index=False))

# ── 7. Export DataFrames for visualization layer ──────────────
print("\nExporting DataFrames to processed data folder...")

df_segments.to_csv("data/processed/segments.csv", index=False)
df_delinquency.to_csv("data/processed/delinquency_profile.csv", index=False)
df_concentration.to_csv("data/processed/concentration.csv", index=False)

print("  Saved: data/processed/segments.csv")
print("  Saved: data/processed/delinquency_profile.csv")
print("  Saved: data/processed/concentration.csv")
print("\nAnalysis complete.")