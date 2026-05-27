"""
Local demo runner — executes the full pipeline with pandas + SQLite.
Zero infrastructure required. Production runs the same logic on PySpark + PostgreSQL
orchestrated by Dagster (orchestration/etl_job.py).

Usage:
    python3 run_demo.py

    # Then in a second terminal:
    DATABASE_URL=sqlite:///cost_of_living_demo.db uvicorn api.main:app --reload
    streamlit run dashboard.py
"""
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("demo")

# Must be set before importing api or anything that reads DATABASE_URL at import time
os.environ["DATABASE_URL"] = "sqlite:///cost_of_living_demo.db"

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from experiments.ab_engine import run_all_experiments, save_results
from pipeline.config import RAW_COLUMNS, STATE_ABBREV, STATE_TO_REGION

DB_URL = "sqlite:///cost_of_living_demo.db"
SOURCE = os.getenv("SOURCE_PATH", "cost_of_living_us_dap2.xls")
engine = create_engine(DB_URL)


def _banner(step: str) -> None:
    print(f"\n{'─' * 60}\n  {step}\n{'─' * 60}")


def _read_source(path: str) -> pd.DataFrame:
    """Detect file format by magic bytes, not extension, then read and validate."""
    with open(path, "rb") as fh:
        magic = fh.read(4)
    if magic[:2] == b"\xd0\xcf":           # OLE2 compound doc → real .xls
        raw = pd.read_excel(path, header=0)
    elif magic[:4] == b"PK\x03\x04":       # ZIP-based → .xlsx
        raw = pd.read_excel(path, header=0, engine="openpyxl")
    else:                                   # Text file (CSV, or CSV with .xls extension)
        raw = pd.read_csv(path, encoding="latin-1", low_memory=False)

    if raw.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"Expected {len(RAW_COLUMNS)} columns, found {raw.shape[1]} in {path}. "
            "Check the source file."
        )
    raw.columns = list(RAW_COLUMNS)
    return raw


# ── Step 1: Ingest ─────────────────────────────────────────────────────────────
_banner("STEP 1 / 4  |  INGEST")

if not Path(SOURCE).exists():
    log.error("Source file not found: %s", SOURCE)
    sys.exit(1)

raw = _read_source(SOURCE)
raw = raw.drop(columns=["isMetro"], errors="ignore")
log.info("Loaded %d raw records from %s", len(raw), SOURCE)


# ── Step 2: Transform ─────────────────────────────────────────────────────────
_banner("STEP 2 / 4  |  TRANSFORM")

df = raw.copy()

# Expand state abbreviations
df["state"] = df["state"].map(STATE_ABBREV).fillna(df["state"])

# Normalise strings — split on underscore, keep first token, strip whitespace
df["county"]   = df["county"].astype(str).str.split("_").str[0].str.strip()
df["areaname"] = df["areaname"].astype(str).str.split("_").str[0].str.strip()

# Coerce numeric cost columns; fill nulls with 0
_COST_COLS = [
    "housing_cost", "food_cost", "transportation_cost", "healthcare_cost",
    "other_necessities_cost", "childcare_cost", "taxes",
]
for col in _COST_COLS + ["total_cost", "median_family_income"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

# Recompute total_cost from components when the recorded value is 0
component_sum       = df[_COST_COLS].sum(axis=1)
zero_total          = df["total_cost"] == 0.0
df.loc[zero_total, "total_cost"] = component_sum[zero_total]

# Deduplicate on the composite natural key — county names repeat across states
# (e.g. "Jefferson County" exists in 25 states; deduplicating on county alone
# would silently destroy valid data)
before = len(df)
df = df.drop_duplicates(subset=["state", "county"])
log.info("Deduplicated: %d → %d rows (kept unique state+county pairs)", before, len(df))

# Derived metrics — affordability_ratio guarded against division by zero
df["affordability_ratio"] = np.where(
    df["total_cost"] > 0,
    (df["median_family_income"] / df["total_cost"]).round(3),
    np.nan,
)
df["region"] = df["state"].map(STATE_TO_REGION).fillna("Other")

region_counts = df["region"].value_counts()
print("\nRegion distribution:")
for r, c in region_counts.items():
    print(f"  {r:<12} {c:>4} counties")

df.to_sql("cost_of_living_processed", engine, if_exists="replace", index=False)
log.info("Written %d rows → cost_of_living_processed", len(df))


# ── Step 3: Load — regional aggregates ────────────────────────────────────────
_banner("STEP 3 / 4  |  LOAD — REGIONAL AGGREGATES")

regional = (
    df[df["region"] != "Other"]
    .groupby("region", sort=False)
    .agg(
        avg_total_cost          = ("total_cost",             "mean"),
        avg_housing_cost        = ("housing_cost",           "mean"),
        avg_food_cost           = ("food_cost",              "mean"),
        avg_healthcare_cost     = ("healthcare_cost",        "mean"),
        avg_childcare_cost      = ("childcare_cost",         "mean"),
        avg_transportation_cost = ("transportation_cost",    "mean"),
        avg_median_income       = ("median_family_income",   "mean"),
        avg_affordability_ratio = ("affordability_ratio",    "mean"),
        county_count            = ("total_cost",             "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("avg_total_cost", ascending=False)
)

regional.to_sql("regional_cost_statistics", engine, if_exists="replace", index=False)
log.info("Written %d regional rows → regional_cost_statistics", len(regional))

print("\nRegional Cost of Living (annual, USD):")
_display = ["region", "avg_total_cost", "avg_housing_cost",
            "avg_median_income", "avg_affordability_ratio", "county_count"]
print(regional[_display].to_string(index=False))


# ── Step 4: A/B Experiments ────────────────────────────────────────────────────
_banner("STEP 4 / 4  |  A/B EXPERIMENTS")

all_results = []
for metric in ("total_cost", "housing_cost", "affordability_ratio"):
    results = run_all_experiments(engine, metric=metric)
    save_results(results, engine)   # upsert — safe to call multiple times
    all_results.extend(results)

sig_results = [r for r in all_results if r.significant]
print(f"\n{len(all_results)} experiments run — {len(sig_results)} significant at p < 0.05\n")
print(f"{'Experiment':<45} {'p-value':>8} {'Cohen d':>8} {'Lift%':>7}  {'Winner'}")
print("─" * 90)
for r in sorted(all_results, key=lambda x: x.p_value):
    flag  = "✓" if r.significant else " "
    label = f"{r.control_region} vs {r.treatment_region} [{r.metric}]"
    print(f"{flag} {label:<43} {r.p_value:>8.4f} {r.cohens_d:>8.3f} {r.lift_pct:>7.1f}%  {r.winner}")


# ── Create indexes for API query performance ───────────────────────────────────
with engine.begin() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_col_state   ON cost_of_living_processed (state)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_col_region  ON cost_of_living_processed (region)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_col_county  ON cost_of_living_processed (county)"))

print(f"""
{'═' * 60}
  Pipeline complete — SQLite DB: cost_of_living_demo.db

  Start the REST API (separate terminal):
    DATABASE_URL=sqlite:///cost_of_living_demo.db \\
    uvicorn api.main:app --reload

  Start the dashboard (separate terminal):
    streamlit run dashboard.py

  Quick smoke-test:
    curl http://localhost:8000/health
    curl http://localhost:8000/api/v1/regions
    curl "http://localhost:8000/api/v1/states?limit=10"
    curl "http://localhost:8000/api/v1/counties?state=California&limit=20"
    curl "http://localhost:8000/api/v1/experiments?significant_only=true"
{'═' * 60}
""")
