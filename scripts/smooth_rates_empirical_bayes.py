"""Empirical-Bayes smoothing of municipal varicella incidence rates.

Small municipalities produce unstable rates: a handful of cases on a tiny
population yields extreme values. This script applies a global
Poisson-Gamma Empirical Bayes (EB) estimator, per age group, that shrinks each
municipal rate towards the group's global mean in proportion to how little
information the municipality carries. Large municipalities keep almost their
crude rate; small ones are pulled towards the mean.

The estimator and its method-of-moments shrinkage follow Marshall (1991),
"Mapping disease and mortality rates using Empirical Bayes estimators", Applied
Statistics 40(2):283-294, the global-shrinkage special case used by GeoDa and
by Clayton & Kaldor (1987).

Model, per age group g, municipality i:
    O_gi ~ Poisson(n_gi * theta_gi),  theta_gi ~ Gamma(nu, alpha)
with prior mean m_g = E[theta] = nu/alpha and prior variance phi_g.
Method of moments on the crude rates r_gi = O_gi / n_gi:
    m_g   = sum_i O_gi / sum_i n_gi                      (pooled rate)
    s2_g  = sum_i n_gi (r_gi - m_g)^2 / sum_i n_gi       (population-weighted var)
    phi_g = s2_g - m_g / nbar_g,     nbar_g = mean(n_gi)  (between-area variance)
    phi_g = max(phi_g, 0)
Shrinkage weight and smoothed rate for each municipality:
    C_gi      = phi_g / (phi_g + m_g / n_gi)   in [0, 1]
    theta_hat = C_gi * r_gi + (1 - C_gi) * m_g

C_gi near 1 keeps the crude rate (large n or large between-area variance);
C_gi near 0 pulls the rate to the global mean (small n). phi_g = 0 shrinks every
municipality fully to m_g (no detectable signal beyond Poisson noise).

EB stabilises variance only. It does not correct under-reporting, surveillance
changes or denominator errors, and the result depends on the Gamma assumption
and on the global mean, which is why shrinkage is estimated per age group.

Input : the full municipal age-year panel (1,102 comparable municipalities,
        2008-2025) built by generate_age_standardized_sir.read_panel(), with
        observed_* and population_* per age group.
Output: docs/data_processed/cobertura_vacunacion/empirical_bayes/
        municipal_incidence_eb.csv  and  municipal_incidence_eb.metadata.json

The smoothed rate is produced for every year 2008-2025 (one EB fit per age group
and year) and for the pooled baseline 2008-2014. The evolution chart uses the
full smoothed series; the priority list reads its 2024 and 2025 values.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_age_standardized_sir import read_panel
from generate_moran_lisa import read_points, nearest_neighbors

DATA = ROOT / "docs/data_processed"
OUTDIR = DATA / "cobertura_vacunacion/empirical_bayes"
YEARS = tuple(range(2008, 2026))
BASELINE_YEARS = tuple(range(2008, 2015))
AGE_PARTS = ("under_1", "1_4", "5_14", "15_49", "50_plus")
# "all" is smoothed as its own fit: total municipal cases over total population.
AGE_GROUPS = ("all",) + AGE_PARTS
LABELS = {
    "all": "Todas las edades", "under_1": "Menores de 1 año", "1_4": "1–4 años",
    "5_14": "5–14 años", "15_49": "15–49 años", "50_plus": "50 años o más",
}
RATE_SCALE = 100_000.0


def eb_global(observed: np.ndarray, population: np.ndarray):
    """Global Poisson-Gamma EB (Marshall 1991). Returns smoothed rate per 100k,
    shrinkage weight C, and the group summaries (m, phi) as rates per 100k."""
    observed = np.asarray(observed, dtype=float)
    population = np.asarray(population, dtype=float)
    valid = np.isfinite(observed) & np.isfinite(population) & (population > 0)
    smoothed = np.full(observed.shape, np.nan)
    weight = np.full(observed.shape, np.nan)
    if valid.sum() == 0:
        return smoothed, weight, {"mean_per_100k": np.nan, "between_var": np.nan, "n": 0}
    O, n = observed[valid], population[valid]
    crude = O / n
    m = O.sum() / n.sum()                                   # pooled rate
    s2 = np.average((crude - m) ** 2, weights=n)            # weighted variance
    nbar = n.mean()
    phi = max(s2 - m / nbar, 0.0)                           # between-area variance
    C = phi / (phi + m / n) if phi > 0 else np.zeros_like(n)
    smoothed[valid] = (C * crude + (1 - C) * m) * RATE_SCALE
    weight[valid] = C
    return smoothed, weight, {
        "mean_per_100k": m * RATE_SCALE,
        "between_var": phi * RATE_SCALE ** 2,
        "n": int(valid.sum()),
    }


def eb_local(observed: np.ndarray, population: np.ndarray, neighbors: np.ndarray):
    """Local (neighbourhood) Poisson-Gamma EB, Marshall (1991).

    For each municipality i, the shrinkage target is the mean rate of its
    neighbourhood (i plus its k nearest neighbours) and the between-area variance
    is estimated within that neighbourhood. Shrinks small municipalities towards
    their regional level rather than the national one. Returns smoothed rate per
    100k and the shrinkage weight; both are NaN where the focal municipality has
    no valid rate or its neighbourhood has fewer than two valid areas.
    """
    observed = np.asarray(observed, dtype=float)
    population = np.asarray(population, dtype=float)
    smoothed = np.full(observed.shape, np.nan)
    weight = np.full(observed.shape, np.nan)
    for i in range(len(observed)):
        idx = np.concatenate(([i], neighbors[i]))
        O, n = observed[idx], population[idx]
        valid = np.isfinite(O) & np.isfinite(n) & (n > 0)
        if not valid[0] or valid.sum() < 2:              # focal must be valid
            continue
        O, n = O[valid], n[valid]
        m = O.sum() / n.sum()
        crude = O / n
        s2 = np.average((crude - m) ** 2, weights=n)
        phi = max(s2 - m / n.mean(), 0.0)
        c0, n0 = crude[0], n[0]
        C = phi / (phi + m / n0) if phi > 0 else 0.0
        smoothed[i] = (C * c0 + (1 - C) * m) * RATE_SCALE
        weight[i] = C
    return smoothed, weight


def _rate(observed, population):
    population = population.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(population > 0, observed / population * RATE_SCALE, np.nan)


def build(panel: pd.DataFrame):
    """panel: columns codigo_municipio, ano_epidemiologico, observed_<g>, population_<g>."""
    panel = panel.rename(columns={"codigo_municipio": "code", "ano_epidemiologico": "year"})
    # "all": total municipal cases (incl. unknown-age) over total population, to match
    # the evolution chart's "Todas las edades" definition.
    panel["observed_all"] = panel["casos_total"]
    panel["population_all"] = panel[[f"population_{g}" for g in AGE_PARTS]].sum(axis=1)
    # Canonical municipality order, and the 8-nearest-neighbour matrix shared with
    # section 8 (Moran/LISA), restricted to municipalities present in the panel.
    points = read_points()
    codes = [c for c in sorted(panel.code.unique()) if c in points]
    neighbors = nearest_neighbors(points, codes)
    missing_points = sorted(set(panel.code.unique()) - set(codes))

    def fit(frame_indexed, group):
        """Global and local EB for one period, aligned to the canonical code order."""
        sub = frame_indexed.reindex(codes)
        O = sub[f"observed_{group}"].to_numpy(float)
        n = sub[f"population_{group}"].to_numpy(float)
        g_rate, g_w, summ = eb_global(O, n)
        l_rate, l_w = eb_local(O, n, neighbors)
        return O, n, g_rate, g_w, l_rate, l_w, summ

    rows = []
    group_summaries = {}
    for group in AGE_GROUPS:
        # One EB fit per year across the 1,102 municipalities.
        for year in YEARS:
            indexed = panel[panel.year == year].set_index("code")
            O, n, g_rate, g_w, l_rate, l_w, summ = fit(indexed, group)
            rows.append(pd.DataFrame({
                "code": codes, "year": str(year), "age_group": group, "scope": "annual",
                "observed": O, "population": n, "rate_crude": _rate(O, n),
                "rate_eb": g_rate, "shrinkage": g_w,
                "rate_eb_local": l_rate, "shrinkage_local": l_w,
            }))
            group_summaries[f"annual_{group}_{year}"] = summ
        # Pooled baseline 2008-2014: sum cases and person-years per municipality, then one EB fit.
        base = panel[panel.year.isin(BASELINE_YEARS)].groupby("code")[[f"observed_{group}", f"population_{group}"]].sum()
        O, n, g_rate, g_w, l_rate, l_w, summ = fit(base, group)
        rows.append(pd.DataFrame({
            "code": codes, "year": "baseline_2008_2014", "age_group": group, "scope": "baseline",
            "observed": O, "population": n, "rate_crude": _rate(O, n),
            "rate_eb": g_rate, "shrinkage": g_w,
            "rate_eb_local": l_rate, "shrinkage_local": l_w,
        }))
        group_summaries[f"baseline_{group}"] = summ
    result = pd.concat(rows, ignore_index=True)
    result["rate_crude"] = result["rate_crude"].replace([np.inf, -np.inf], np.nan)
    metadata = {
        "model_global": "global Poisson-Gamma Empirical Bayes, per age group and year (Marshall 1991): shrinks each municipality towards the national group mean",
        "model_local": "local (neighbourhood) Poisson-Gamma EB (Marshall 1991): shrinks towards the mean of the municipality and its 8 nearest neighbours, using the same neighbour matrix as section 8 (Moran/LISA)",
        "rate_scale_per": int(RATE_SCALE),
        "years": list(YEARS),
        "baseline_years": list(BASELINE_YEARS),
        "neighbor_count": 8,
        "age_groups": {g: LABELS[g] for g in AGE_GROUPS},
        "municipalities": int(len(codes)),
        "municipalities_without_point": missing_points,
        "shrinkage_rule": "C = phi / (phi + m / n); smoothed = C*crude + (1-C)*m; phi=0 shrinks fully to the target mean (national for global, neighbourhood for local)",
        "local_note": "rate_eb_local and shrinkage_local are null where the municipality has no representative point or its neighbourhood has fewer than two valid areas; local EB stabilises small municipalities less than global because each neighbourhood has fewer data than the country",
        "scope_note": "annual rows cover 2008-2025 for the evolution chart; the priority list reads the 2024 and 2025 values; baseline rows pool 2008-2014",
        "limitations": "stabilises variance only; does not correct under-reporting, surveillance changes or denominator errors; depends on the Gamma assumption and on the shrinkage target (national or neighbourhood)",
        "group_summaries": group_summaries,
    }
    return result, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()
    panel = read_panel()
    result, metadata = build(panel)
    args.outdir.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.outdir / "municipal_incidence_eb.csv", index=False, float_format="%.8f")
    (args.outdir / "municipal_incidence_eb.metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in metadata.items() if k != "group_summaries"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
