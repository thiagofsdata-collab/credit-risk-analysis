# Data Dictionary — Credit Risk Analysis

## Source
Kaggle: [Give Me Some Credit](https://www.kaggle.com/competitions/GiveMeSomeCredit/data)

---

## Table: `loans_raw`
Raw data loaded directly from CSV. Never modified after ingestion.

| Column | Type | Description |
|---|---|---|
| `loan_id` | SERIAL | Surrogate primary key generated on ingestion |
| `serious_delinquency` | SMALLINT | **Target variable.** 1 = borrower was 90+ days past due within 2 years |
| `revolving_utilization` | NUMERIC | Ratio of revolving credit balance to credit limit. Values clamped to [0,1] in clean table |
| `age` | SMALLINT | Borrower age in years. Records outside [18, 100] excluded in clean table |
| `times_30_59_days_late` | SMALLINT | Number of times borrower was 30–59 days past due (not worse) |
| `debt_ratio` | NUMERIC | Monthly debt payments divided by monthly gross income |
| `monthly_income` | NUMERIC | Self-reported monthly income in USD. ~20% null — imputed with median in clean table |
| `open_credit_lines` | SMALLINT | Number of open credit lines and installment loans |
| `times_90_days_late` | SMALLINT | Number of times borrower was 90+ days past due |
| `real_estate_loans` | SMALLINT | Number of mortgage and real estate loans |
| `times_60_89_days_late` | SMALLINT | Number of times borrower was 60–89 days past due (not worse) |
| `number_of_dependents` | SMALLINT | Number of dependents. ~2.6% null — imputed with 0 in clean table |

---

## Table: `loans_clean`
Cleaned and enriched version of `loans_raw`. Used for all analysis.

### Cleaning Rules Applied
| Column | Rule |
|---|---|
| `age` | Records outside [18, 100] removed via WHERE filter |
| `revolving_utilization` | Clamped to [0, 1] using LEAST/GREATEST |
| `monthly_income` | Nulls imputed with median of non-null values |
| `debt_ratio` | Capped at 10 to limit outlier distortion |
| `number_of_dependents` | Nulls imputed with 0 (mode) |

### Derived Columns
| Column | Type | Logic |
|---|---|---|
| `age_group` | VARCHAR | under_30 / 30_to_44 / 45_to_59 / 60_plus |
| `income_band` | VARCHAR | low (<3k) / medium (3k–7k) / high (7k–12k) / very_high (12k+) |
| `utilization_band` | VARCHAR | low (<30%) / medium (30–60%) / high (60–90%) / critical (90%+) |
| `total_delinquency_events` | INTEGER | Sum of all three delinquency count columns |

---

## Processed Files (`data/processed/`)

| File | Description |
|---|---|
| `segments.csv` | Default rate by age_group × income_band × utilization_band |
| `delinquency_profile.csv` | Default rate by delinquency event bucket |
| `concentration.csv` | Portfolio default concentration with cumulative share |
| `heatmap.csv` | Default rate by age_group × income_band (dedicated, no utilization split) |