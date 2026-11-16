"""Generate municipal peak weeks for the three scatterplot periods in section 5C.

Run after generate_seasonal_territories.py with .venv/bin/python.
"""

import csv
import gzip
import json
from pathlib import Path

from pyproj import Transformer
from shapely import transform
from shapely.geometry import shape

from generate_phase_analysis import phase_metrics


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/data_processed/estacionalidad/seasonal_territories"
BOUNDARIES = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
OUTPUT = ROOT / "docs/data_processed/estacionalidad/municipal_phase_2008_2025.csv"
PERIODS = {
    "2008–2014": range(2008, 2015),
    "2015–2019": range(2015, 2020),
    "2022–2025": range(2022, 2026),
}


def main():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    weeks = manifest["weeks"]
    entities = {row["code"]: row for row in manifest["entities"]
                if row["dimension"] == "municipality"}
    boundary_data = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
    project = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True).transform
    unproject = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True).transform
    geometry_by_code = {feature["properties"]["code"]: feature["geometry"]
                        for feature in boundary_data["features"]}
    if set(entities) != set(geometry_by_code) or len(entities) != 1122:
        raise ValueError("Municipal catalog and geometries differ")
    rows = []
    for code, entity in sorted(entities.items()):
        with gzip.open(SOURCE / f"{entity['id']}.json.gz", "rt", encoding="utf-8") as source:
            payload = json.load(source)
        if payload["id"] != entity["id"]:
            raise ValueError(f"Incorrect series ID: {code}")
        rates = payload["series"]["notification"]["all"]
        if len(rates) != len(weeks):
            raise ValueError(f"Incorrect weekly series length: {code}")
        geometry = transform(shape(geometry_by_code[code]), project, interleaved=False)
        _, latitude = unproject(geometry.centroid.x, geometry.centroid.y)
        for period, years in PERIODS.items():
            weekly = {}
            for week in range(1, 53):
                observed = [rate for (year, current_week), rate in zip(weeks, rates)
                            if year in years and current_week == week and rate is not None]
                weekly[week] = sum(observed) / len(observed) if observed else None
            if not any(rate is not None and rate > 0 for rate in weekly.values()):
                continue  # An all-zero series has no meaningful peak week.
            peak, amplitude, mean_rate, relative_amplitude = phase_metrics(weekly)
            rows.append({
                "period": period,
                "municipality_code": code,
                "municipality": entity["name"],
                "department_code": entity["department"],
                "latitude": f"{latitude:.5f}",
                "peak_week": peak,
                "amplitude_per_100k": f"{amplitude:.9f}",
                "mean_rate_per_100k": f"{mean_rate:.9f}",
                "relative_amplitude": f"{relative_amplitude:.6f}" if relative_amplitude is not None else "",
                "observed_weeks": sum(rate is not None for rate in weekly.values()),
            })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} municipal phase rows")


if __name__ == "__main__":
    main()
