"""
load_data.py
------------
Loads the raw Kaggle credit risk CSV into PostgreSQL.
Handles column renaming, basic type validation, and null reporting.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ── 1. Load credentials ────────────────────────────────────────
load_dotenv("config/db_config.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── 2. Load CSV ────────────────────────────────────────────────
RAW_FILE = "data/raw/cs-training.csv"

print("Loading CSV...")
df = pd.read_csv(RAW_FILE, index_col=0)
print(f"  Rows loaded: {len(df):,}")

# ── 3. Rename columns ──────────────────────────────────────────
df.columns = [
    "serious_delinquency",
    "revolving_utilization",
    "age",
    "times_30_59_days_late",
    "debt_ratio",
    "monthly_income",
    "open_credit_lines",
    "times_90_days_late",
    "real_estate_loans",
    "times_60_89_days_late",
    "number_of_dependents",
]

# ── 4. Report nulls before loading ────────────────────────────
print("\nNull counts per column:")
print(df.isnull().sum())

# ── 5. Basic type enforcement ──────────────────────────────────
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df["monthly_income"] = pd.to_numeric(df["monthly_income"], errors="coerce")
df["number_of_dependents"] = pd.to_numeric(df["number_of_dependents"], errors="coerce")

# ── 6. Load into PostgreSQL ────────────────────────────────────
print("\nConnecting to PostgreSQL...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    with open("sql/schema/01_create_tables.sql", "r") as f:
        conn.execute(text(f.read()))
    conn.commit()
print("  Schema applied.")

print("  Loading data into loans_raw...")
df.to_sql(
    name="loans_raw",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=5000,
    method="multi",
)

print(f"\nDone. {len(df):,} rows loaded into loans_raw.")