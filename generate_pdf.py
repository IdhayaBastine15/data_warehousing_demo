"""
Generates a comprehensive PDF documentation for the Cost of Living Experimentation Platform.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

OUTPUT = "Cost_of_Living_Platform_Documentation.pdf"

# ── Colour palette ────────────────────────────────────────────────────────────
DARK_BG   = colors.HexColor("#1E1E2E")
CODE_BG   = colors.HexColor("#2A2A3E")
ACCENT    = colors.HexColor("#7C3AED")   # purple
ACCENT2   = colors.HexColor("#06B6D4")   # cyan
GREEN     = colors.HexColor("#10B981")
ORANGE    = colors.HexColor("#F59E0B")
TEXT_DARK = colors.HexColor("#1F2937")
LIGHT_GRAY= colors.HexColor("#F3F4F6")
BORDER    = colors.HexColor("#E5E7EB")

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    "MyTitle",
    parent=styles["Title"],
    fontSize=28, textColor=ACCENT,
    spaceAfter=8, leading=34,
    alignment=TA_CENTER,
)
subtitle_style = ParagraphStyle(
    "MySubtitle",
    parent=styles["Normal"],
    fontSize=13, textColor=TEXT_DARK,
    spaceAfter=4, leading=18,
    alignment=TA_CENTER,
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=18, textColor=ACCENT,
    spaceBefore=20, spaceAfter=8, leading=24,
    borderPad=4,
)
h2_style = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=14, textColor=ACCENT2,
    spaceBefore=14, spaceAfter=6, leading=18,
)
h3_style = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontSize=12, textColor=GREEN,
    spaceBefore=10, spaceAfter=4, leading=16,
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=10, textColor=TEXT_DARK,
    spaceAfter=6, leading=15,
    alignment=TA_JUSTIFY,
)
bullet_style = ParagraphStyle(
    "Bullet", parent=styles["Normal"],
    fontSize=10, textColor=TEXT_DARK,
    spaceAfter=3, leading=14,
    leftIndent=16, bulletIndent=4,
)
code_style = ParagraphStyle(
    "Code", parent=styles["Code"],
    fontSize=7.5,
    fontName="Courier",
    textColor=colors.HexColor("#E2E8F0"),
    backColor=CODE_BG,
    leading=11,
    leftIndent=6, rightIndent=6,
    spaceAfter=10, spaceBefore=4,
    borderPad=6,
)
label_style = ParagraphStyle(
    "Label", parent=styles["Normal"],
    fontSize=9, textColor=colors.white,
    backColor=ACCENT,
    leading=13,
    leftIndent=6, spaceAfter=0, spaceBefore=6,
    fontName="Helvetica-Bold",
)
note_style = ParagraphStyle(
    "Note", parent=styles["Normal"],
    fontSize=9, textColor=TEXT_DARK,
    backColor=colors.HexColor("#FEF3C7"),
    leading=13, leftIndent=8, rightIndent=8,
    spaceAfter=8, spaceBefore=4,
    borderPad=6,
)

def h(text, style=h1_style):
    return Paragraph(text, style)

def p(text, style=body_style):
    return Paragraph(text, style)

def b(text):
    return Paragraph(f"• {text}", bullet_style)

def code_block(label, code_text):
    items = []
    items.append(Paragraph(f"  {label}", label_style))
    items.append(Preformatted(code_text.strip(), code_style))
    return items

def hr():
    return HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8, spaceBefore=4)

# ═══════════════════════════════════════════════════════════════════════════════
# Content builder
# ═══════════════════════════════════════════════════════════════════════════════
story = []

# ── COVER PAGE ────────────────────────────────────────────────────────────────
story.append(Spacer(1, 3*cm))
story.append(Paragraph("Cost of Living", title_style))
story.append(Paragraph("Experimentation Platform", title_style))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("End-to-End Data Pipeline Documentation", subtitle_style))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("PySpark · PostgreSQL · FastAPI · Dagster · A/B Testing", subtitle_style))
story.append(Spacer(1, 1*cm))
story.append(hr())
story.append(Spacer(1, 0.5*cm))

cover_data = [
    ["Author",    "Idhaya Bastine Kennedy"],
    ["Dataset",   "EPI Family Budget Calculator (~3,000 US Counties)"],
    ["Language",  "Python 3.11"],
    ["Date",      "May 2026"],
]
cover_table = Table(cover_data, colWidths=[4*cm, 11*cm])
cover_table.setStyle(TableStyle([
    ("FONTNAME",   (0,0),(-1,-1), "Helvetica"),
    ("FONTSIZE",   (0,0),(-1,-1), 10),
    ("FONTNAME",   (0,0),(0,-1),  "Helvetica-Bold"),
    ("TEXTCOLOR",  (0,0),(0,-1),  ACCENT),
    ("TEXTCOLOR",  (1,0),(1,-1),  TEXT_DARK),
    ("ROWBACKGROUNDS", (0,0),(-1,-1), [LIGHT_GRAY, colors.white]),
    ("GRID",       (0,0),(-1,-1), 0.5, BORDER),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 10),
]))
story.append(cover_table)
story.append(PageBreak())

# ── TABLE OF CONTENTS ─────────────────────────────────────────────────────────
story.append(h("Table of Contents"))
toc_items = [
    ("1", "Project Overview & Architecture"),
    ("2", "Dataset"),
    ("3", "Technology Stack"),
    ("4", "Ingest Layer — pipeline/ingest.py"),
    ("5", "Transform Layer — pipeline/transform.py"),
    ("6", "Load Layer — pipeline/load.py"),
    ("7", "A/B Experiment Engine — experiments/ab_engine.py"),
    ("8", "Orchestration — orchestration/etl_job.py"),
    ("9", "REST API — api/main.py"),
    ("10","Local Demo Runner — run_demo.py"),
    ("11","How To See the Output"),
]
toc_table = Table(toc_items, colWidths=[1.5*cm, 13.5*cm])
toc_table.setStyle(TableStyle([
    ("FONTNAME",   (0,0),(-1,-1), "Helvetica"),
    ("FONTSIZE",   (0,0),(-1,-1), 10),
    ("FONTNAME",   (0,0),(0,-1),  "Helvetica-Bold"),
    ("TEXTCOLOR",  (0,0),(0,-1),  ACCENT),
    ("TEXTCOLOR",  (1,0),(1,-1),  TEXT_DARK),
    ("ROWBACKGROUNDS", (0,0),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("TOPPADDING", (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ("LEFTPADDING",(0,0),(-1,-1), 8),
]))
story.append(toc_table)
story.append(PageBreak())

# ── SECTION 1: OVERVIEW ───────────────────────────────────────────────────────
story.append(h("1. Project Overview & Architecture"))
story.append(p(
    "This project is a production-grade data engineering platform that ingests US county-level "
    "cost-of-living data, processes it through a PySpark ETL pipeline, stores results in "
    "PostgreSQL, runs statistical A/B experiments across US Census regions, and exposes "
    "all results through a self-documenting FastAPI REST interface."
))
story.append(Spacer(1, 0.3*cm))
story.append(h("Architecture Flow", h2_style))

arch = """\
┌───────────────────────────────────────────────────────────┐
│               Dagster Orchestration                       │
│               orchestration/etl_job.py                   │
└──────────────────────┬────────────────────────────────────┘
                       │
           ┌───────────▼──────────────┐
           │   INGEST  (PySpark)      │  CSV → schema → Parquet staging
           │   pipeline/ingest.py     │
           └───────────┬──────────────┘
                       │  data/staging/  (Parquet)
           ┌───────────▼──────────────┐
           │   TRANSFORM (PySpark)    │  Broadcast join · dedup · enrich
           │   pipeline/transform.py  │
           └───────────┬──────────────┘  data/processed/ (partitioned by region)
                       │
           ┌───────────▼──────────────┐
           │   LOAD                   │  Parquet → PostgreSQL via SQLAlchemy
           │   pipeline/load.py       │  County rows + regional aggregates
           └───────────┬──────────────┘
                       │
           ┌───────────▼──────────────┐
           │   EXPERIMENT ENGINE      │  Welch t-test · Cohen's d · 95% CI
           │   experiments/ab_engine  │  All pairwise region comparisons
           └───────────┬──────────────┘
                       │
           ┌───────────▼──────────────┐
           │   REST API  (FastAPI)    │  /api/v1/regions  /states  /experiments
           │   api/main.py            │  Self-docs at /docs
           └──────────────────────────┘"""
story.append(Preformatted(arch, code_style))

story.append(h("PostgreSQL Tables", h2_style))
db_data = [
    ["Table", "Contents"],
    ["cost_of_living_processed", "Cleaned county-level records (~3,000 rows)"],
    ["regional_cost_statistics", "Spark SQL aggregates per US Census region (5 rows)"],
    ["experiment_results", "Pairwise A/B test results (p-value, Cohen's d, CI, winner)"],
]
db_table = Table(db_data, colWidths=[7*cm, 8*cm])
db_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), ACCENT),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 9),
    ("GRID",       (0,0),(-1,-1), 0.5, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 8),
]))
story.append(db_table)
story.append(PageBreak())

# ── SECTION 2: DATASET ────────────────────────────────────────────────────────
story.append(h("2. Dataset"))
story.append(p(
    "<b>Source:</b> Economic Policy Institute (EPI) Family Budget Calculator — "
    "cost_of_living_us_dap2.xls"
))
story.append(p(
    "The dataset covers approximately 3,000 US counties and metropolitan areas, "
    "providing annual cost estimates across nine expenditure categories for a "
    "family of four (2 adults, 2 children)."
))

col_data = [
    ["Column", "Type", "Description"],
    ["case_id",                "Integer", "Unique row identifier"],
    ["state",                  "String",  "US state abbreviation (e.g. CA)"],
    ["areaname",               "String",  "Metropolitan/micropolitan area name"],
    ["county",                 "String",  "County name"],
    ["housing_cost",           "Float",   "Annual housing cost (USD)"],
    ["food_cost",              "Float",   "Annual food cost (USD)"],
    ["transportation_cost",    "Float",   "Annual transportation cost (USD)"],
    ["healthcare_cost",        "Float",   "Annual healthcare cost (USD)"],
    ["other_necessities_cost", "Float",   "Other annual necessities (USD)"],
    ["childcare_cost",         "Float",   "Annual childcare cost (USD)"],
    ["taxes",                  "Float",   "Annual taxes (USD)"],
    ["total_cost",             "Float",   "Total annual cost of living (USD)"],
    ["median_family_income",   "Float",   "Median annual family income (USD)"],
]
col_table = Table(col_data, colWidths=[5*cm, 2.5*cm, 7.5*cm])
col_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), ACCENT2),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8.5),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ("LEFTPADDING",(0,0),(-1,-1), 7),
]))
story.append(col_table)
story.append(PageBreak())

# ── SECTION 3: TECH STACK ─────────────────────────────────────────────────────
story.append(h("3. Technology Stack"))

stack_data = [
    ["Layer", "Technology", "Version", "Why"],
    ["Batch Processing", "PySpark", "3.5.1",
     "Mirrors Databricks DataFrame API; Catalyst optimiser; partitioned Parquet"],
    ["Orchestration", "Dagster", "1.7.6",
     "Type-validated op outputs, run history, lineage — same role as Databricks Workflows"],
    ["Analytical Store", "PostgreSQL", "15+",
     "ACID writes; complex SQL joins for the API layer"],
    ["Experimentation", "SciPy", "1.12.0",
     "Welch's t-test — correct for unequal group variances across US regions"],
    ["API", "FastAPI", "0.111.0",
     "Auto-generated OpenAPI docs; async-ready; Pydantic validation"],
    ["Data Wrangling", "Pandas", "2.1.4",
     "XLS ingestion bridge and pandas→SQL via SQLAlchemy"],
    ["Containers", "Docker + Compose", "latest",
     "Reproducible full-stack: PostgreSQL + API in one docker-compose up"],
    ["DB ORM", "SQLAlchemy", "2.0.30",
     "DB-agnostic engine; works with both PostgreSQL (prod) and SQLite (demo)"],
]
stack_table = Table(stack_data, colWidths=[3.5*cm, 3*cm, 1.8*cm, 6.7*cm])
stack_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), DARK_BG),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8.5),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 7),
    ("VALIGN",     (0,0),(-1,-1), "TOP"),
]))
story.append(stack_table)
story.append(PageBreak())

# ── SECTION 4: INGEST ─────────────────────────────────────────────────────────
story.append(h("4. Ingest Layer — pipeline/ingest.py"))
story.append(p(
    "The ingest layer is responsible for reading the raw CSV-formatted XLS source file, "
    "enforcing a strongly typed schema, and writing the data to a Parquet staging zone. "
    "PySpark is used here to mirror the Databricks/production execution environment."
))
story.append(h("Key Concepts", h2_style))
for item in [
    "<b>SparkSession</b> — entry point to all PySpark functionality; configured with "
    "adaptive query execution and 8 shuffle partitions for local demo efficiency.",
    "<b>StructType schema enforcement</b> — every column has an explicit type. "
    "Without this, Spark would infer types and may silently coerce floats to strings.",
    "<b>Pandas bridge</b> — the XLS file is tab/comma-delimited without a native Spark "
    "connector, so pandas reads it first, then hands the DataFrame to Spark.",
    "<b>Parquet output</b> — columnar format; far more efficient for the downstream "
    "column-selective GROUP BY queries than row-based CSV.",
]:
    story.append(b(item))

story.append(Spacer(1, 0.4*cm))
story += code_block("pipeline/ingest.py", '''\
"""
Ingestion layer — reads raw XLS/CSV source into Parquet staging zone.
Uses PySpark for schema enforcement and scalable I/O.
"""
import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType, IntegerType
)

RAW_SCHEMA = StructType([
    StructField("case_id",                 IntegerType(), True),
    StructField("state",                   StringType(),  True),
    StructField("areaname",                StringType(),  True),
    StructField("county",                  StringType(),  True),
    StructField("isMetro",                 StringType(),  True),
    StructField("housing_cost",            FloatType(),   True),
    StructField("food_cost",               FloatType(),   True),
    StructField("transportation_cost",     FloatType(),   True),
    StructField("healthcare_cost",         FloatType(),   True),
    StructField("other_necessities_cost",  FloatType(),   True),
    StructField("childcare_cost",          FloatType(),   True),
    StructField("taxes",                   FloatType(),   True),
    StructField("total_cost",              FloatType(),   True),
    StructField("median_family_income",    FloatType(),   True),
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


def ingest(source_path: str, staging_path: str = "data/staging") -> int:
    """
    Read the raw XLS source (stored as CSV), enforce schema, drop unused
    columns, and write to Parquet staging zone.
    Returns the number of records written.
    """
    spark = get_spark()

    # XLS file is tab/comma-delimited — read via pandas then hand to Spark
    raw_pd = pd.read_csv(source_path, encoding="latin-1", low_memory=False)
    raw_pd.columns = [
        "case_id", "state", "areaname", "county", "isMetro",
        "housing_cost", "food_cost", "transportation_cost", "healthcare_cost",
        "other_necessities_cost", "childcare_cost", "taxes",
        "total_cost", "median_family_income",
    ]

    df: DataFrame = (
        spark.createDataFrame(raw_pd, schema=RAW_SCHEMA)
        .drop("isMetro")           # column not needed downstream
    )

    df.write.mode("overwrite").parquet(staging_path)
    count = df.count()
    print(f"[ingest] {count:,} records written to {staging_path}")
    return count
''')
story.append(PageBreak())

# ── SECTION 5: TRANSFORM ──────────────────────────────────────────────────────
story.append(h("5. Transform Layer — pipeline/transform.py"))
story.append(p(
    "The transform layer reads staged Parquet data and applies a sequence of "
    "enrichment and cleaning operations. The output is partitioned Parquet, "
    "structured for efficient predicate pushdown on region-level queries."
))
story.append(h("Operations Performed", h2_style))
for item in [
    "<b>Broadcast join</b> — expands state abbreviations (AL → Alabama) using a "
    "tiny lookup DataFrame that Spark broadcasts to all executors, avoiding a shuffle.",
    "<b>String normalisation</b> — county and areaname fields contain embedded "
    "underscores (e.g. 'Jefferson_County'); split on '_' and keep the first token.",
    "<b>Null fill</b> — median_family_income NULLs are replaced with 0.0 so "
    "affordability_ratio never produces NaN.",
    "<b>Deduplication</b> — dropDuplicates(['county']) removes any repeated entries "
    "caused by multiple family-type variants in the source dataset.",
    "<b>Derived column: affordability_ratio</b> — median_family_income / total_cost. "
    "A value > 1.0 means the median income exceeds the cost of living.",
    "<b>Derived column: region</b> — US Census region label built with a "
    "PySpark when/otherwise chain (equivalent to a SQL CASE expression).",
    "<b>Partitioned Parquet output</b> — writing partitionBy('region') means queries "
    "like WHERE region = 'West' skip all other partitions entirely.",
]:
    story.append(b(item))

story.append(Spacer(1, 0.4*cm))
story += code_block("pipeline/transform.py", '''\
"""
Transform layer — cleans, enriches, and partitions cost-of-living data.

Key operations:
  - Expand US state abbreviations via broadcast join
  - Normalise county/areaname strings
  - Fill nulls and deduplicate
  - Add derived metrics: affordability_ratio, region label
  - Partition output by region for predicate-pushdown efficiency
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pipeline.ingest import get_spark

STATE_ABBREV = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii',
    # ... (all 50 states + territories)
}

REGION_MAP = {
    'Northeast': ['Maine', 'New Hampshire', 'Vermont', 'Massachusetts', 'Rhode Island',
                  'Connecticut', 'New York', 'New Jersey', 'Pennsylvania'],
    'Southeast': ['Maryland', 'Delaware', 'Virginia', 'West Virginia', 'North Carolina',
                  'South Carolina', 'Georgia', 'Florida', 'Alabama', 'Mississippi',
                  'Tennessee', 'Kentucky'],
    'Midwest':   ['Ohio', 'Michigan', 'Indiana', 'Wisconsin', 'Illinois', 'Minnesota',
                  'Iowa', 'Missouri', 'North Dakota', 'South Dakota', 'Nebraska', 'Kansas'],
    'Southwest': ['Texas', 'Oklahoma', 'New Mexico', 'Arizona'],
    'West':      ['Colorado', 'Wyoming', 'Montana', 'Idaho', 'Washington', 'Oregon',
                  'Utah', 'Nevada', 'California', 'Alaska', 'Hawaii'],
}


def _region_column() -> F.Column:
    """Build a when/otherwise chain that assigns a US Census region to each state."""
    expr = None
    for region, states in REGION_MAP.items():
        condition = F.col("state").isin(states)
        expr = F.when(condition, F.lit(region)) if expr is None \
               else expr.when(condition, F.lit(region))
    return expr.otherwise(F.lit("Other"))


def transform(staging_path: str, processed_path: str = "data/processed") -> int:
    spark = get_spark()
    df: DataFrame = spark.read.parquet(staging_path)

    # 1. Expand state abbreviations via broadcast join
    abbrev_rows = [(k, v) for k, v in STATE_ABBREV.items()]
    abbrev_df = spark.createDataFrame(abbrev_rows, ["abbrev", "full_name"])

    df = (
        df.join(F.broadcast(abbrev_df), df["state"] == abbrev_df["abbrev"], "left")
          .withColumn("state", F.coalesce(F.col("full_name"), F.col("state")))
          .drop("abbrev", "full_name")
    )

    # 2. Normalise string fields
    df = (
        df.withColumn("county",   F.split(F.col("county"),   "_")[0])
          .withColumn("areaname", F.split(F.col("areaname"), "_")[0])
    )

    # 3. Fill nulls
    df = df.fillna({"median_family_income": 0.0})

    # 4. Deduplicate
    df = df.dropDuplicates(["county"])

    # 5. Derived metrics
    df = (
        df.withColumn(
            "affordability_ratio",
            F.round(F.col("median_family_income") / F.col("total_cost"), 3),
        )
        .withColumn("region", _region_column())
    )

    # 6. Partition by region for predicate-pushdown on downstream reads
    df.write.mode("overwrite").partitionBy("region").parquet(processed_path)

    count = df.count()
    print(f"[transform] {count:,} records written to {processed_path}")
    return count
''')
story.append(PageBreak())

# ── SECTION 6: LOAD ───────────────────────────────────────────────────────────
story.append(h("6. Load Layer — pipeline/load.py"))
story.append(p(
    "The load layer moves processed data from Parquet into PostgreSQL. "
    "Two tables are populated: county-level detail records and regional aggregates "
    "computed via Spark SQL before the data leaves the cluster."
))
story.append(h("Key Concepts", h2_style))
for item in [
    "<b>toPandas() + SQLAlchemy</b> — avoids needing a JDBC driver for the local/demo "
    "run. In production this would be swapped for a Spark JDBC write or Delta Lake write.",
    "<b>Spark SQL aggregation before collect</b> — the GROUP BY runs distributed on Spark "
    "before toPandas(); only 5 summary rows are collected, not 3,000.",
    "<b>chunksize=500</b> — Pandas writes rows to PostgreSQL in batches of 500 to "
    "avoid a single large INSERT that could exhaust server memory.",
    "<b>if_exists='replace'</b> — makes the pipeline fully idempotent; re-running "
    "overwrites previous results without duplication.",
]:
    story.append(b(item))

story.append(Spacer(1, 0.4*cm))
story += code_block("pipeline/load.py", '''\
"""
Load layer — writes processed Parquet data to PostgreSQL.

Uses toPandas() + SQLAlchemy for the DB write so no JDBC driver is needed
for local/demo runs. In production this would be swapped for a Spark JDBC
write with a connection pool or a Databricks Delta Lake target.
"""
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from sqlalchemy import create_engine
from pipeline.ingest import get_spark


def load(
    processed_path: str,
    db_url: str = "postgresql://dap:dap@127.0.0.1:5432/dap",
) -> int:
    """
    1. Write county-level processed records to `cost_of_living_processed`
    2. Compute regional aggregates in Spark SQL → `regional_cost_statistics`
    Returns the number of county-level rows loaded.
    """
    spark = get_spark()
    engine = create_engine(db_url)

    df: DataFrame = spark.read.parquet(processed_path)
    df.createOrReplaceTempView("cost_of_living")

    # County-level load
    county_pd = df.toPandas()
    county_pd.to_sql(
        "cost_of_living_processed", engine,
        if_exists="replace", index=False, chunksize=500,
    )
    print(f"[load] {len(county_pd):,} county rows → cost_of_living_processed")

    # Regional aggregates via Spark SQL (heavy computation stays on Spark)
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
    regional_pd.to_sql(
        "regional_cost_statistics", engine,
        if_exists="replace", index=False,
    )
    print(f"[load] {len(regional_pd)} regions → regional_cost_statistics")

    return len(county_pd)
''')
story.append(PageBreak())

# ── SECTION 7: A/B ENGINE ─────────────────────────────────────────────────────
story.append(h("7. A/B Experiment Engine — experiments/ab_engine.py"))
story.append(p(
    "The experiment engine applies rigorous statistical testing to compare cost-of-living "
    "metrics between any two US Census regions. This mirrors the kind of work a Business "
    "Experimentation & Optimisation team does — building infrastructure that lets analysts "
    "ask 'did this difference have a statistically significant effect?'"
))
story.append(h("Statistical Methodology", h2_style))

stat_data = [
    ["Concept", "Formula / Explanation"],
    ["Hypothesis",
     "H₀: mean(metric, A) = mean(metric, B)\nH₁: means differ (two-tailed)"],
    ["Test",
     "Welch's t-test (ttest_ind, equal_var=False) — correct when group variances differ"],
    ["Significance", "p_value < alpha (default alpha = 0.05)"],
    ["Effect Size",
     "Cohen's d = (treatment_mean − control_mean) / pooled_std\n"
     "Small < 0.2 | Medium < 0.5 | Large ≥ 0.8"],
    ["Confidence Interval",
     "95% CI on mean difference using Welch–Satterthwaite degrees of freedom\n"
     "CI = mean_diff ± t_crit × SE_diff"],
    ["Lift %",
     "(treatment_mean − control_mean) / control_mean × 100"],
    ["Winner",
     "For cost metrics: lower is better. For affordability_ratio: higher is better."],
]
stat_table = Table(stat_data, colWidths=[4*cm, 11*cm])
stat_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), GREEN),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8.5),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 7),
    ("VALIGN",     (0,0),(-1,-1), "TOP"),
]))
story.append(stat_table)

story.append(Spacer(1, 0.4*cm))
story += code_block("experiments/ab_engine.py", '''\
"""
A/B Experimentation Engine

Implements the statistical core of an experimentation platform:
  - Welch\'s t-test (correct when group variances differ)
  - Cohen\'s d effect size
  - 95% confidence interval on the mean difference
  - Lift % and winner determination
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, asdict
from typing import Literal
import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import Engine, text

VALID_REGIONS = {"Northeast", "Southeast", "Midwest", "Southwest", "West"}
VALID_METRICS = {
    "total_cost", "housing_cost", "food_cost",
    "healthcare_cost", "childcare_cost", "transportation_cost",
    "affordability_ratio",
}


@dataclass
class ExperimentResult:
    experiment_id:    str
    control_region:   str
    treatment_region: str
    metric:           str
    control_mean:     float
    treatment_mean:   float
    lift_pct:         float    # % change from control to treatment
    p_value:          float
    cohens_d:         float    # effect size
    ci_lower:         float    # 95% CI lower bound
    ci_upper:         float    # 95% CI upper bound
    significant:      bool
    winner:           str      # control_region | treatment_region | no_winner


def run_experiment(
    engine: Engine,
    control_region: str,
    treatment_region: str,
    metric: str = "total_cost",
    alpha: float = 0.05,
) -> ExperimentResult:
    stmt = text(
        f"SELECT region, {metric} FROM cost_of_living_processed"
        " WHERE region IN (:control, :treatment)"
    )
    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn,
                         params={"control": control_region,
                                 "treatment": treatment_region})

    control   = df.loc[df["region"] == control_region,   metric].dropna().values
    treatment = df.loc[df["region"] == treatment_region, metric].dropna().values

    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("Insufficient data: need at least 2 samples per group")

    # Welch\'s t-test
    t_stat, p_value = stats.ttest_ind(control, treatment, equal_var=False)

    # Cohen\'s d using pooled standard deviation
    pooled_std = np.sqrt((control.std() ** 2 + treatment.std() ** 2) / 2)
    cohens_d   = float((treatment.mean() - control.mean()) / pooled_std) \
                 if pooled_std > 0 else 0.0

    # 95% CI on the mean difference (Welch-Satterthwaite approximation)
    mean_diff = float(treatment.mean() - control.mean())
    se_diff   = float(np.sqrt(
        control.std() ** 2 / len(control) +
        treatment.std() ** 2 / len(treatment)
    ))
    df_welch  = (
        (control.std() ** 2 / len(control) + treatment.std() ** 2 / len(treatment)) ** 2
        / (
            (control.std() ** 2 / len(control))  ** 2 / (len(control)   - 1)
          + (treatment.std() ** 2 / len(treatment)) ** 2 / (len(treatment) - 1)
        )
    )
    t_crit   = stats.t.ppf(1 - alpha / 2, df=df_welch)
    ci_lower = round(mean_diff - t_crit * se_diff, 2)
    ci_upper = round(mean_diff + t_crit * se_diff, 2)
    lift_pct = round(mean_diff / float(control.mean()) * 100, 2) \
               if control.mean() != 0 else 0.0

    significant = bool(p_value < alpha)
    higher_is_better = metric == "affordability_ratio"
    if significant:
        treatment_wins = (
            treatment.mean() > control.mean() if higher_is_better
            else treatment.mean() < control.mean()
        )
        winner: str = treatment_region if treatment_wins else control_region
    else:
        winner = "no_winner"

    return ExperimentResult(
        experiment_id    = f"{control_region}_vs_{treatment_region}_{metric}",
        control_region   = control_region,
        treatment_region = treatment_region,
        metric           = metric,
        control_mean     = round(float(control.mean()), 2),
        treatment_mean   = round(float(treatment.mean()), 2),
        lift_pct         = lift_pct,
        p_value          = round(float(p_value), 4),
        cohens_d         = round(cohens_d, 3),
        ci_lower         = ci_lower,
        ci_upper         = ci_upper,
        significant      = significant,
        winner           = winner,
    )


def run_all_experiments(
    engine: Engine,
    metric: str = "total_cost",
    alpha: float = 0.05,
) -> list[ExperimentResult]:
    """Run pairwise experiments across all 5 US Census regions."""
    regions = sorted(VALID_REGIONS)
    results = []
    for i, control in enumerate(regions):
        for treatment in regions[i + 1:]:
            try:
                results.append(
                    run_experiment(engine, control, treatment, metric, alpha)
                )
            except ValueError as e:
                print(f"[ab_engine] Skipped {control} vs {treatment}: {e}")
    return results


def save_results(results: list[ExperimentResult], engine: Engine) -> None:
    """Persist experiment results to PostgreSQL for API consumption."""
    records = [asdict(r) for r in results]
    pd.DataFrame(records).to_sql(
        "experiment_results", engine, if_exists="replace", index=False,
    )
    sig = sum(r.significant for r in results)
    print(f"[ab_engine] {len(results)} experiments saved — {sig} significant at p<0.05")
''')
story.append(PageBreak())

# ── SECTION 8: ORCHESTRATION ──────────────────────────────────────────────────
story.append(h("8. Orchestration — orchestration/etl_job.py"))
story.append(p(
    "Dagster orchestrates the pipeline by wrapping each stage as a typed op. "
    "Ops pass their return values (record counts) downstream, giving Dagster "
    "type-safe lineage tracking. The entire pipeline executes with a single "
    "dagster job execute command."
))
story.append(h("Why Dagster?", h2_style))
for item in [
    "<b>Typed op outputs</b> — each op declares its output type (Out(int)), "
    "and Dagster validates it before passing to the next op.",
    "<b>Run history & lineage</b> — every run is logged with timestamps, "
    "durations, and asset lineage in the Dagster UI.",
    "<b>Environment-driven config</b> — SOURCE_PATH, DATABASE_URL, etc. are "
    "injected via env vars, making the same job run locally and in production.",
    "<b>Same role as Databricks Workflows</b> — if this were deployed on "
    "Databricks, the @job decorator would be replaced by a Workflow definition "
    "with the same op order.",
]:
    story.append(b(item))

story.append(Spacer(1, 0.4*cm))
story += code_block("orchestration/etl_job.py", '''\
"""
Dagster job that orchestrates the full pipeline:
  ingest -> transform -> load -> run_experiments
"""
import os
from dagster import job, op, Out, In, get_dagster_logger

DB_URL       = os.getenv("DATABASE_URL",  "postgresql://dap:dap@127.0.0.1:5432/dap")
SOURCE_PATH  = os.getenv("SOURCE_PATH",   "cost_of_living_us_dap2.xls")
STAGING_PATH = os.getenv("STAGING_PATH",  "data/staging")
PROCESSED_PATH = os.getenv("PROCESSED_PATH", "data/processed")

logger = get_dagster_logger()


@op(out=Out(int))
def ingest_op() -> int:
    from pipeline.ingest import ingest
    count = ingest(SOURCE_PATH, STAGING_PATH)
    logger.info("Ingested %d records", count)
    return count


@op(ins={"ingested": In(int)}, out=Out(int))
def transform_op(ingested: int) -> int:
    from pipeline.transform import transform
    count = transform(STAGING_PATH, PROCESSED_PATH)
    logger.info("Transformed %d records", count)
    return count


@op(ins={"transformed": In(int)}, out=Out(int))
def load_op(transformed: int) -> int:
    from pipeline.load import load
    count = load(PROCESSED_PATH, DB_URL)
    logger.info("Loaded %d records to PostgreSQL", count)
    return count


@op(ins={"loaded": In(int)}, out=Out(bool))
def experiment_op(loaded: int) -> bool:
    from sqlalchemy import create_engine
    from experiments.ab_engine import run_all_experiments, save_results

    db_engine = create_engine(DB_URL)

    for metric in ("total_cost", "affordability_ratio"):
        results = run_all_experiments(db_engine, metric=metric)
        save_results(results, db_engine)
        logger.info(
            "Experiments complete for metric=%s: %d/%d significant",
            metric,
            sum(r.significant for r in results),
            len(results),
        )
    return True


@job
def etl_pipeline():
    experiment_op(load_op(transform_op(ingest_op())))
''')
story.append(PageBreak())

# ── SECTION 9: REST API ───────────────────────────────────────────────────────
story.append(h("9. REST API — api/main.py"))
story.append(p(
    "FastAPI serves the pipeline outputs over HTTP. Every endpoint is automatically "
    "documented at /docs (Swagger UI) and /redoc. Pydantic validates request bodies "
    "at the boundary, and SQLAlchemy handles parameterised queries to prevent SQL injection."
))

api_data = [
    ["Method", "Path", "Description"],
    ["GET",  "/health",                         "Health check — returns {status: ok}"],
    ["GET",  "/api/v1/regions",                 "Regional cost statistics (5 rows)"],
    ["GET",  "/api/v1/states?limit=N",          "Per-state aggregates, ordered by metric"],
    ["GET",  "/api/v1/experiments",             "Experiment results; filter by metric/significance"],
    ["POST", "/api/v1/experiments/run",         "Run a new pairwise experiment on demand"],
]
api_table = Table(api_data, colWidths=[1.5*cm, 6*cm, 7.5*cm])
api_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), ORANGE),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8.5),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 7),
]))
story.append(api_table)

story.append(Spacer(1, 0.4*cm))
story += code_block("api/main.py", '''\
"""
Cost of Living Experimentation Platform — REST API
Self-documenting at /docs (Swagger UI).
"""
import os
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dap:dap@127.0.0.1:5432/dap")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(
    title="Cost of Living Experimentation Platform",
    version="1.0.0",
)

VALID_REGIONS = {"Northeast", "Southeast", "Midwest", "Southwest", "West"}

class ExperimentRequest(BaseModel):
    control_region:   str
    treatment_region: str
    metric:           str   = "total_cost"
    alpha:            float = 0.05


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}


@app.get("/api/v1/regions", tags=["analytics"])
def get_regional_stats():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM regional_cost_statistics ORDER BY avg_total_cost DESC")
        ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/states", tags=["analytics"])
def get_state_stats(
    limit: int = Query(20, ge=1, le=50),
    order_by: str = Query("total_cost"),
):
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT state, region,
                    ROUND(AVG(total_cost),           2) AS avg_total_cost,
                    ROUND(AVG(housing_cost),         2) AS avg_housing_cost,
                    ROUND(AVG(median_family_income), 2) AS avg_median_income,
                    ROUND(AVG(affordability_ratio),  3) AS avg_affordability_ratio,
                    COUNT(*) AS county_count
                FROM cost_of_living_processed
                WHERE region != \'Other\'
                GROUP BY state, region
                ORDER BY {order_by} DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/v1/experiments", tags=["experiments"])
def get_experiments(
    significant_only: bool = Query(False),
    metric: str = Query("total_cost"),
):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT * FROM experiment_results
                WHERE metric = :metric
                  AND (:sig_only = false OR significant = true)
                ORDER BY p_value ASC
            """),
            {"metric": metric, "sig_only": significant_only},
        ).mappings().all()
    return [dict(r) for r in rows]


@app.post("/api/v1/experiments/run", tags=["experiments"])
def trigger_experiment(body: ExperimentRequest):
    if body.control_region not in VALID_REGIONS:
        raise HTTPException(400, f"control_region must be one of {sorted(VALID_REGIONS)}")
    if body.treatment_region not in VALID_REGIONS:
        raise HTTPException(400, f"treatment_region must be one of {sorted(VALID_REGIONS)}")
    if body.control_region == body.treatment_region:
        raise HTTPException(400, "Regions must differ")

    from experiments.ab_engine import run_experiment, save_results
    result = run_experiment(
        engine, body.control_region, body.treatment_region,
        body.metric, body.alpha
    )
    save_results([result], engine)
    return result.__dict__
''')
story.append(PageBreak())

# ── SECTION 10: DEMO RUNNER ───────────────────────────────────────────────────
story.append(h("10. Local Demo Runner — run_demo.py"))
story.append(p(
    "The demo runner replicates the full pipeline logic using pandas and SQLite — "
    "no Java, no PostgreSQL, no Docker required. It is ideal for quickly verifying "
    "end-to-end behaviour or for demos on a laptop. The production pipeline "
    "(pipeline/ + orchestration/) uses the identical algorithms on PySpark + PostgreSQL."
))
story += code_block("run_demo.py (core logic — mirrors all 4 pipeline steps)", '''\
import pandas as pd, numpy as np, os, sys
from sqlalchemy import create_engine

os.environ["DATABASE_URL"] = "sqlite:///cost_of_living_demo.db"
engine = create_engine("sqlite:///cost_of_living_demo.db")

# ── STEP 1: INGEST ────────────────────────────────────────────────────────────
raw = pd.read_csv("cost_of_living_us_dap2.xls", encoding="latin-1", low_memory=False)
raw.columns = [
    "case_id", "state", "areaname", "county", "isMetro",
    "housing_cost", "food_cost", "transportation_cost", "healthcare_cost",
    "other_necessities_cost", "childcare_cost", "taxes",
    "total_cost", "median_family_income",
]
raw.drop(columns=["isMetro"], inplace=True)

# ── STEP 2: TRANSFORM ─────────────────────────────────────────────────────────
df = raw.copy()
df["state"]  = df["state"].map(STATE_ABBREV).fillna(df["state"])   # expand abbreviations
df["county"]   = df["county"].astype(str).str.split("_").str[0]    # normalise strings
df["areaname"] = df["areaname"].astype(str).str.split("_").str[0]
df["median_family_income"] = df["median_family_income"].fillna(0.0) # fill nulls
df = df.drop_duplicates(subset=["county"])                          # deduplicate
df["affordability_ratio"] = (df["median_family_income"] / df["total_cost"]).round(3)
state_to_region = {s: r for r, states in REGION_MAP.items() for s in states}
df["region"] = df["state"].map(state_to_region).fillna("Other")
df.to_sql("cost_of_living_processed", engine, if_exists="replace", index=False)

# ── STEP 3: LOAD REGIONAL AGGREGATES ─────────────────────────────────────────
regional = (
    df[df["region"] != "Other"]
    .groupby("region")
    .agg(
        avg_total_cost          = ("total_cost",           "mean"),
        avg_housing_cost        = ("housing_cost",         "mean"),
        avg_food_cost           = ("food_cost",            "mean"),
        avg_healthcare_cost     = ("healthcare_cost",      "mean"),
        avg_childcare_cost      = ("childcare_cost",       "mean"),
        avg_transportation_cost = ("transportation_cost",  "mean"),
        avg_median_income       = ("median_family_income", "mean"),
        avg_affordability_ratio = ("affordability_ratio",  "mean"),
        county_count            = ("total_cost",           "count"),
    )
    .round(2).reset_index()
    .sort_values("avg_total_cost", ascending=False)
)
regional.to_sql("regional_cost_statistics", engine, if_exists="replace", index=False)

# ── STEP 4: A/B EXPERIMENTS ───────────────────────────────────────────────────
from experiments.ab_engine import run_all_experiments, save_results
all_results = []
for metric in ("total_cost", "housing_cost", "affordability_ratio"):
    all_results.extend(run_all_experiments(engine, metric=metric))
save_results(all_results, engine)
''')
story.append(PageBreak())

# ── SECTION 11: HOW TO SEE THE OUTPUT ────────────────────────────────────────
story.append(h("11. How To See the Output"))

story.append(h("Option A — Run the Local Demo (No Docker, No Java needed)", h2_style))
story.append(Paragraph(
    "<b>Step 1:</b> Install dependencies", body_style
))
story += code_block("Terminal", "pip install -r requirements.txt")

story.append(Paragraph("<b>Step 2:</b> Run the pipeline demo", body_style))
story += code_block("Terminal", "python3 run_demo.py")
story.append(p(
    "This prints the 4-step pipeline output to your terminal: record counts, "
    "region distribution, regional cost table, and A/B experiment results."
))

story.append(Paragraph("<b>Step 3:</b> Start the REST API", body_style))
story += code_block("Terminal",
    'DATABASE_URL=sqlite:///cost_of_living_demo.db uvicorn api.main:app --reload')
story.append(p("The API starts at http://localhost:8000"))

story.append(Paragraph("<b>Step 4:</b> Open the interactive API docs", body_style))
story += code_block("Browser", "http://localhost:8000/docs")
story.append(Paragraph(
    "<i>This opens the Swagger UI where you can click any endpoint and try it live.</i>",
    body_style,
))

story.append(Spacer(1, 0.4*cm))
story.append(h("Option B — curl the API endpoints", h2_style))
story += code_block("Terminal — example API calls", '''\
# Regional cost statistics
curl http://localhost:8000/api/v1/regions

# Top 10 most expensive states by total cost
curl "http://localhost:8000/api/v1/states?limit=10&order_by=total_cost"

# All significant experiment results for housing cost
curl "http://localhost:8000/api/v1/experiments?significant_only=true&metric=housing_cost"

# Run a new A/B experiment on demand (Northeast vs Midwest on housing cost)
curl -X POST http://localhost:8000/api/v1/experiments/run \\
  -H "Content-Type: application/json" \\
  -d \'{"control_region": "Midwest", "treatment_region": "Northeast", "metric": "housing_cost"}\'

# Health check
curl http://localhost:8000/health
''')

story.append(h("Option C — Full Production Stack (Docker)", h2_style))
story += code_block("Terminal", "docker-compose up --build")
story.append(p("Docker Compose starts PostgreSQL and the FastAPI server together."))
story += code_block("Terminal — run the Dagster pipeline inside the container",
    "docker-compose exec api dagster job execute -f orchestration/etl_job.py -j etl_pipeline")

story.append(Spacer(1, 0.4*cm))
story.append(h("Where to Find the Data", h2_style))
out_data = [
    ["Location", "Contents"],
    ["Terminal output (run_demo.py)",    "Step-by-step printed summaries, region table, A/B results table"],
    ["http://localhost:8000/docs",        "Swagger UI — interactive API documentation and live testing"],
    ["http://localhost:8000/api/v1/regions", "JSON — 5 regional cost aggregates"],
    ["http://localhost:8000/api/v1/experiments", "JSON — all pairwise A/B test results"],
    ["cost_of_living_demo.db (SQLite)",   "Local database with 3 tables — open with DB Browser for SQLite"],
    ["data/staging/ (Parquet)",           "Raw staged data after ingest step (PySpark run only)"],
    ["data/processed/ (Parquet)",         "Cleaned, enriched, region-partitioned data (PySpark run only)"],
]
out_table = Table(out_data, colWidths=[6*cm, 9*cm])
out_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,0), DARK_BG),
    ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8.5),
    ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, LIGHT_GRAY]),
    ("TOPPADDING", (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("LEFTPADDING",(0,0),(-1,-1), 8),
    ("VALIGN",     (0,0),(-1,-1), "TOP"),
]))
story.append(out_table)

story.append(Spacer(1, 1*cm))
story.append(hr())
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "<i>End of Documentation — Cost of Living Experimentation Platform</i>",
    ParagraphStyle("Footer", parent=body_style, alignment=TA_CENTER,
                   textColor=colors.grey, fontSize=9)
))

# ── BUILD ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF created: {OUTPUT}")
