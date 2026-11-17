"""Calculate period-level global Moran I and municipal local Moran clusters.

Inputs are the municipal notification rates and the 2025 DANE geometry already
published with the site. Run with:

    .venv/bin/python scripts/generate_moran_lisa.py
"""

import csv
import json
from pathlib import Path

import numpy as np
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
RATES = ROOT / "docs/data_processed/heterogeneidad_espacial/spatial_series_2008_2025.csv"
GEOMETRY = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
GLOBAL_OUTPUT = ROOT / "docs/data_processed/heterogeneidad_espacial/moran_global_periods.csv"
LOCAL_OUTPUT = ROOT / "docs/data_processed/heterogeneidad_espacial/moran_lisa_periods.csv"
PERIODS = ("2008-2014", "2015-2019", "2020-2021", "2022-2025")
NEIGHBOR_COUNT = 8
PERMUTATIONS = 9999
SEED = 2026
FDR_THRESHOLD = 0.05


def read_points():
    """Return municipal representative points, indexed by stable DIVIPOLA order."""
    collection = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    features = sorted(
        (item for item in collection["features"] if item["properties"]["kind"] == "MUNICIPIO"),
        key=lambda item: item["properties"]["code"],
    )
    points = {}
    for item in features:
        point = shape(item["geometry"]).representative_point()
        points[item["properties"]["code"]] = (point.y, point.x)
    return points


def read_rates():
    """Read exact rates from counts and person-years; retain missing rates as missing."""
    by_period = {period: {} for period in PERIODS}
    with RATES.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            period = row["period"]
            if period not in by_period:
                continue
            population_years = int(row["population_years"])
            if row["rate_per_100k"] and population_years > 0:
                by_period[period][row["code"]] = (
                    int(row["notifications"]) / population_years * 100_000
                )
    return by_period


def nearest_neighbors(points, codes, k=NEIGHBOR_COUNT):
    """Find nearest representative points by great-circle distance in kilometers."""
    coordinates = np.radians(np.array([points[code] for code in codes], dtype=float))
    latitude, longitude = coordinates.T
    lat_diff = latitude[:, None] - latitude[None, :]
    lon_diff = longitude[:, None] - longitude[None, :]
    haversine = (
        np.sin(lat_diff / 2) ** 2
        + np.cos(latitude[:, None])
        * np.cos(latitude[None, :])
        * np.sin(lon_diff / 2) ** 2
    )
    distances = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(haversine, 0, 1)))
    np.fill_diagonal(distances, np.inf)
    return np.argsort(distances, axis=1, kind="stable")[:, :k]


def benjamini_hochberg(p_values):
    """Adjust the local two-sided permutation p-values across one period."""
    size = len(p_values)
    order = np.argsort(p_values, kind="stable")
    ranked = p_values[order] * size / np.arange(1, size + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    result = np.empty(size, dtype=float)
    result[order] = np.minimum(adjusted, 1.0)
    return result


def sample_other_indices(rng, size, k, excluded):
    """Draw k distinct non-focal indices for each conditional permutation."""
    draws = rng.integers(0, size - 1, size=(PERMUTATIONS, k))
    duplicates = np.any(np.diff(np.sort(draws, axis=1), axis=1) == 0, axis=1)
    while np.any(duplicates):
        count = int(duplicates.sum())
        draws[duplicates] = rng.integers(0, size - 1, size=(count, k))
        duplicates = np.any(np.diff(np.sort(draws, axis=1), axis=1) == 0, axis=1)
    return draws + (draws >= excluded)


def moran_statistics(rates, neighbors, rng):
    """Return global and local Moran results under row-standardized kNN weights."""
    size = len(rates)
    deviations = rates - rates.mean()
    denominator = np.dot(deviations, deviations)
    if denominator <= 0:
        raise ValueError("Moran I is undefined for a constant rate")
    lag = deviations[neighbors].mean(axis=1)
    global_i = float(np.dot(deviations, lag) / denominator)
    local_i = deviations * lag / (denominator / size)

    global_exceedances = 0
    for _ in range(PERMUTATIONS):
        shuffled = rng.permutation(deviations)
        shuffled_i = np.dot(shuffled, shuffled[neighbors].mean(axis=1)) / denominator
        global_exceedances += shuffled_i >= global_i
    global_p = (1 + global_exceedances) / (PERMUTATIONS + 1)

    local_p = np.ones(size, dtype=float)
    for focal in range(size):
        if deviations[focal] == 0:
            continue
        sampled = sample_other_indices(rng, size, neighbors.shape[1], focal)
        simulated_lag = deviations[sampled].mean(axis=1)
        simulated_i = deviations[focal] * simulated_lag / (denominator / size)
        exceedances = np.count_nonzero(np.abs(simulated_i) >= abs(local_i[focal]))
        local_p[focal] = (1 + exceedances) / (PERMUTATIONS + 1)
    local_q = benjamini_hochberg(local_p)
    quadrants = np.full(size, "NS", dtype="U2")
    quadrants[(deviations > 0) & (lag > 0)] = "HH"
    quadrants[(deviations < 0) & (lag < 0)] = "LL"
    quadrants[(deviations > 0) & (lag < 0)] = "HL"
    quadrants[(deviations < 0) & (lag > 0)] = "LH"
    nominal_clusters = np.where(local_p <= FDR_THRESHOLD, quadrants, "NS")
    fdr_clusters = np.where(local_q <= FDR_THRESHOLD, quadrants, "NS")
    return global_i, global_p, local_i, local_p, local_q, lag, nominal_clusters, fdr_clusters


def main():
    points = read_points()
    rates_by_period = read_rates()
    common = set(points)
    for rates in rates_by_period.values():
        common &= set(rates)
    codes = sorted(common)
    if len(codes) <= NEIGHBOR_COUNT:
        raise ValueError("Too few municipalities with valid rates in every period")
    excluded = sorted(set(points) - common)
    neighbors = nearest_neighbors(points, codes)
    if np.any(neighbors == np.arange(len(codes))[:, None]):
        raise AssertionError("A municipality was selected as its own neighbor")
    rng = np.random.default_rng(SEED)
    global_rows = []
    local_rows = []
    for period in PERIODS:
        rates = np.array([rates_by_period[period][code] for code in codes], dtype=float)
        (
            global_i, global_p, local_i, local_p, local_q, lag,
            nominal_clusters, fdr_clusters,
        ) = moran_statistics(rates, neighbors, rng)
        global_rows.append({
            "period": period,
            "municipalities": len(codes),
            "neighbors": NEIGHBOR_COUNT,
            "permutations": PERMUTATIONS,
            "global_i": f"{global_i:.8f}",
            "p_positive": f"{global_p:.4f}",
            "hh_nominal": int(np.count_nonzero(nominal_clusters == "HH")),
            "ll_nominal": int(np.count_nonzero(nominal_clusters == "LL")),
            "hh_fdr": int(np.count_nonzero(fdr_clusters == "HH")),
            "ll_fdr": int(np.count_nonzero(fdr_clusters == "LL")),
        })
        for index, code in enumerate(codes):
            local_rows.append({
                "period": period,
                "code": code,
                "rate_per_100k": f"{rates[index]:.4f}",
                "lag_deviation": f"{lag[index]:.6f}",
                "local_i": f"{local_i[index]:.8f}",
                "p_two_sided": f"{local_p[index]:.4f}",
                "q_bh": f"{local_q[index]:.6f}",
                "cluster_nominal": nominal_clusters[index],
                "cluster_fdr": fdr_clusters[index],
            })
        print(
            f"{period}: n={len(codes)}, I={global_i:.4f}, p={global_p:.4f}, "
            f"HH/LL nominal={global_rows[-1]['hh_nominal']}/{global_rows[-1]['ll_nominal']}, "
            f"HH/LL FDR={global_rows[-1]['hh_fdr']}/{global_rows[-1]['ll_fdr']}"
        )
    for path, rows in ((GLOBAL_OUTPUT, global_rows), (LOCAL_OUTPUT, local_rows)):
        with path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(f"Common municipalities: {len(codes)}; excluded for missing rate: {excluded}")


if __name__ == "__main__":
    main()
