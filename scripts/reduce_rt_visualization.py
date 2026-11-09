"""Create display-only Rt summaries; never alter the original daily estimates.

Average blocks of at most seven days, refining until Rt and both interval
limits stay within 0.75 screen pixels of the display polyline at 650 x 300 px.
Keep run endpoints, extrema and Rt=1 crossing neighbors exactly. Never average
across missing Rt. Preserve the 2013--March 2014 detail at daily resolution.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/data_processed/numero_reproductivo/rt_stratified"
OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/rt_visualization"
FIELDS = ["count", "window_cases", "rt", "rt_lower_95", "rt_upper_95"]
CURVES = ["rt", "rt_lower_95", "rt_upper_95"]


def mean_blocks(curves, max_days, tolerance, x_scale):
    """Return contiguous blocks, using exact anchors and error-driven refinement."""
    n = len(curves)
    anchors = {0, n - 1}
    for values in curves.T:
        anchors.update([int(np.argmin(values)), int(np.argmax(values))])
    crossings = np.flatnonzero(np.diff(np.sign(curves[:, 0] - 1)))
    anchors.update(crossings.tolist())
    anchors.update((crossings + 1).tolist())
    blocks = []
    cursor = 0
    for anchor in sorted(anchors):
        while cursor < anchor:
            stop = min(cursor + max_days, anchor)
            blocks.append((cursor, stop))
            cursor = stop
        blocks.append((anchor, anchor + 1))
        cursor = anchor + 1
    x = np.arange(n)
    cumulative = np.vstack([np.zeros(3), np.cumsum(curves, axis=0)])
    while True:
        starts, stops = np.array(blocks).T
        centers = (starts + stops - 1) / 2
        values = (cumulative[stops] - cumulative[starts]) / (stops - starts)[:, None]
        # Avoid cancellation at exact anchors, including isolated sharp peaks.
        single = stops - starts == 1
        values[single] = curves[starts[single]]
        # Screen-space distance handles steep changes within a horizontal
        # pixel without averaging away visible peaks or troughs. Check nearby
        # ordered segments, independently for mean and both interval limits.
        if len(blocks) == 1:
            errors = np.zeros(n)
        else:
            base = np.clip(np.searchsorted(centers, x, side="right") - 1, 0, len(centers) - 2)
            errors = np.zeros(n)
            for column in range(3):
                distances = np.full(n, np.inf)
                for offset in [-2, -1, 0, 1, 2]:
                    left = np.clip(base + offset, 0, len(centers) - 2)
                    ax = centers[left] * x_scale
                    ay = values[left, column]
                    dx = (centers[left + 1] - centers[left]) * x_scale
                    dy = values[left + 1, column] - ay
                    along = np.clip(((x * x_scale - ax) * dx + (curves[:, column] - ay) * dy)
                                    / (dx * dx + dy * dy), 0, 1)
                    distance = np.hypot(x * x_scale - ax - along * dx, curves[:, column] - ay - along * dy)
                    distances = np.minimum(distances, distance)
                errors = np.maximum(errors, distances)
        refined = []
        for start, stop in blocks:
            if stop - start > 1 and errors[start:stop].max() > tolerance:
                middle = (start + stop) // 2
                refined.extend([(start, middle), (middle, stop)])
            else:
                refined.append((start, stop))
        if len(refined) == len(blocks):
            if errors.max(initial=0) > tolerance + 1e-8:
                raise AssertionError("Display error exceeds tolerance")
            return blocks, float(errors.max(initial=0))
        blocks = refined


def pack(data, blocks):
    result = {"index": [], "first": [], "last": [], **{field: [] for field in FIELDS}}
    for first, stop in blocks:
        first, stop = int(first), int(stop)
        result["index"].append((first + stop - 1) / 2)
        result["first"].append(first)
        result["last"].append(stop - 1)
        for field in FIELDS:
            values = np.asarray(data[field][first:stop], dtype=float)
            valid = values[np.isfinite(values)]
            result[field].append(round(float(valid.mean()), 12) if len(valid) else None)
    return result


def reduce_series(data, calendar, method, max_days=7, pixel_error=.75, height=300, width=650):
    if max_days < 1 or pixel_error <= 0 or height <= 0 or width <= 0:
        raise ValueError("Positive block size, pixel error and height required")
    n = len(calendar["date"])
    if any(len(data[field]) != n for field in FIELDS):
        raise ValueError("Input arrays do not match the source calendar")
    curves = np.array([data[field] for field in CURVES], dtype=float).T
    finite = np.isfinite(curves).all(axis=1)
    if not np.array_equal(np.isfinite(curves[:, 0]), finite):
        raise ValueError("Finite Rt requires finite interval bounds")
    maximum = float(np.max(curves[finite], initial=0))
    domain = min(maximum, 2) if method == "symptom" else maximum
    tolerance = max(domain * pixel_error * .98 / height, 1e-12)
    changes = np.flatnonzero(np.diff(np.r_[False, finite, False]))
    blocks = []
    worst_error = 0.
    cursor = 0
    for begin, stop in changes.reshape(-1, 2):
        # Two null endpoints represent each gap; the browser keeps separate
        # segments, so line and band can never bridge it.
        if cursor < begin:
            blocks.append((cursor, cursor + 1))
            if begin - cursor > 1:
                blocks.append((begin - 1, begin))
        local, error = mean_blocks(curves[begin:stop], max_days, tolerance, (domain / height) * width / max(n - 1, 1))
        worst_error = max(worst_error, error)
        blocks.extend((begin + first, begin + last) for first, last in local)
        cursor = stop
    if cursor < n:
        blocks.append((cursor, cursor + 1))
        if n - cursor > 1:
            blocks.append((n - 1, n))
    packed = pack(data, blocks)
    detail_indices = [i for i, date in enumerate(calendar["date"]) if "2013-01-01" <= date <= "2014-03-31"]
    packed["detail"] = pack(data, [(i, i + 1) for i in detail_indices])
    packed["reduction"] = {"input_points": n, "overview_points": len(blocks),
                           "max_screen_error_pixels": worst_error / max(domain / height, 1e-9), "tolerance": tolerance,
                           "max_days": max_days}
    return packed


def encode_blocks(data):
    """Delta-coded block coordinates avoid three large absolute-index arrays."""
    result = {field: values for field, values in data.items() if field not in ["index", "first", "last", "detail"]}
    cursor = 0
    offsets, lengths = [], []
    for first, last in zip(data["first"], data["last"]):
        offsets.append(first - cursor)
        lengths.append(last - first + 1)
        cursor = last + 1
    result["offset"] = offsets
    result["length"] = lengths
    if "detail" in data:
        result["detail"] = encode_blocks(data["detail"])
    return result


def generate(source=SOURCE, output=OUTPUT, max_days=7, pixel_error=.75):
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError("Output must be separate from the original data directory")
    raw_manifest = (source / "manifest.json").read_bytes()
    manifest = copy.deepcopy(json.loads(raw_manifest))
    manifest["visualization"] = {"format": 1, "algorithm": "adaptive_block_means",
                               "max_days": max_days, "pixel_error": pixel_error,
                               "reference_height": 300, "reference_width": 650, "original_directory": "../rt_stratified",
                               "original_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
                               "original_generator_sha256": hashlib.sha256((ROOT / "scripts/generate_rt_stratified.py").read_bytes()).hexdigest()}
    source_hashes = {}
    totals = {"input_points": 0, "overview_points": 0, "source_bytes": 0, "output_bytes": 0}
    for method, calendar in manifest["calendars"].items():
        directory = output / method
        directory.mkdir(parents=True, exist_ok=True)
        for index, entry in enumerate(manifest["series"]):
            relative = f"{method}/{entry['id']}.json.gz"
            original = (source / relative).read_bytes()
            source_hashes[relative] = hashlib.sha256(original).hexdigest()
            data = json.loads(gzip.decompress(original))
            reduced = reduce_series(data, calendar, method, max_days, pixel_error)
            compressed = gzip.compress(json.dumps(encode_blocks(reduced), ensure_ascii=False, separators=(",", ":"),
                                                 allow_nan=False).encode(), mtime=0)
            (output / relative).write_bytes(compressed)
            entry[method]["overview_points"] = len(reduced["index"])
            totals["input_points"] += len(data["rt"])
            totals["overview_points"] += len(reduced["index"])
            totals["source_bytes"] += len(original)
            totals["output_bytes"] += len(compressed)
            if index % 200 == 0:
                print(f"{method}: {index + 1}/{len(manifest['series'])}", flush=True)
    manifest["visualization"]["totals"] = totals
    (output / "source_hashes.json").write_text(json.dumps(source_hashes, separators=(",", ":")))
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(totals), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--max-days", type=int, default=7)
    parser.add_argument("--pixel-error", type=float, default=.75)
    args = parser.parse_args()
    generate(args.source, args.output, args.max_days, args.pixel_error)
