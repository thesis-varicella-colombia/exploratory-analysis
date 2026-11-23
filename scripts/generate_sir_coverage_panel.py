"""Join age-standardized municipal SIR with already-lagged PAI coverage.

The PAI source labels each source year as the following analysis year. This
script preserves that convention and never shifts the coverage a second time.
Administrative dose coverage is not a population immune fraction.
"""

from pathlib import Path

import pandas as pd

from municipal_coverage import harmonize_coverage, canonical_coverage, coverage_at_least, capped_coverage


ROOT = Path(__file__).resolve().parents[1]
SIR_SOURCE = ROOT / "docs/data_processed/anomalias_cobertura/age_standardized_sir_municipal_periods.csv"
COVERAGE_SOURCE = ROOT / "data/vaccine_coverage_municipal_lagged_2016_2025.csv"
OUTPUT = ROOT / "docs/data_processed/anomalias_cobertura/age_standardized_sir_coverage_periods.csv"
PERIOD_YEARS = {
    "2015-2019": range(2016, 2020),
    "2020-2021": range(2020, 2022),
    "2022-2025": range(2022, 2026),
}
DOSE_COLUMNS = {
    "first_dose": "%_varicela_un_anio_dosis_unica",
    "booster": "%_varicela_cinco_anios_refuerzo",
}


def build_panel(sir, coverage):
    """Return a period panel with observed raw coverage and quality counts."""
    required = {"period", "code", "sir_period", "sir_pre"}
    if not required.issubset(sir.columns):
        raise ValueError("SIR source is missing required columns")
    coverage = harmonize_coverage(coverage)
    sir = sir.loc[sir.period.isin(PERIOD_YEARS)].copy()
    if sir.duplicated(["period", "code"]).any():
        raise ValueError("Duplicate municipality-period SIR")

    rows = []
    for period, years in PERIOD_YEARS.items():
        selected = coverage.loc[coverage.anio.isin(years)]
        for code, group in selected.groupby("DIVIPOLA", sort=False):
            row = {"period": period, "code": code,
                   "coverage_years_available": len(group),
                   "coverage_years_expected": len(years)}
            for dose, column in DOSE_COLUMNS.items():
                values = pd.to_numeric(group[column], errors="coerce")
                present = values.notna()
                row[f"coverage_{dose}_mean"] = canonical_coverage(values.mean())
                row[f"coverage_{dose}_years"] = int(present.sum())
                row[f"coverage_{dose}_above_100_years"] = int((values > 100).sum())
                usable = capped_coverage(values)
                row[f"coverage_{dose}_valid_years"] = int(usable.notna().sum())
                row[f"coverage_{dose}_valid_mean"] = canonical_coverage(usable.mean())
            rows.append(row)
    coverage_period = pd.DataFrame(rows)
    result = sir.merge(
        coverage_period, on=["period", "code"], how="left",
        validate="one_to_one",
    )
    if len(result) != len(sir):
        raise ValueError("Coverage join changed the SIR row count")
    for dose in DOSE_COLUMNS:
        mean = result[f"coverage_{dose}_valid_mean"]
        if ((mean < 0) | (mean > 100)).any():
            raise ValueError("Valid coverage mean outside [0, 100]")
    return result


def classify_quadrants(panel, critical_coverage, dose="first_dose",
                       sir_reference="period"):
    """Count the four descriptive cells for a supplied model threshold.

    Finite nonnegative annual coverage is capped at 100 before averaging.
    Only municipality-periods with usable coverage in every year are classified. The caller must justify the
    critical coverage externally; it is not estimated by this script.
    """
    if not 0 < critical_coverage <= 100:
        raise ValueError("Critical coverage must be in (0, 100]")
    if dose not in DOSE_COLUMNS or sir_reference not in {"period", "pre"}:
        raise ValueError("Unknown dose or SIR reference")
    coverage = panel[f"coverage_{dose}_valid_mean"]
    complete = (
        panel[f"coverage_{dose}_valid_years"]
        == panel.coverage_years_expected
    )
    sir = panel[f"sir_{sir_reference}"]
    eligible = panel.loc[complete & coverage.notna() & sir.notna()].copy()
    eligible["coverage_above_threshold"] = (
        coverage_at_least(eligible[f"coverage_{dose}_valid_mean"], critical_coverage)
    )
    eligible["sir_above_one"] = eligible[f"sir_{sir_reference}"] >= 1
    counts = (
        eligible.groupby(
            ["period", "coverage_above_threshold", "sir_above_one"]
        ).size().rename("municipalities").reset_index()
    )
    return eligible, counts


def main():
    sir = pd.read_csv(SIR_SOURCE, dtype={"code": str})
    coverage = pd.read_csv(COVERAGE_SOURCE, dtype={"DIVIPOLA": str})
    result = build_panel(sir, coverage)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, float_format="%.8f")
    for period in PERIOD_YEARS:
        subset = result.loc[result.period == period]
        print(
            f"{period}: {len(subset)} municipalities; "
            f"complete first-dose coverage="
            f"{(subset.coverage_first_dose_valid_years == subset.coverage_years_expected).sum()}; "
            f"complete booster coverage="
            f"{(subset.coverage_booster_valid_years == subset.coverage_years_expected).sum()}"
        )
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
