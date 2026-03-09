# Data Warehousing Demo

A demonstration ETL (Extract, Transform, Load) pipeline that ingests cost of living, unemployment, and quality of life data from multiple sources into a PostgreSQL data warehouse using Dagster for orchestration.

## Architecture

```
Data Sources                  Staging          Warehouse        Output
─────────────────             ─────────        ─────────        ──────
CSV (Cost of Living)  ──────► Cassandra ──────►
MongoDB (Unemployment) ──────►           JOIN ► PostgreSQL ──► Bokeh
MongoDB (Quality of Life) ──►                                  Dashboard
```

**Pipeline stages:**
1. **Extract** — Read raw data from source files/databases, load into Cassandra (staging)
2. **Transform** — Pull from Cassandra, clean and normalize data, load to PostgreSQL
3. **Join** — Merge all three transformed datasets into a unified dataframe
4. **Load** — Persist merged data to PostgreSQL warehouse
5. **Visualise** — Generate interactive dashboards using Bokeh

## Project Structure

```
data_warehousing_demo/
├── cost_of_living_etl.py        # Dagster job definition (pipeline entrypoint)
├── extract.py                   # Extract ops for all three data sources
├── transfer_and_load.py         # Transform, join, and load ops
├── visualization.py             # Bokeh visualization op
└── cost_of_living_us_dap2.xls  # Source dataset (US cost of living by county)
```

## Data Sources

| Source | Format | Data |
|--------|--------|------|
| `cost_of_living_us_dap2.xls` | CSV/XLS | Housing, food, transport, healthcare costs by US county |
| MongoDB `unemployment` collection | NoSQL | Unemployment rates |
| MongoDB `quality_of_life` collection | NoSQL | Quality of life metrics |

### Cost of Living Schema

| Column | Type | Description |
|--------|------|-------------|
| `case_id` | int | Record identifier |
| `state` | text | US state abbreviation |
| `areaname` | text | Area name |
| `county` | text | County name |
| `housing_cost` | float | Monthly housing cost |
| `food_cost` | float | Monthly food cost |
| `transportation_cost` | float | Monthly transportation cost |
| `healthcare_cost` | float | Monthly healthcare cost |
| `other_necessities_cost` | float | Other monthly necessities |
| `childcare_cost` | float | Monthly childcare cost |
| `taxes` | float | Monthly taxes |
| `total_cost` | float | Total monthly cost |
| `median_family_income` | float | Median family income |

## Prerequisites

- Python 3.8+
- Apache Cassandra (running on `127.0.0.1`)
- PostgreSQL (running on `127.0.0.1:5432`)
- MongoDB (running locally)

## Installation

```bash
pip install dagster dagster-pandas pandas numpy cassandra-driver pymongo sqlalchemy psycopg2-binary bokeh
```

## Database Setup

**PostgreSQL** — create a database and user:
```sql
CREATE USER dap WITH PASSWORD 'dap';
CREATE DATABASE dap OWNER dap;
```

**Cassandra** — the pipeline auto-creates the keyspace and table on first run.

**MongoDB** — ensure the `unemployment` database with an `unemployment` collection is accessible.

## Running the Pipeline

```bash
dagster job execute -f cost_of_living_etl.py -j etl
```

Or launch the Dagster UI:
```bash
dagit -f cost_of_living_etl.py
```

## Transformation Logic

The `transform_cost_of_living` step applies the following cleaning steps:

- **State expansion** — converts abbreviations to full names (e.g. `CA` → `California`)
- **Name cleaning** — splits underscore-separated county/area names, keeping the first segment
- **Missing income** — fills null `median_family_income` values with `0`
- **Deduplication** — removes duplicate counties, keeping the first occurrence
- Saves the cleaned data to the `cost_of_living_structured` table in PostgreSQL

## Technologies

| Tool | Role |
|------|------|
| [Dagster](https://dagster.io/) | Pipeline orchestration and op graph |
| [Pandas](https://pandas.pydata.org/) | Data manipulation |
| [Cassandra](https://cassandra.apache.org/) | Staging / NoSQL store |
| [PostgreSQL](https://www.postgresql.org/) | Data warehouse |
| [MongoDB](https://www.mongodb.com/) | Source for unemployment data |
| [SQLAlchemy](https://www.sqlalchemy.org/) | PostgreSQL ORM/connection layer |
| [Bokeh](https://bokeh.org/) | Interactive data visualization |
| [dagster-pandas](https://docs.dagster.io/_apidocs/libraries/dagster-pandas) | DataFrame type validation |

## Development Status

| Module | Status |
|--------|--------|
| Cost of living extraction | Complete |
| Cost of living transformation | Complete |
| Unemployment extraction | In progress |
| Quality of life extraction | In progress |
| Data joining | Placeholder |
| Loading to warehouse | Placeholder |
| Visualization | Framework only |
