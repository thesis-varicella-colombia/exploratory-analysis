"""Simplify the repository's DANE MGN GeoJSON for the web map.

Usage: python3 scripts/prepare_spatial_boundaries.py
"""

import argparse
import json
import lzma
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/MGN_ADM_MPIO_GRAFICO.geojson.xz"
OUTPUT = ROOT / "docs/data_processed/municipal_boundaries_dane.geojson"
TOLERANCE_SQUARED = 0.002 ** 2  # Degrees in CRS84; sufficient for the national view.


def segment_distance_squared(point, start, end):
    ax, ay = start[:2]
    bx, by = end[:2]
    px, py = point[:2]
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    fraction = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return (px - ax - fraction * dx) ** 2 + (py - ay - fraction * dy) ** 2


def simplify_ring(ring):
    if len(ring) <= 4:
        return [[round(value, 4) for value in point[:2]] for point in ring]
    keep = {0, len(ring) - 1}
    pending = [(0, len(ring) - 1)]
    while pending:
        first, last = pending.pop()
        if last - first <= 1:
            continue
        farthest = max(
            range(first + 1, last),
            key=lambda index: segment_distance_squared(ring[index], ring[first], ring[last]),
        )
        if segment_distance_squared(ring[farthest], ring[first], ring[last]) > TOLERANCE_SQUARED:
            keep.add(farthest)
            pending.extend([(first, farthest), (farthest, last)])
    simplified = []
    for index in sorted(keep):
        point = [round(value, 4) for value in ring[index][:2]]
        if not simplified or point != simplified[-1]:
            simplified.append(point)
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    if len(simplified) < 4:
        return [[round(value, 4) for value in point[:2]] for point in ring]
    return simplified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE,
                        help="DANE MGN GeoJSON or .geojson.xz (defaults to the repository copy)")
    args = parser.parse_args()
    opener = lzma.open if args.source.suffix == ".xz" else open
    with opener(args.source, "rt", encoding="utf-8") as source:
        original = json.load(source)
    if original.get("type") != "FeatureCollection":
        raise ValueError("Expected a GeoJSON FeatureCollection")

    features = []
    codes = set()
    for feature in original["features"]:
        props = feature["properties"]
        code = props["mpio_cdpmp"]
        if code in codes:
            raise ValueError(f"Duplicate DIVIPOLA code: {code}")
        codes.add(code)
        geometry = feature["geometry"]
        if geometry["type"] != "MultiPolygon":
            raise ValueError(f"Unexpected geometry for {code}: {geometry['type']}")
        features.append({
            "type": "Feature",
            "properties": {
                "code": code,
                "name": props["mpio_cnmbr"],
                "department": props["dpto_cnmbr"],
                "kind": props["mpio_tipo"],
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [simplify_ring(ring) for ring in polygon]
                    for polygon in geometry["coordinates"]
                ],
            },
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as target:
        json.dump({"type": "FeatureCollection", "features": features}, target,
                  ensure_ascii=False, separators=(",", ":"))
        target.write("\n")
    print(f"Generated: {OUTPUT.relative_to(ROOT)} ({len(features)} features)")


if __name__ == "__main__":
    main()
