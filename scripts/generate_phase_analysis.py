"""Build department peak-week, seasonal amplitude, and annual Spearman summaries.

Run generate_latitude_week_heatmap.py first. Uses weeks 1–52 and excludes 2007.
"""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/data_processed/estacionalidad/latitude_week_heatmap.csv"
BOUNDARIES = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
PHASE_OUTPUT = ROOT / "docs/data_processed/estacionalidad/department_phase_2008_2025.csv"
CORRELATION_OUTPUT = ROOT / "docs/data_processed/estacionalidad/phase_spearman_2008_2025.csv"
GEO_OUTPUT = ROOT / "docs/data_processed/estacionalidad/department_boundaries_dane.geojson"
PERIODS = {
    "2008–2014": range(2008, 2015),
    "2015–2019": range(2015, 2020),
    "2020–2021": range(2020, 2022),
    "2022–2025": range(2022, 2026),
}


def read_rates():
    departments = {}
    rates = defaultdict(dict)
    with SOURCE.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["period"] not in {str(year) for year in range(2008, 2026)}:
                continue
            code = row["department_code"]
            departments[code] = (row["department"], float(row["latitude"]))
            rates[int(row["period"]), code][int(row["week"])] = (
                float(row["mean_rate_per_100k"]) if row["mean_rate_per_100k"] else None
            )
    if len(departments) != 32 or len(rates) != 18 * 32:
        raise ValueError("Expected 32 departments for each year from 2008 to 2025")
    if any(len(weeks) != 52 for weeks in rates.values()):
        raise ValueError("Expected 52 week positions per department and year")
    return departments, rates


def phase_metrics(weekly_rates):
    # Circular smoothing avoids an artificial break between weeks 52 and 1.
    smoothed = {}
    for week in range(1, 53):
        window = [weekly_rates[(week + offset - 1) % 52 + 1] for offset in range(-2, 3)]
        valid = [rate for rate in window if rate is not None]
        smoothed[week] = sum(valid) / len(valid) if valid else None
    valid_weeks = {week: rate for week, rate in smoothed.items() if rate is not None}
    if not valid_weeks:
        raise ValueError("Department has no observed weeks")
    peak = max(valid_weeks, key=lambda week: (valid_weeks[week], -week))
    amplitude = valid_weeks[peak] - min(valid_weeks.values())
    mean_rate = sum(valid_weeks.values()) / len(valid_weeks)
    relative_amplitude = amplitude / mean_rate if mean_rate > 0 else None
    return peak, amplitude, mean_rate, relative_amplitude


def ranks(values):
    ordered = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    index = 0
    while index < len(values):
        end = index + 1
        while end < len(values) and values[ordered[end]] == values[ordered[index]]:
            end += 1
        average_rank = (index + 1 + end) / 2
        for position in ordered[index:end]:
            result[position] = average_rank
        index = end
    return result


def spearman(xs, ys):
    """Spearman coefficient as the correlation of ranks, averaging tied ranks."""
    x_ranks, y_ranks = ranks(xs), ranks(ys)
    x_mean, y_mean = sum(x_ranks) / len(xs), sum(y_ranks) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_ranks, y_ranks))
    x_size = sum((x - x_mean) ** 2 for x in x_ranks)
    y_size = sum((y - y_mean) ** 2 for y in y_ranks)
    return numerator / math.sqrt(x_size * y_size) if x_size and y_size else None


def write_phase(departments, rates):
    rows = []
    for label, years in [(str(year), (year,)) for year in range(2008, 2026)] + list(PERIODS.items()):
        for code, (name, latitude) in sorted(departments.items()):
            weekly = {}
            for week in range(1, 53):
                values = [rates[year, code][week] for year in years]
                observed = [value for value in values if value is not None]
                weekly[week] = sum(observed) / len(observed) if observed else None
            peak, amplitude, mean_rate, relative_amplitude = phase_metrics(weekly)
            rows.append({
                "period": label, "department_code": code, "department": name,
                "latitude": f"{latitude:.5f}", "peak_week": peak,
                "amplitude_per_100k": f"{amplitude:.9f}",
                "mean_rate_per_100k": f"{mean_rate:.9f}",
                "relative_amplitude": f"{relative_amplitude:.6f}" if relative_amplitude is not None else "",
                "observed_weeks": sum(value is not None for value in weekly.values()),
            })
    with PHASE_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with CORRELATION_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(["year", "spearman_r", "departments"])
        for year in range(2008, 2026):
            annual = [row for row in rows if row["period"] == str(year)]
            coefficient = spearman(
                [float(row["latitude"]) for row in annual],
                [int(row["peak_week"]) for row in annual],
            )
            writer.writerow([year, f"{coefficient:.6f}" if coefficient is not None else "", len(annual)])
    return len(rows)


def write_boundaries(departments):
    with BOUNDARIES.open(encoding="utf-8") as source:
        municipal = json.load(source)
    geometries = defaultdict(list)
    for feature in municipal["features"]:
        code = feature["properties"]["code"][:2]
        if code in departments:
            geometry = shape(feature["geometry"])
            geometries[code].append(geometry if geometry.is_valid else geometry.buffer(0))
    if set(geometries) != set(departments):
        raise ValueError("Department geometry and rates do not match")
    features = []
    for code, (name, latitude) in sorted(departments.items()):
        geometry = unary_union(geometries[code])
        features.append({
            "type": "Feature",
            "properties": {"code": code, "name": name, "latitude": latitude},
            "geometry": mapping(geometry),
        })
    with GEO_OUTPUT.open("w", encoding="utf-8") as target:
        json.dump({"type": "FeatureCollection", "features": features}, target,
                  ensure_ascii=False, separators=(",", ":"))
        target.write("\n")


def main():
    departments, rates = read_rates()
    count = write_phase(departments, rates)
    write_boundaries(departments)
    print(f"Generated {count} phase rows, 18 correlations, and 32 department geometries")


if __name__ == "__main__":
    main()
