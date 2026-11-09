"""Display reduction must preserve daily sources, gaps, extrema and screen shape."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reduce_rt_visualization import CURVES, FIELDS, OUTPUT, SOURCE, encode_blocks, generate, reduce_series


def fixture(n=180, start="2012-12-01"):
    dates = pd.date_range(start, periods=n)
    values = 1 + .35 * np.sin(np.arange(n) / 24)
    data = {"count": [float(i % 5) for i in range(n)], "window_cases": [10.] * n,
            "rt": values.tolist(), "rt_lower_95": (values * .8).tolist(), "rt_upper_95": (values * 1.2).tolist()}
    calendar = {"date": dates.strftime("%Y-%m-%d").tolist()}
    return data, calendar


def unpack(encoded):
    cursor = 0
    first, last = [], []
    for offset, length in zip(encoded["offset"], encoded["length"]):
        first.append(cursor + offset)
        cursor += offset + length
        last.append(cursor - 1)
    return {**encoded, "first": first, "last": last,
            "index": [(a + b) / 2 for a, b in zip(first, last)]}


class RtReductionTests(unittest.TestCase):
    def test_smooth_curve_is_reduced_and_stays_within_screen_tolerance(self):
        original, calendar = fixture()
        reduced = reduce_series(original, calendar, "notification")
        self.assertLess(len(reduced["rt"]), len(original["rt"]) * .65)
        domain = max(original["rt_upper_95"])
        sx, sy = 650 / (len(original["rt"]) - 1), 300 / domain
        # Independent all-segment distance oracle, including the rounded output.
        for field in CURVES:
            x = np.array(reduced["index"]) * sx
            y = np.array(reduced[field]) * sy
            for day, value in enumerate(original[field]):
                dx, dy = np.diff(x), np.diff(y)
                along = np.clip(((day * sx - x[:-1]) * dx + (value * sy - y[:-1]) * dy) / (dx * dx + dy * dy), 0, 1)
                distance = np.hypot(day * sx - x[:-1] - along * dx, value * sy - y[:-1] - along * dy)
                self.assertLessEqual(distance.min(), .75001)
        self.assertEqual(reduced["index"][0], 0)
        self.assertEqual(reduced["index"][-1], len(original["rt"]) - 1)
        self.assertTrue(all(b - a < 7 for a, b in zip(reduced["first"], reduced["last"])))

    def test_peaks_crossings_gaps_and_band_order_survive(self):
        data, calendar = fixture()
        for i in [*range(7), *range(50, 57)]:
            for field in CURVES:
                data[field][i] = None
        data["rt"][71], data["rt_lower_95"][71], data["rt_upper_95"][71] = 10., 8., 12.
        reduced = reduce_series(data, calendar, "notification")
        at_peak = reduced["index"].index(71)
        self.assertEqual(reduced["rt"][at_peak], 10.)
        for position, (first, last) in enumerate(zip(reduced["first"], reduced["last"])):
            if reduced["rt"][position] is not None:
                self.assertTrue(all(data["rt"][i] is not None for i in range(first, last + 1)))
                self.assertLessEqual(reduced["rt_lower_95"][position], reduced["rt"][position])
                self.assertLessEqual(reduced["rt"][position], reduced["rt_upper_95"][position])
        for day in range(1, len(data["rt"])):
            before, after = data["rt"][day - 1:day + 1]
            if before is not None and after is not None and np.sign(before - 1) != np.sign(after - 1):
                self.assertIn(day - 1, reduced["index"])
                self.assertIn(day, reduced["index"])
        self.assertIn(50, reduced["index"])
        self.assertIn(56, reduced["index"])

    def test_detail_is_daily_and_coordinate_encoding_is_lossless(self):
        data, calendar = fixture(600)
        reduced = reduce_series(data, calendar, "symptom")
        detail = reduced["detail"]
        for position, day in enumerate(detail["index"]):
            for field in FIELDS:
                self.assertAlmostEqual(detail[field][position], data[field][int(day)], places=11)
        decoded = unpack(encode_blocks(reduced))
        for field in ["first", "last", "index"]:
            self.assertEqual(decoded[field], reduced[field])
        self.assertEqual(len(detail["index"]), 455)

    def test_zero_series_and_original_output_guard(self):
        data, calendar = fixture(20)
        for field in CURVES:
            data[field] = [None] * 20
        reduced = reduce_series(data, calendar, "notification")
        self.assertEqual(reduced["index"], [0, 19])
        self.assertEqual(reduced["rt"], [None, None])
        with self.assertRaisesRegex(ValueError, "separate"):
            generate(SOURCE, SOURCE)
        with self.assertRaisesRegex(ValueError, "separate"):
            generate(SOURCE, SOURCE / "reduced")


class PublishedReductionTests(unittest.TestCase):
    @unittest.skipUnless((OUTPUT / "source_hashes.json").exists(), "Generate visualization data first")
    def test_sources_unchanged_and_all_publication_invariants(self):
        manifest = json.loads((OUTPUT / "manifest.json").read_text())
        metadata = manifest["visualization"]
        self.assertEqual(hashlib.sha256((SOURCE / "manifest.json").read_bytes()).hexdigest(), metadata["original_manifest_sha256"])
        generator = (ROOT / "scripts/generate_rt_stratified.py").read_bytes()
        # Existing artifacts retain the generator hash from before the path-only
        # section reorganization. Verify that restoring those paths recovers it;
        # future regenerations record the current generator hash instead.
        historical_generator = generator.replace(
            b"data_processed/numero_reproductivo/", b"data_processed/",
        ).replace(b"data_processed/evolucion_semanal/", b"data_processed/")
        self.assertIn(metadata["original_generator_sha256"], {
            hashlib.sha256(generator).hexdigest(),
            hashlib.sha256(historical_generator).hexdigest(),
        })
        hashes = json.loads((OUTPUT / "source_hashes.json").read_text())
        total = 0
        for method, calendar in manifest["calendars"].items():
            for group in manifest["series"]:
                relative = f"{method}/{group['id']}.json.gz"
                source = (SOURCE / relative).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(), hashes[relative])
                original = json.loads(gzip.decompress(source))
                packed = json.loads(gzip.decompress((OUTPUT / relative).read_bytes()))
                data = unpack(packed)
                total += len(data["rt"])
                self.assertEqual(len(data["rt"]), group[method]["overview_points"])
                self.assertLessEqual(packed["reduction"]["max_screen_error_pixels"], .750001)
                self.assertEqual(data["first"][0], 0)
                self.assertEqual(data["last"][-1], len(calendar["date"]) - 1)
                for field in CURVES:
                    source_values = np.array(original[field], dtype=float)
                    target_values = np.array(data[field], dtype=float)
                    finite = np.isfinite(source_values)
                    if finite.any():
                        self.assertAlmostEqual(float(np.nanmax(source_values)), float(np.nanmax(target_values)), places=10)
                        self.assertAlmostEqual(float(np.nanmin(source_values)), float(np.nanmin(target_values)), places=10)
                for i, (first, last) in enumerate(zip(data["first"], data["last"])):
                    if data["rt"][i] is not None:
                        self.assertLess(last - first, 7)
                        self.assertTrue(all(value is not None for value in original["rt"][first:last + 1]))
                detail = unpack(packed["detail"])
                for i, day in enumerate(detail["index"]):
                    for field in FIELDS:
                        self.assertEqual(detail[field][i], original[field][int(day)])
        self.assertEqual(total, metadata["totals"]["overview_points"])


if __name__ == "__main__":
    unittest.main()
