"""Diagnose zero inflation before fitting municipality-level endemic channels.

The integrated weekly table stores only municipality-weeks with notifications.
Within nationally observed weeks, absent municipality rows are represented as
zero notifications in this diagnostic. This does not establish that surveillance
was complete in every municipality-week.
"""

import json
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sivigila_integrado_notification_semanal_municipal.parquet"
GEOMETRY = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
OUTPUT = ROOT / "docs/data_processed/anomalias_cobertura/municipal_zero_diagnostics_2008_2014.csv"
START_YEAR = 2008
END_YEAR = 2014
WEEKS = range(1, 53)


def calculate_diagnostics():
    """Return one row per mapped unit for the seven-year weekly baseline."""
    features = json.loads(GEOMETRY.read_text(encoding="utf-8"))["features"]
    codes = sorted(feature["properties"]["code"] for feature in features)
    if len(codes) != 1122 or len(set(codes)) != len(codes):
        raise ValueError("Expected 1,122 unique mapped units")

    columns = [
        "codigo_municipio", "ano_epidemiologico",
        "semana_epidemiologica", "casos_total",
    ]
    records = ds.dataset(SOURCE, format="parquet").to_table(columns=columns).to_pandas()
    records = records.loc[
        records.ano_epidemiologico.between(START_YEAR, END_YEAR)
        & records.semana_epidemiologica.isin(WEEKS)
    ]
    national_weeks = (
        records[["ano_epidemiologico", "semana_epidemiologica"]]
        .drop_duplicates()
        .sort_values(["ano_epidemiologico", "semana_epidemiologica"])
    )
    week_pairs = list(map(tuple, national_weeks.to_numpy()))
    index = pd.MultiIndex.from_product(
        [codes, week_pairs], names=["code", "year_week"]
    )
    counts = (
        records.groupby(
            ["codigo_municipio", "ano_epidemiologico", "semana_epidemiologica"]
        ).casos_total.sum()
    )
    counts.index = pd.MultiIndex.from_arrays(
        [
            counts.index.get_level_values(0),
            list(zip(
                counts.index.get_level_values(1),
                counts.index.get_level_values(2),
            )),
        ],
        names=["code", "year_week"],
    )
    observed = counts.reindex(index)
    missing_rows = observed.isna().groupby(level="code").sum()
    complete = observed.fillna(0).astype(int)
    zero_fraction = complete.eq(0).groupby(level="code").mean()
    cases = complete.groupby(level="code").sum()

    table = complete.rename_axis(index=["code", "year_week"]).reset_index()
    table[["year", "week"]] = pd.DataFrame(
        table.year_week.tolist(), index=table.index
    )
    quartiles = (
        table.groupby(["code", "week"])["casos_total"]
        .quantile([0.25, 0.50, 0.75])
        .unstack()
    )
    collapsed = quartiles.eq(0).all(axis=1).groupby(level="code").sum()
    result = pd.DataFrame({
        "code": codes,
        "national_weeks": len(week_pairs),
        "weeks_without_row": missing_rows.reindex(codes).to_numpy(),
        "zero_fraction": zero_fraction.reindex(codes).to_numpy(),
        "collapsed_weeks": collapsed.reindex(codes).to_numpy(),
        "collapsed_fraction": collapsed.reindex(codes).to_numpy() / len(WEEKS),
        "baseline_notifications": cases.reindex(codes).to_numpy(),
    })
    return result


def main():
    result = calculate_diagnostics()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, float_format="%.6f")
    print(f"Mapped units: {len(result)}")
    print(f"Median zero fraction: {result.zero_fraction.median():.4f}")
    print(f"Median collapsed weeks: {result.collapsed_weeks.median():.0f} of 52")
    print(f"At least 26 collapsed weeks: {(result.collapsed_weeks >= 26).sum()}")
    print(f"All 52 collapsed weeks: {(result.collapsed_weeks == 52).sum()}")
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
