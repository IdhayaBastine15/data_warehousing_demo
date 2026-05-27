"""
Load layer — writes processed Parquet data to the warehouse (PostgreSQL or SQLite).

Two tables are maintained:
  cost_of_living_processed   — county-level granularity (replace on each run)
  regional_cost_statistics   — pre-aggregated regional summary (replace on each run)

Each run stamps a run_id + loaded_at for data lineage.
Indexes are created (or skipped if they already exist) on the most-queried columns.
"""
import logging
import uuid
from datetime import datetime, timezone

import pandas as pd
from pyspark.sql import DataFrame
from sqlalchemy import Engine, create_engine, text

from pipeline.ingest import get_spark

log = logging.getLogger(__name__)

_INDEX_DDL: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_col_state   ON cost_of_living_processed (state)",
    "CREATE INDEX IF NOT EXISTS idx_col_region  ON cost_of_living_processed (region)",
    "CREATE INDEX IF NOT EXISTS idx_col_county  ON cost_of_living_processed (county)",
    "CREATE INDEX IF NOT EXISTS idx_rcs_region  ON regional_cost_statistics (region)",
]


def _create_indexes(engine: Engine) -> None:
    with engine.begin() as conn:
        for stmt in _INDEX_DDL:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                log.debug("Index skipped (%s): %s", type(exc).__name__, stmt)


def load(
    processed_path: str,
    db_url: str = "postgresql://dap:dap@127.0.0.1:5432/dap",
) -> int:
    """
    Load county-level and regional-aggregate data into the warehouse.
    Returns the number of county-level rows loaded.
    """
    spark = get_spark()
    engine = create_engine(db_url, pool_pre_ping=True)
    run_id    = str(uuid.uuid4())
    loaded_at = datetime.now(timezone.utc).isoformat()

    df: DataFrame = spark.read.parquet(processed_path)
    df.createOrReplaceTempView("cost_of_living")

    # County-level load
    county_pd = df.toPandas()
    county_pd["run_id"]    = run_id
    county_pd["loaded_at"] = loaded_at
    county_pd.to_sql(
        "cost_of_living_processed", engine,
        if_exists="replace", index=False, chunksize=500,
    )
    log.info(
        "Loaded %d county rows → cost_of_living_processed (run=%s)",
        len(county_pd), run_id,
    )

    # Regional aggregates via Spark SQL
    regional_df: DataFrame = spark.sql("""
        SELECT
            region,
            ROUND(AVG(total_cost),            2) AS avg_total_cost,
            ROUND(AVG(housing_cost),          2) AS avg_housing_cost,
            ROUND(AVG(food_cost),             2) AS avg_food_cost,
            ROUND(AVG(healthcare_cost),       2) AS avg_healthcare_cost,
            ROUND(AVG(childcare_cost),        2) AS avg_childcare_cost,
            ROUND(AVG(transportation_cost),   2) AS avg_transportation_cost,
            ROUND(AVG(median_family_income),  2) AS avg_median_income,
            ROUND(AVG(affordability_ratio),   3) AS avg_affordability_ratio,
            COUNT(*)                             AS county_count
        FROM cost_of_living
        WHERE region != 'Other'
        GROUP BY region
        ORDER BY avg_total_cost DESC
    """)

    regional_pd = regional_df.toPandas()
    regional_pd["run_id"]    = run_id
    regional_pd["loaded_at"] = loaded_at
    regional_pd.to_sql(
        "regional_cost_statistics", engine,
        if_exists="replace", index=False,
    )
    log.info("Loaded %d regions → regional_cost_statistics", len(regional_pd))

    _create_indexes(engine)
    return len(county_pd)
