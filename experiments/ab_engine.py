"""
A/B Experimentation Engine

Implements the statistical core of an experimentation platform:
  - Welch's t-test (correct when group variances differ, which they do across US regions)
  - Cohen's d effect size
  - 95% confidence interval on the mean difference
  - Winner determination with statistical rigour

save_results() uses upsert semantics (delete-then-insert per experiment_id)
so calling it multiple times never overwrites results for unrelated experiments.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import Engine, text

from pipeline.config import VALID_METRICS, VALID_REGIONS

log = logging.getLogger(__name__)

# Explicit allowlist map: prevents any SQL column injection even if upstream
# validation is bypassed. Keys == values here, but the indirection is the guard.
_SAFE_METRIC_COL: dict[str, str] = {m: m for m in VALID_METRICS}

_CREATE_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_id    TEXT PRIMARY KEY,
    control_region   TEXT    NOT NULL,
    treatment_region TEXT    NOT NULL,
    metric           TEXT    NOT NULL,
    control_mean     REAL,
    treatment_mean   REAL,
    lift_pct         REAL,
    p_value          REAL,
    cohens_d         REAL,
    ci_lower         REAL,
    ci_upper         REAL,
    significant      INTEGER,
    winner           TEXT
)
"""


@dataclass
class ExperimentResult:
    experiment_id:    str
    control_region:   str
    treatment_region: str
    metric:           str
    control_mean:     float
    treatment_mean:   float
    lift_pct:         float
    p_value:          float
    cohens_d:         float
    ci_lower:         float
    ci_upper:         float
    significant:      bool
    winner:           str


def run_experiment(
    engine: Engine,
    control_region: str,
    treatment_region: str,
    metric: str = "total_cost",
    alpha: float = 0.05,
) -> ExperimentResult:
    """
    Compare `metric` between `control_region` and `treatment_region`.

    Cost metrics: lower is better (treatment wins if significantly lower).
    affordability_ratio: higher is better.
    """
    if control_region not in VALID_REGIONS or treatment_region not in VALID_REGIONS:
        raise ValueError(f"Regions must be one of {sorted(VALID_REGIONS)}")
    if metric not in VALID_METRICS:
        raise ValueError(f"Metric must be one of {sorted(VALID_METRICS)}")

    col = _SAFE_METRIC_COL[metric]
    stmt = text(
        f"SELECT region, {col} AS value FROM cost_of_living_processed"  # noqa: S608
        " WHERE region IN (:control, :treatment)"
    )
    with engine.connect() as conn:
        df = pd.read_sql(
            stmt, conn, params={"control": control_region, "treatment": treatment_region}
        )

    ctrl = df.loc[df["region"] == control_region,   "value"].dropna().to_numpy(dtype=float)
    trt  = df.loc[df["region"] == treatment_region, "value"].dropna().to_numpy(dtype=float)

    if len(ctrl) < 2 or len(trt) < 2:
        raise ValueError(
            f"Need ≥2 samples per group; got {len(ctrl)} (control) / {len(trt)} (treatment)"
        )

    _, p_value = stats.ttest_ind(ctrl, trt, equal_var=False)

    pooled_std = float(np.sqrt((ctrl.std() ** 2 + trt.std() ** 2) / 2))
    cohens_d   = float((trt.mean() - ctrl.mean()) / pooled_std) if pooled_std > 0 else 0.0

    mean_diff = float(trt.mean() - ctrl.mean())
    se_diff   = float(np.sqrt(ctrl.std() ** 2 / len(ctrl) + trt.std() ** 2 / len(trt)))
    df_welch  = (
        (ctrl.std() ** 2 / len(ctrl) + trt.std() ** 2 / len(trt)) ** 2
        / (
            (ctrl.std() ** 2 / len(ctrl)) ** 2 / (len(ctrl) - 1)
            + (trt.std() ** 2  / len(trt))  ** 2 / (len(trt)  - 1)
        )
    )
    t_crit   = stats.t.ppf(1 - alpha / 2, df=df_welch)
    ci_lower = round(mean_diff - t_crit * se_diff, 2)
    ci_upper = round(mean_diff + t_crit * se_diff, 2)
    lift_pct = round(mean_diff / float(ctrl.mean()) * 100, 2) if ctrl.mean() != 0 else 0.0

    significant = bool(p_value < alpha)
    higher_is_better = metric == "affordability_ratio"
    if significant:
        trt_wins = trt.mean() > ctrl.mean() if higher_is_better else trt.mean() < ctrl.mean()
        winner   = treatment_region if trt_wins else control_region
    else:
        winner = "no_winner"

    return ExperimentResult(
        experiment_id    = f"{control_region}_vs_{treatment_region}_{metric}",
        control_region   = control_region,
        treatment_region = treatment_region,
        metric           = metric,
        control_mean     = round(float(ctrl.mean()), 2),
        treatment_mean   = round(float(trt.mean()),  2),
        lift_pct         = lift_pct,
        p_value          = round(float(p_value),  4),
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
    """Run all pairwise region comparisons for a given metric."""
    regions = sorted(VALID_REGIONS)
    results = []
    for i, control in enumerate(regions):
        for treatment in regions[i + 1:]:
            try:
                results.append(run_experiment(engine, control, treatment, metric, alpha))
            except ValueError as exc:
                log.warning("Skipped %s vs %s [%s]: %s", control, treatment, metric, exc)
    return results


def save_results(results: list[ExperimentResult], engine: Engine) -> None:
    """
    Upsert experiment results.

    Uses delete-then-insert per experiment_id so that saving results for one
    metric never touches rows from a different metric / experiment pair.
    """
    if not results:
        return

    records = [asdict(r) for r in results]
    df = pd.DataFrame(records)
    ids = df["experiment_id"].tolist()

    with engine.begin() as conn:
        conn.execute(text(_CREATE_RESULTS_TABLE))
        for eid in ids:
            conn.execute(
                text("DELETE FROM experiment_results WHERE experiment_id = :eid"),
                {"eid": eid},
            )

    df.to_sql("experiment_results", engine, if_exists="append", index=False)

    sig = sum(r.significant for r in results)
    log.info("Saved %d experiments (%d significant at p<0.05)", len(results), sig)
