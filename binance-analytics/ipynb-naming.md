## Repository Structure & Notebook Conventions

This repository enforces pragmatic structural hygiene to maintain modularity and prevent pipeline clutter as the algorithmic engine scales.

### 1. Naming Standard
- **Casing:** All filenames must use `snake_case` exclusively. No spaces, no hyphens.
- **Format:** `[Functional Prefix]_[Subject]_[Action].ipynb`
- **Numerical Ordering (Optional):** Use `_01_`, `_02_` sequences **only when execution order matters** (e.g., ETL pipelines with dependencies). For independent notebooks (EDA, experimentation, feature exploration), omit numbers to reduce overhead.

### 2. Functional Prefixes

Every notebook must lead with one of these approved prefixes to group files by their layer in the engineering stack:

| Prefix | Domain Lifecycle Phase | Core Operational Focus |
| :--- | :--- | :--- |
| `etl_` | Extract, Transform, Load | BigQuery data ingestion, historical bootstrapping, delta accumulation. |
| `qa_`  | Quality Assurance & Validation | Schema integrity verification, outlier detection, data sanity parsing. |
| `eda_` | Exploratory Data Analysis | Data profiling, asset liquidity mapping, statistical distributions. |
| `feat_`| Feature Engineering | Alpha factor generation, moving averages, mathematical derivatives. |
| `sim_` | Simulation & Backtesting | Backtesting execution loops, signal performance verifications. |
| `exp_` | Experimentation & Scratchpad | Short-lived algorithmic prototypes and sandboxed code exploration. |
| `viz_` | Visualization | Pure charting and reporting (distinct from analysis-heavy EDA). |
| `ml_`  | Machine Learning | Model training, hyperparameter tuning, inference, evaluation. |

### 3. Action Suffixes (by Functional Area)

The `_[Action]` suffix describes the specific operation performed.

| Functional Prefix | Common Action Suffixes | Example |
| :--- | :--- | :--- |
| `etl_` | `_bootstrap`, `_delta`, `_load`, `_merge` | `etl_cse_bootstrap.ipynb` |
| `qa_`  | `_schema_check`, `_outlier_detect`, `_null_analysis`, `_duplicate_check` | `qa_cse_schema_check.ipynb` |
| `eda_` | `_profile`, `_distributions`, `_correlations`, `_missing`, `_trends` | `eda_liquidity_profile.ipynb` |
| `feat_`| `_create`, `_transform`, `_select`, `_scale`, `_encode` | `feat_moving_averages_create.ipynb` |
| `sim_` | `_backtest`, `_walkforward`, `_monte_carlo`, `_stress_test` | `sim_strategy_backtest.ipynb` |
| `exp_` | `_prototype`, `_sandbox`, `_test_hypothesis` | `exp_stochastic_prototype.ipynb` |
| `viz_` | `_dashboard`, `_timeseries`, `_heatmap`, `_distribution` | `viz_returns_distribution.ipynb` |
| `ml_`  | `_train`, `_validate`, `_tune`, `_inference`, `_evaluate` | `ml_credit_risk_train.ipynb` |

### 4. Unified Directory Layout

```text
├── config/                     # Global system configurations and schema definitions
│   └── bq_schemas.json         # Hard schemas for BigQuery tables
├── ingest/                     # Production codebase (C++ engine / Python core)
│   ├── bq_pipeline.py          # Stable, automated daily delta accumulator scripts
│   └── client.py               # Optimized BigQuery initialization clients
├── notebooks/                  # Interactive research and verification sandbox
│   ├── etl_01_cse_bootstrap.ipynb   # Numbers used: must run before delta
│   ├── etl_02_cse_delta.ipynb       # Numbers used: depends on bootstrap
│   ├── qa_schema_checks.ipynb       # No number: independent check
│   ├── eda_liquidity_profile.ipynb  # No number: standalone exploration
│   ├── feat_moving_averages_create.ipynb
│   ├── ml_train_strategy.ipynb
│   └── exp_stochastic_sandbox.ipynb
└── tests/                      # Native unit testing suites