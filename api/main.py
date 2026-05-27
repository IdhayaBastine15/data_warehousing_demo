"""
Cost of Living Experimentation Platform — REST API

Endpoints:
  GET  /health                     — liveness + DB connectivity check
  GET  /api/v1/regions             — regional cost statistics
  GET  /api/v1/states              — per-state aggregates (sorted by chosen metric)
  GET  /api/v1/counties            — county-level records (optional state filter)
  GET  /api/v1/experiments         — experiment results (filterable by metric / significance)
  POST /api/v1/experiments/run     — trigger an on-demand pairwise experiment
"""
from __future__ import annotations

import os
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, text

from pipeline.config import VALID_METRICS, VALID_REGIONS

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dap:dap@127.0.0.1:5432/dap")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(
    title="Cost of Living Experimentation Platform",
    description=(
        "Analytics API powered by a PySpark ETL pipeline on US county-level "
        "cost-of-living data. Exposes regional statistics and A/B experiment results."
    ),
    version="2.0.0",
)


class MetricEnum(str, Enum):
    total_cost          = "total_cost"
    housing_cost        = "housing_cost"
    food_cost           = "food_cost"
    healthcare_cost     = "healthcare_cost"
    childcare_cost      = "childcare_cost"
    transportation_cost = "transportation_cost"
    affordability_ratio = "affordability_ratio"


# Safe allowlist: maps each MetricEnum value to the aggregated column name used
# in the state-stats GROUP BY query. Prevents f-string SQL injection at the source.
_STATE_ORDER_COL: dict[str, str] = {
    "total_cost":          "avg_total_cost",
    "housing_cost":        "avg_housing_cost",
    "food_cost":           "avg_food_cost",
    "healthcare_cost":     "avg_healthcare_cost",
    "childcare_cost":      "avg_childcare_cost",
    "transportation_cost": "avg_transportation_cost",
    "affordability_ratio": "avg_affordability_ratio",
}


class ExperimentRequest(BaseModel):
    control_region:   str
    treatment_region: str
    metric:           str   = "total_cost"
    alpha:            float = 0.05

    @field_validator("control_region", "treatment_region")
    @classmethod
    def _validate_region(cls, v: str) -> str:
        if v not in VALID_REGIONS:
            raise ValueError(f"Must be one of {sorted(VALID_REGIONS)}")
        return v

    @field_validator("metric")
    @classmethod
    def _validate_metric(cls, v: str) -> str:
        if v not in VALID_METRICS:
            raise ValueError(f"Must be one of {sorted(VALID_METRICS)}")
        return v

    @field_validator("alpha")
    @classmethod
    def _validate_alpha(cls, v: float) -> float:
        if not 0 < v < 1:
            raise ValueError("alpha must be between 0 and 1 (exclusive)")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    """Liveness probe — also tests DB connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as exc:
        raise HTTPException(503, f"DB unreachable: {exc}") from exc


@app.get("/api/v1/regions", tags=["analytics"])
def get_regional_stats():
    """Return aggregated cost statistics for each US Census region."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM regional_cost_statistics ORDER BY avg_total_cost DESC")
        ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/states", tags=["analytics"])
def get_state_stats(
    limit:    int         = Query(20, ge=1, le=50, description="Number of states to return"),
    order_by: MetricEnum  = Query(MetricEnum.total_cost, description="Metric to sort by"),
):
    """Return per-state cost aggregates ordered by the chosen metric."""
    order_col = _STATE_ORDER_COL[order_by.value]  # safe: enum value → known column name
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT
                    state, region,
                    ROUND(AVG(total_cost),           2) AS avg_total_cost,
                    ROUND(AVG(housing_cost),         2) AS avg_housing_cost,
                    ROUND(AVG(food_cost),            2) AS avg_food_cost,
                    ROUND(AVG(healthcare_cost),      2) AS avg_healthcare_cost,
                    ROUND(AVG(median_family_income), 2) AS avg_median_income,
                    ROUND(AVG(affordability_ratio),  3) AS avg_affordability_ratio,
                    COUNT(*) AS county_count
                FROM cost_of_living_processed
                WHERE region != 'Other'
                GROUP BY state, region
                ORDER BY {order_col} DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/counties", tags=["analytics"])
def get_counties(
    state: str | None = Query(None, description="Filter by full state name"),
    limit: int        = Query(50, ge=1, le=500),
):
    """Return county-level records, optionally filtered by state."""
    if state:
        stmt   = text(
            "SELECT * FROM cost_of_living_processed "
            "WHERE state = :state ORDER BY total_cost DESC LIMIT :limit"
        )
        params: dict = {"state": state, "limit": limit}
    else:
        stmt   = text(
            "SELECT * FROM cost_of_living_processed ORDER BY total_cost DESC LIMIT :limit"
        )
        params = {"limit": limit}

    with engine.connect() as conn:
        rows = conn.execute(stmt, params).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/experiments", tags=["experiments"])
def get_experiments(
    significant_only: bool        = Query(False, description="Return only significant results"),
    metric:           MetricEnum  = Query(MetricEnum.total_cost),
):
    """Return stored experiment results, optionally filtered by significance."""
    # Use explicit branches instead of a dynamic boolean predicate so that the
    # query works identically on SQLite (INTEGER 0/1) and PostgreSQL (BOOLEAN).
    if significant_only:
        stmt = text(
            "SELECT * FROM experiment_results "
            "WHERE metric = :metric AND significant = 1 ORDER BY p_value ASC"
        )
    else:
        stmt = text(
            "SELECT * FROM experiment_results "
            "WHERE metric = :metric ORDER BY p_value ASC"
        )
    with engine.connect() as conn:
        rows = conn.execute(stmt, {"metric": metric.value}).mappings().all()
    return [dict(r) for r in rows]


@app.post("/api/v1/experiments/run", tags=["experiments"])
def trigger_experiment(body: ExperimentRequest):
    """Run a pairwise A/B experiment on-demand and persist the result."""
    if body.control_region == body.treatment_region:
        raise HTTPException(400, "control_region and treatment_region must differ")

    from experiments.ab_engine import run_experiment, save_results
    try:
        result = run_experiment(
            engine,
            body.control_region,
            body.treatment_region,
            body.metric,
            body.alpha,
        )
        save_results([result], engine)
        return result.__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
