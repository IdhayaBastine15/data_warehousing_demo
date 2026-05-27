"""
Dagster job that orchestrates the full pipeline:
  ingest → transform → load → experiments

Each @op is a thin wrapper that delegates to pipeline/ and experiments/ modules.
Dagster handles type checking between ops, run history, and asset lineage.

Note: get_dagster_logger() must be called inside an op (context-bound), not at
module level — calling it at module level raises a DagsterInvariantViolationError.
"""
import os

from dagster import In, Out, job, op

DB_URL         = os.getenv("DATABASE_URL",    "postgresql://dap:dap@127.0.0.1:5432/dap")
SOURCE_PATH    = os.getenv("SOURCE_PATH",     "cost_of_living_us_dap2.xls")
STAGING_PATH   = os.getenv("STAGING_PATH",   "data/staging")
PROCESSED_PATH = os.getenv("PROCESSED_PATH", "data/processed")


@op(out=Out(int))
def ingest_op(context) -> int:
    from pipeline.ingest import ingest
    count = ingest(SOURCE_PATH, STAGING_PATH)
    context.log.info("Ingested %d records", count)
    return count


@op(ins={"ingested": In(int)}, out=Out(int))
def transform_op(context, ingested: int) -> int:
    from pipeline.transform import transform
    count = transform(STAGING_PATH, PROCESSED_PATH)
    context.log.info("Transformed %d records (from %d staged)", count, ingested)
    return count


@op(ins={"transformed": In(int)}, out=Out(int))
def load_op(context, transformed: int) -> int:
    from pipeline.load import load
    count = load(PROCESSED_PATH, DB_URL)
    context.log.info("Loaded %d county rows to warehouse", count)
    return count


@op(ins={"loaded": In(int)}, out=Out(bool))
def experiment_op(context, loaded: int) -> bool:
    from sqlalchemy import create_engine
    from experiments.ab_engine import run_all_experiments, save_results

    db_engine = create_engine(DB_URL)
    for metric in ("total_cost", "affordability_ratio"):
        results = run_all_experiments(db_engine, metric=metric)
        save_results(results, db_engine)
        sig = sum(r.significant for r in results)
        context.log.info(
            "Experiments for metric=%s: %d/%d significant",
            metric, sig, len(results),
        )
    return True


@job
def etl_pipeline():
    experiment_op(load_op(transform_op(ingest_op())))
