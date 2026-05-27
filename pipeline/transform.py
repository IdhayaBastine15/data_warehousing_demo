"""
Transform layer — cleans, enriches, and partitions cost-of-living data using PySpark.

Key operations:
  1. Expand state abbreviations via broadcast join
  2. Normalise county / areaname strings (split on underscore, strip whitespace)
  3. Fill nulls; coerce numeric types; recompute total_cost if it is 0
  4. Deduplicate on (state, county) — the natural composite key
     NOTE: county names repeat across states (e.g. "Jefferson County" in 25 states)
           deduplicating on county alone would silently destroy valid data
  5. Derive: affordability_ratio (guarded against division by zero), region label
  6. Partition output by region for predicate-pushdown efficiency
"""
import logging

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType

from pipeline.config import REGION_MAP, STATE_ABBREV
from pipeline.ingest import get_spark

log = logging.getLogger(__name__)

_COST_COLS = (
    "housing_cost", "food_cost", "transportation_cost", "healthcare_cost",
    "other_necessities_cost", "childcare_cost", "taxes",
)


def _region_expr() -> F.Column:
    expr = None
    for region, states in REGION_MAP.items():
        cond = F.col("state").isin(states)
        expr = F.when(cond, F.lit(region)) if expr is None else expr.when(cond, F.lit(region))
    return expr.otherwise(F.lit("Other"))


def transform(staging_path: str, processed_path: str = "data/processed") -> int:
    spark = get_spark()
    df: DataFrame = spark.read.parquet(staging_path)

    # 1. Expand state abbreviations via broadcast join
    abbrev_df = spark.createDataFrame(list(STATE_ABBREV.items()), ["abbrev", "full_name"])
    df = (
        df.join(F.broadcast(abbrev_df), df["state"] == abbrev_df["abbrev"], "left")
          .withColumn("state", F.coalesce(F.col("full_name"), F.col("state")))
          .drop("abbrev", "full_name")
    )

    # 2. Normalise strings — split on underscore, keep first token, trim whitespace
    for col in ("county", "areaname"):
        df = df.withColumn(col, F.trim(F.split(F.col(col), "_")[0]))

    # 3. Fill nulls and coerce numeric types
    null_defaults: dict = {c: 0.0 for c in _COST_COLS}
    null_defaults["total_cost"] = 0.0
    null_defaults["median_family_income"] = 0.0
    df = df.fillna(null_defaults)
    for c in (*_COST_COLS, "total_cost"):
        df = df.withColumn(c, F.col(c).cast(FloatType()))

    # Recompute total_cost from components when recorded value is 0 but parts are not
    component_sum = sum(F.col(c) for c in _COST_COLS)
    df = df.withColumn(
        "total_cost",
        F.when(F.col("total_cost") == 0.0, component_sum).otherwise(F.col("total_cost")),
    )

    # 4. Deduplicate on the composite natural key — county names repeat across states
    before = df.count()
    df = df.dropDuplicates(["state", "county"])
    log.info("Deduplicated: %d → %d rows", before, df.count())

    # 5. Derived metrics
    df = (
        df.withColumn(
            "affordability_ratio",
            F.when(
                F.col("total_cost") > 0.0,
                F.round(F.col("median_family_income") / F.col("total_cost"), 3),
            ).otherwise(F.lit(None).cast(FloatType())),
        )
        .withColumn("region", _region_expr())
    )

    # 6. Partition by region for predicate-pushdown on downstream reads
    df.write.mode("overwrite").partitionBy("region").parquet(processed_path)
    count = df.count()
    log.info("Transformed %d records → %s (partitioned by region)", count, processed_path)
    return count
