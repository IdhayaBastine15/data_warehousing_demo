"""
Ingestion layer — reads raw XLS/CSV source into Parquet staging zone.
Uses PySpark for schema enforcement and scalable I/O.
"""
import logging
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    FloatType, IntegerType, StringType, StructField, StructType,
)

from pipeline.config import RAW_COLUMNS

log = logging.getLogger(__name__)

# Schema for the staging zone — isMetro is dropped before this is applied
STAGING_SCHEMA = StructType([
    StructField("case_id",                IntegerType(), True),
    StructField("state",                  StringType(),  True),
    StructField("areaname",               StringType(),  True),
    StructField("county",                 StringType(),  True),
    StructField("housing_cost",           FloatType(),   True),
    StructField("food_cost",              FloatType(),   True),
    StructField("transportation_cost",    FloatType(),   True),
    StructField("healthcare_cost",        FloatType(),   True),
    StructField("other_necessities_cost", FloatType(),   True),
    StructField("childcare_cost",         FloatType(),   True),
    StructField("taxes",                  FloatType(),   True),
    StructField("total_cost",             FloatType(),   True),
    StructField("median_family_income",   FloatType(),   True),
])


def get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("CostOfLivingPipeline")
        .master("local[*]")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .getOrCreate()
    )


def _read_source(source_path: str) -> pd.DataFrame:
    """
    Detect file format by magic bytes (not extension) then read.
    Many government CSVs ship with a .xls extension — handle both.
    Validates column count before returning.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    with open(source_path, "rb") as fh:
        magic = fh.read(4)

    if magic[:2] == b"\xd0\xcf":           # OLE2 compound doc → real .xls
        raw = pd.read_excel(source_path, header=0)
    elif magic[:4] == b"PK\x03\x04":       # ZIP-based → .xlsx
        raw = pd.read_excel(source_path, header=0, engine="openpyxl")
    else:                                   # Text file (CSV with any extension)
        raw = pd.read_csv(source_path, encoding="latin-1", low_memory=False)

    if raw.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"Expected {len(RAW_COLUMNS)} columns, got {raw.shape[1]}. "
            f"Check the source file format: {source_path}"
        )
    raw.columns = list(RAW_COLUMNS)
    return raw


def ingest(source_path: str, staging_path: str = "data/staging") -> int:
    """
    Read the raw source, drop unused columns, enforce schema, write Parquet.
    Returns the number of records written.
    """
    spark = get_spark()
    raw_pd = _read_source(source_path)
    raw_pd = raw_pd.drop(columns=["isMetro"], errors="ignore")
    log.info("Read %d raw records from %s", len(raw_pd), source_path)

    df: DataFrame = spark.createDataFrame(raw_pd, schema=STAGING_SCHEMA)

    # Cache before write+count to avoid reading Parquet back just for the count
    df.cache()
    df.write.mode("overwrite").parquet(staging_path)
    count = df.count()
    df.unpersist()

    log.info("Staged %d records → %s", count, staging_path)
    return count
