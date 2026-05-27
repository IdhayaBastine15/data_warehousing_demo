# Cost of Living Experimentation Platform

This project is a full end-to-end data pipeline built to process US county-level cost-of-living data, run statistical A/B experiments across regions, and serve results through a REST API and interactive dashboard. It was designed to mirror how data platforms are built in production — with PySpark for distributed processing, Dagster for orchestration, PostgreSQL as the warehouse, and FastAPI on top.

The demo mode runs entirely on your laptop using pandas and SQLite — no infrastructure needed. The production path uses the exact same logic but on PySpark and PostgreSQL, orchestrated through Dagster.

---

## What it actually does

The pipeline pulls raw county-level data from the Economic Policy Institute's Family Budget Calculator — about 31,000 records covering housing, food, transport, healthcare, childcare, taxes, and median family income for every US county. It cleans and enriches that data, loads it into a warehouse, then runs pairwise statistical tests across the five US Census regions to answer questions like:

- Does the Midwest cost significantly less to live in than the Northeast?
- Is California's affordability ratio statistically different from Texas's?
- Which region offers the best income-to-cost ratio, and how confident are we in that?

Every experiment produces a p-value, Cohen's d effect size, a 95% confidence interval, and a clear winner — the same statistical rigour you'd apply in a production A/B testing platform.

---

## Pipeline architecture

```
Raw source (CSV/XLS)
        │
        ▼
┌───────────────────┐
│  INGEST           │  Magic-byte file detection → schema enforcement → Parquet staging
│  pipeline/ingest  │
└────────┬──────────┘
         │  data/staging/  (Parquet)
         ▼
┌───────────────────┐
│  TRANSFORM        │  State expansion (broadcast join) → string normalisation
│  pipeline/        │  Dedup on (state, county) → affordability_ratio → region label
│  transform        │  Partitioned output by region for predicate-pushdown efficiency
└────────┬──────────┘
         │  data/processed/  (Parquet, partitioned by region)
         ▼
┌───────────────────┐
│  LOAD             │  County-level → cost_of_living_processed
│  pipeline/load    │  Spark SQL aggregates → regional_cost_statistics
│                   │  run_id + loaded_at on every row for lineage
└────────┬──────────┘
         │
         ▼
┌────────────────────────┐
│  EXPERIMENT ENGINE     │  Welch's t-test · Cohen's d · 95% CI
│  experiments/          │  Pairwise across all 5 regions × 7 metrics
│  ab_engine             │  Upsert results — never overwrites unrelated experiments
└────────┬───────────────┘
         │
         ▼
┌───────────────────┐     ┌──────────────────────┐
│  REST API         │     │  Streamlit Dashboard  │
│  api/main.py      │     │  dashboard.py         │
│  :8000            │     │  :8501                │
└───────────────────┘     └──────────────────────┘

All of the above is orchestrated by Dagster (orchestration/etl_job.py)
```

---

## Tech stack

**PySpark 3.5** handles the heavy lifting in the pipeline — schema enforcement, broadcast joins, window functions, and partitioned Parquet writes. The code is written to run on `local[*]` for development but works unchanged on a Databricks or EMR cluster by swapping the SparkSession config.

**Dagster** orchestrates the four pipeline stages, enforcing type contracts between ops and giving you run history and asset lineage out of the box.

**PostgreSQL** (or SQLite for local demo) stores the three output tables. Indexes are created automatically on `state`, `region`, and `county` so API queries stay fast.

**SciPy** powers the experiment engine. Welch's t-test is used instead of Student's t-test because the cost variance genuinely differs between regions — using the pooled-variance version would inflate false positives.

**FastAPI** serves the results. Everything is validated through Pydantic models and the interactive docs live at `/docs`.

**Streamlit + Plotly** for the dashboard — regional radar charts, county drill-downs, confidence interval forest plots, and the full experiment results table.

---

## Getting started

### Demo mode (no infrastructure)

```bash
# Clone and enter the project
git clone <repo-url>
cd data_warehousing_demo

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline — takes about 10 seconds
python3 run_demo.py
```

That writes everything to `cost_of_living_demo.db`. Then in separate terminals:

```bash
# Start the API
DATABASE_URL=sqlite:///cost_of_living_demo.db uvicorn api.main:app --reload

# Start the dashboard
streamlit run dashboard.py
```

API: http://localhost:8000/docs  
Dashboard: http://localhost:8501

### Production mode with Docker

```bash
docker-compose up --build
```

This starts PostgreSQL, the FastAPI server, and the Streamlit dashboard. Then run the pipeline:

```bash
docker-compose exec api dagster job execute -f orchestration/etl_job.py -j etl_pipeline
```

---

## Project structure

```
data_warehousing_demo/
│
├── pipeline/
│   ├── config.py        ← Shared constants: STATE_ABBREV, REGION_MAP, VALID_METRICS, etc.
│   ├── ingest.py        ← File format detection, schema enforcement, Parquet staging
│   ├── transform.py     ← Cleaning, enrichment, deduplication, partitioned output
│   └── load.py          ← Warehouse write + regional aggregates + index creation
│
├── experiments/
│   └── ab_engine.py     ← Welch t-test, Cohen's d, 95% CI, upsert-safe persistence
│
├── orchestration/
│   └── etl_job.py       ← Dagster @op + @job wiring the four stages together
│
├── api/
│   └── main.py          ← FastAPI routes with enum-validated query params
│
├── dashboard.py         ← Streamlit dashboard (4 pages: Overview, Regional, State, Experiments)
├── run_demo.py          ← Zero-infra demo runner using pandas + SQLite
├── docker-compose.yml   ← PostgreSQL + API + Dashboard services
├── Dockerfile
└── requirements.txt
```

---

## API reference

| Method | Endpoint | What it returns |
|--------|----------|-----------------|
| GET | `/health` | Liveness check + DB connectivity status |
| GET | `/api/v1/regions` | Aggregated cost stats for each US Census region |
| GET | `/api/v1/states` | Per-state averages, sortable by any cost metric |
| GET | `/api/v1/counties` | County-level records, filterable by state |
| GET | `/api/v1/experiments` | Experiment results, filterable by metric and significance |
| POST | `/api/v1/experiments/run` | Run a new pairwise experiment on-demand |

Quick examples:

```bash
# Check the service is up
curl http://localhost:8000/health

# Regional breakdown
curl http://localhost:8000/api/v1/regions

# Top 10 states by housing cost
curl "http://localhost:8000/api/v1/states?limit=10&order_by=housing_cost"

# All counties in California, sorted by total cost
curl "http://localhost:8000/api/v1/counties?state=California&limit=50"

# Only the statistically significant experiments for total cost
curl "http://localhost:8000/api/v1/experiments?significant_only=true&metric=total_cost"

# Kick off a new experiment between two regions
curl -X POST http://localhost:8000/api/v1/experiments/run \
  -H "Content-Type: application/json" \
  -d '{"control_region": "Midwest", "treatment_region": "Northeast", "metric": "housing_cost"}'
```

---

## How the experiments work

The engine compares any cost metric between two regions using a pairwise Welch's t-test. Each comparison produces:

- **p-value** — how likely this difference is under the null hypothesis (threshold: 0.05)
- **Cohen's d** — the effect size. Values below 0.2 are negligible; above 0.8 is large
- **95% confidence interval** — the range we expect the true mean difference to fall within
- **Lift %** — the relative change from control to treatment
- **Winner** — the region with the statistically better outcome, or `no_winner` if the result is not significant

For cost metrics (housing, food, etc.) lower is better. For `affordability_ratio` (income divided by total cost), higher is better.

Available metrics: `total_cost`, `housing_cost`, `food_cost`, `healthcare_cost`, `childcare_cost`, `transportation_cost`, `affordability_ratio`

Available regions: `Northeast`, `Southeast`, `Midwest`, `Southwest`, `West`

---

## Data source

Economic Policy Institute — Family Budget Calculator  
~31,000 records covering US counties across nine cost categories.  
The raw file is a CSV exported with an `.xls` extension (common in older government data systems). The pipeline detects this by reading the file's magic bytes rather than trusting the extension.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://dap:dap@127.0.0.1:5432/dap` | SQLAlchemy connection string |
| `SOURCE_PATH` | `cost_of_living_us_dap2.xls` | Path to the raw source file |
| `STAGING_PATH` | `data/staging` | Parquet staging zone |
| `PROCESSED_PATH` | `data/processed` | Parquet processed zone (partitioned by region) |

For local demo, `DATABASE_URL` is automatically set to `sqlite:///cost_of_living_demo.db` by `run_demo.py`.
