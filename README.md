# Credit Risk Analysis — Loan Portfolio Case Study

A end-to-end credit risk analysis project built with PostgreSQL, Python, and Plotly.  
This project simulates a real analyst workflow: ingesting raw loan data, applying business-driven cleaning rules in SQL, extracting insights with window functions and CTEs, and presenting findings through an interactive dashboard.

---

## Business Problem

A consumer lending institution wants to understand the risk profile of its loan portfolio.  
The core questions driving this analysis are:

- Which borrower segments carry the highest default risk?
- How strongly does delinquency history predict future default?
- Where is default risk concentrated across the portfolio?

---

## Key Findings

| Finding | Detail |
|---|---|
| Credit utilization is the strongest default predictor | Borrowers above 90% utilization default at 19–28%, vs 3–5% for low-utilization borrowers |
| A single delinquency event multiplies risk by 4.5x | Clean borrowers default at 2.7%; one event pushes that to 12.2% |
| Risk is highly concentrated | The top 9 segments account for over 68% of all portfolio defaults |
| Income alone does not predict risk | High-income borrowers with critical utilization still default at 19%+ |

---

## Project Structure
```
credit-risk-analysis/
├── data/
│   ├── raw/                  # Original Kaggle CSV (not versioned)
│   └── processed/            # Cleaned outputs from analysis layer
├── sql/
│   ├── schema/               # Table creation and cleaning scripts
│   └── queries/              # Analytical CTEs and window function queries
├── src/
│   ├── ingestion/            # CSV → PostgreSQL loader
│   ├── analysis/             # Pandas analysis and metric extraction
│   └── visualization/        # Plotly interactive dashboard
├── outputs/
│   └── figures/              # Exported HTML dashboard
├── docs/
│   └── data_dictionary.md    # Column definitions and business meaning
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Database | PostgreSQL 15 | Schema, cleaning, analytical queries |
| SQL Patterns | CTEs + Window Functions | Segmentation, ranking, concentration |
| Data Layer | Python + Pandas | Extraction, metric computation |
| Visualization | Plotly | Interactive dashboard |
| Environment | Docker | Portable PostgreSQL instance |
| Version Control | Git + branching strategy | Feature branches → dev → main |

---

## Dataset

**Source:** [Give Me Some Credit — Kaggle](https://www.kaggle.com/competitions/GiveMeSomeCredit/data)  
**Size:** 150,000 borrower records  
**Target variable:** `SeriousDlqin2yrs` — whether the borrower experienced 90+ day delinquency within 2 years

The raw data is not versioned. Download `cs-training.csv` from Kaggle and place it at `data/raw/cs-training.csv`.

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/your-username/credit-risk-analysis.git
cd credit-risk-analysis
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL via Docker
```bash
docker run --name credit-risk-db \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 -d postgres:15
```

### 5. Configure credentials
Create `config/db_config.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credit_risk
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### 6. Load data
```bash
python src/ingestion/load_data.py
```

### 7. Build cleaned table
```bash
Get-Content sql/schema/02_create_clean_table.sql | docker exec -i credit-risk-db psql -U postgres -d credit_risk
```

### 8. Run analysis
```bash
python src/analysis/credit_risk_analysis.py
```

### 9. Launch dashboard
```bash
python src/visualization/dashboard.py
```

---

## SQL Highlights

This project uses PostgreSQL-specific features to perform analytical work directly in the database layer:

**Layered CTEs for data cleaning** — transformations are applied once and reused downstream, avoiding redundant expressions.

**Window functions for segmentation ranking:**
```sql
RANK() OVER (
    PARTITION BY age_group
    ORDER BY default_rate_pct DESC
) AS risk_rank_within_age_group
```

**Cumulative default concentration:**
```sql
SUM(total_defaults * 100.0 / grand_total_defaults) OVER (
    ORDER BY default_rate_pct DESC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS cumulative_default_share_pct
```

---

## Git Workflow

This project follows a structured branching strategy:
```
main          ← stable, always presentable
└── dev       ← integration branch
    ├── feature/data-ingestion
    ├── feature/sql-schema
    ├── feature/sql-analytics
    ├── feature/python-analysis
    ├── feature/plotly-dashboard
    └── feature/readme
```

---

## Next Steps

This project is designed as a baseline for more advanced credit risk work:

- **Scorecard development** — logistic regression to produce borrower-level PD scores
- **IFRS 9 staging simulation** — classify borrowers into Stage 1/2/3 buckets
- **ML model comparison** — XGBoost vs logistic regression for PD estimation
- **Cohort analysis** — track default rates over time by origination period